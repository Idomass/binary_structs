"""
This file has the code for the binary_struct decorator.

Binary struct is essanitialy a c-like struct, with the comforts that come with python.
The library supports serialization and deserialization of objects, with a clear and clean API.s

Basic API:
@binary_struct
class BufferWithSize:
    size: uint32_t
    buf: [uint8_t, 64]
"""

import sys
import logging
import inspect

from binary_structs.utils import BufferField, new_binary_buffer, new_typed_buffer

from collections import OrderedDict


LINE = '-' * 100


def _create_fn(name, local_params: list[str], lines: list[str], globals: dict):
    """
    This function receives a name for the function, and returns a
    function with the given locals and globals
    """

    lines_as_str = '\n    ' + '\n    '.join(lines)
    fn_text = f'def {name}({", ".join(local_params)}):{lines_as_str}'
    logging.debug(f'Created new function:\n{fn_text}')

    ns = {}
    exec(fn_text, globals, ns)

    # Mark the generated functions
    setattr(ns[name], 'bs_generated_func', True)

    return ns[name]


def _get_global_name(obj: object) -> str:
    """
    Returns a name of the obj in the global dict.
    This formatting is necessary to avoid collisions.
    """

    # obj might be an instance, get type name if it is
    obj_name = getattr(obj, '__name__', getattr(type(obj), '__name__'))

    return f'__{hex(id(obj))}_{obj_name}'


def _init_binary_field(self: type, field_name: str, field_type: type, field_value):
    """
    Helper function for initializing binary Fields in a BinaryStruct
    Initialization process is described below
    """

    # Default value initialization
    if field_value is None:
        object.__setattr__(self, field_name, field_type())

    # Check if the correct type was passed
    elif isinstance(field_value, field_type):
        object.__setattr__(self, field_name, field_value)

    # Check if type is compatible
    elif _is_binary_struct(type(field_value)) and _is_binary_struct(field_type) and \
        type(field_value).binary_fields == field_type.binary_fields:
        object.__setattr__(self, field_name, field_value)

    # Check for nested args initialization
    elif isinstance(field_value, list):
        object.__setattr__(self, field_name, field_type(*field_value))

    # Check for nested kwargs initialization
    elif isinstance(field_value, dict):
        object.__setattr__(self, field_name, field_type(**field_value))

    # Try to init with convertable value
    else:
        object.__setattr__(self, field_name, field_type(field_value))


def _set_binary_attr(self: type, field_name: str, field_value):
    """
    Asserts that the type that is passed is defined, and passes
    it into init var
    """

    if not hasattr(self, field_name):
        # This is a new attribute, do nothing
        object.__setattr__(self, field_name, field_value)
        return

    field = getattr(self, field_name)

    if getattr(field, '__name__', '') == 'TypedBuffer':
        new_buf = new_typed_buffer(field.UNDERLYING_TYPE)(field_value)

        object.__setattr__(self, field_name, new_buf)

    elif hasattr(field, '_type_'):
        new_buf = new_binary_buffer(field.UNDERLYING_TYPE, len(field))(*field_value)

        object.__setattr__(self, field_name, new_buf)

    else:
        self._init_binary_field(field_name, type(field), field_value)


def _init_var(name: str, field_type: type, globals: dict, default_value: type) -> list[str]:
    """
    Helper function for _create_init_fn that helps to init a variable.
    Returns the python code that is required to init that variable.
    """

    # Don't allow these type names
    if name in ('size_in_bytes', 'FORMAT'):
        raise AttributeError(f'Can\'t set attribute name to {name}')

    # Add types to the global dict
    default_value_name = _get_global_name(default_value)
    globals[default_value_name] = default_value
    new_type_name = _get_global_name(field_type)
    globals[new_type_name] = field_type

    # Generate function text for the given type
    if issubclass(field_type, BufferField):
        init_var =  [f'{name} = {new_type_name}({name} or {default_value_name} or [])']
        init_var += [f'object.__setattr__(self, "{name}", {name})']

    else:
        init_var = [f'self._init_binary_field("{name}", {new_type_name}, '
                                             f'{name} or {default_value_name})']

    return init_var


def _create_init_fn(binary_attrs: dict, globals: dict, bases: tuple[type]) -> str:
    """
    Create init function and return it.

    Each parameter has a default value of underlying_type()
    """

    init_txt = []
    init_args = ['self']
    init_kwargs = []

    # Init parent classes if they are binary fields
    for parent in bases:
        if not _is_parent_fn_callable(parent, '_bs_init'):
            continue

        parent_init = getattr(parent, '_bs_init')

        for param in inspect.signature(parent_init).parameters.values():
            if param.name == 'self':
                continue

            if param.default is inspect._empty:
                init_args.append(param.name)

            else:
                init_kwargs.append(f'{param.name} = {param.default}')

        parent_variables = parent_init.__code__.co_varnames[1:]
        init_txt.append(f'{_get_global_name(parent)}.{parent_init.__name__}(self, '
                        f'{", ".join(param for param in parent_variables)})')

    # Init variables
    for name, (kind, default_value) in binary_attrs.items():
        init_var_code = _init_var(name, kind, globals, default_value)
        init_txt.extend(init_var_code)
        init_kwargs.append(f'{name} = None')

    return _create_fn('_bs_init', init_args + init_kwargs, init_txt or ['pass'], globals)


def _create_bytes_fn(attributes: dict, globals: dict, bases: tuple[type]) -> str:
    """
    Create bytes function and return it.
    The created function will call bytes() on every class member
    """

    lines = ['buf = b""']

    for parent in bases:
        if not _is_parent_fn_callable(parent, '__bytes__'):
            continue

        lines += [f'buf += {_get_global_name(parent)}.__bytes__(self)']

    # For class attributes
    for attr in attributes.keys():
        lines += [f'buf += bytes(self.{attr})']

    lines += ['return buf']

    return _create_fn('_bs_bytes', ['self'], lines, globals)


def _create_equal_fn(binary_fields: dict, globals: dict, bases: tuple[type]) -> str:
    """
    Create and __eq__ function for a BinaryStruct and return it as a string.
    This function will compare all fields that were declared in the annotations.
    """

    lines = [
        # Make sure that we are comparing binary structs
        'if not hasattr(other, "_is_binary_field"): return False'
    ]

    for parent in bases:
        if not _is_parent_fn_callable(parent, '__eq__'):
            continue

        lines.append(f'if not {_get_global_name(parent)}.__eq__(self, other):')
        lines.append(f'    return False')

    for name in binary_fields:
        lines.append(f'if self.{name} != other.{name}:')
        lines.append(f'    return False')
    lines.append('return True')

    return _create_fn('_bs_eq', ['self, other'], lines, globals)


def _create_string_fn(binary_fields: dict, globals: dict, bases: tuple[type]) -> str:
    """
    Create a function that converts the struct into a string, for visual purposes
    """

    lines = ['string = ""']

    # Add bases
    for parent in bases:
        if not _is_parent_fn_callable(parent, '__str__'):
            continue

        lines += [f'string += {_get_global_name(parent)}.__str__(self)']

    # Add class variables
    for attr in binary_fields:
        lines += [f'attr_str = "\\n    " + "\\n    ".'
                  f'join(line for line in str(self.{attr}).split("\\n"))']
        lines += [f'string  += f"{attr}: {{attr_str}}\\n"']

    lines += ['return string']

    return _create_fn('_bs_str', ['self'], lines, globals)


def _create_iter_fn(binary_fields: dict, globals: dict, bases: tuple[type]):
    """
    Creates the __iter__ function to allow dict conversion
    """

    lines = []

    for parent in bases:
        if not _is_parent_fn_callable(parent, '__iter__'):
            continue

        lines.append(f'for attr, value in {_get_global_name(parent)}.__iter__(self):')
        lines.append('    yield attr, value')

    for name in binary_fields:
        lines.append(f'yield "{name}", self.{name}')

    return _create_fn('_bs_iter', ['self'], lines or ['pass'], globals)


def _create_deserialize_fn(binary_fields: dict, globals: dict, cls: type) -> str:
    """
    Create a deserialize function for binary struct from a buffer
    The function will first deserialize parent classes, then the class attributes
    """

    lines = ['init_dict = {}']

    # For this class bases
    for parent in cls.__bases__:
        if not _is_parent_fn_callable(parent, 'deserialize'):
            continue

        lines.append(f'init_dict.update(dict({_get_global_name(parent)}.deserialize(buf)))')
        lines.append(f'buf = buf[{_get_global_name(parent)}.static_size:]')

    # For this class attributes
    for name in binary_fields:
        lines.append(f'init_dict["{name}"] = {_get_global_name(cls)}.{name}_type.deserialize(buf)')

        lines.append(f'buf = buf[{_get_global_name(cls)}.{name}_type.static_size:]')

    lines.append(f'new_instance = {_get_global_name(cls)}.__new__({_get_global_name(cls)})')
    lines.append(f'{_get_global_name(cls)}._bs_init(new_instance, **init_dict)')
    lines.append(f'return new_instance')

    return _create_fn('deserialize', ['buf'], lines or ['pass'], globals)


def _create_size_fn(binary_fields: dict, globals: dict, bases: tuple[type]) -> str:
    """
    Generates the size property and returns the function as a string
    Created function will search the size_in_bytes attribute of every derived class
    """

    lines = ['counter = 0']

    # Add bases
    for parent in bases:
        if not _is_parent_fn_callable(parent, '_bs_size'):
            continue

        lines += [f'counter += {_get_global_name(parent)}._bs_size(self)']

    # Add class variables
    for attr in binary_fields:
        lines += [f'counter += self.{attr}.size_in_bytes']

    lines += ['return counter']

    return _create_fn('_bs_size', ['self'], lines, globals)


def _is_binary_struct(cls: type):
    """
    Returns if the given class is a binary struct
    """

    return hasattr(cls, f'_{cls.__name__}__is_binary_struct')


def _is_parent_fn_callable(parent: type, fn_name: str):
    fn = getattr(parent, fn_name, None)

    return inspect.isfunction(fn) or inspect.ismethod(fn)


def _get_binary_fields_recursively(cls: type) -> OrderedDict:
    """
    Returns an OrderedDict of all the binary fields in the class hierarchy
    """

    binary_fields = OrderedDict()
    for parent in cls.__bases__:
        if _is_binary_struct(parent):
            binary_fields.update(_get_binary_fields_recursively(parent))

    if _is_binary_struct(cls):
        binary_fields.update(cls.binary_fields)

    return binary_fields


def _set_nested_classes_as_attributes(cls: type):
    """
    Set nested classes as attributes, to allow easy access to underlying type.
    Can be useful for class that had their endianness converted
    """

    full_binary_fields = _get_binary_fields_recursively(cls)

    for attr_name, attr_type in full_binary_fields.items():
        new_attr_name = f'{attr_name}_type'
        if new_attr_name in full_binary_fields:
            raise AttributeError(f'Cannot set binary struct attribute to {new_attr_name}')

        setattr(cls, f'{attr_name}_type', attr_type)


def _parse_and_verify_annotations(annotations: dict) -> OrderedDict:
    """
    Create an OrderedDict from the annotations,
    the dict will have names as keys, and types as values.

    Makes sure that each annotation can be used inside a binary struct.
    """

    ordered_dict = OrderedDict()
    for name, annotation in annotations.items():
        if isinstance(annotation, list):
            if len(annotation) == 1:
                field = new_typed_buffer(annotation[0])

            elif len(annotation) == 2:
                field = new_binary_buffer(*annotation)

        else:
            field = annotation

        # Verify the field type
        if not hasattr(field, '_is_binary_field'):
            raise TypeError('Given field cannot be used inside a binary struct!')

        ordered_dict[name] = field

    return ordered_dict


def _calc_static_size(cls: type) -> int:
    """
    Returns the static size of the class.
    DynamicBuffers sizes will be 0
    """

    return sum(field_type.static_size for field_type in
               _get_binary_fields_recursively(cls).values())


def _process_class(cls):
    """
    This function is the main logic unit, it parses the different parameters and
    returns a processed class
    """

    logging.debug(LINE)
    logging.debug(f'Processing {cls} at {hex(id(cls))}')

    # Rebuild the class, we don't want to mess with the old class
    new_cls_dict = {key: value for key, value in cls.__dict__.items() if key not in ['__dict__', '__weakref__']}
    cls = type(cls.__name__, cls.__bases__, new_cls_dict)

    # Get a copy of the globals from the scope of the defined class
    globals = sys.modules[cls.__module__].__dict__.copy()
    globals['new_binary_buffer'] = new_binary_buffer
    globals['new_typed_buffer'] = new_typed_buffer

    annotations = cls.__dict__.get('__annotations__', {})
    binary_fields = _parse_and_verify_annotations(annotations)
    logging.debug(f'Found fields: {binary_fields}')

    # Add the class to the globals
    globals[_get_global_name(cls)] = cls

    # Add bases to global namepsace, they will be referenced
    # in the generated functions
    for parent in cls.__bases__:
        globals[_get_global_name(parent)] = parent

    # Mark the class as a binary_struct, add the binary_fields
    setattr(cls, '_is_binary_field', None)
    setattr(cls, f'_{cls.__name__}__is_binary_struct', None)
    setattr(cls, 'binary_fields', binary_fields)

    # These will be used for creating the new class
    # They are the same as annotations, but they contain the default value too
    binary_attrs = OrderedDict()
    for name, kind in binary_fields.items():
        value = getattr(cls, name) if hasattr(cls, name) else None
        binary_attrs[name] = (kind, value)

    # Generate functions
    generated_dunders = {
        'eq':       _create_equal_fn(binary_fields, globals, cls.__bases__),
        'str':      _create_string_fn(binary_fields, globals, cls.__bases__),
        'bytes':    _create_bytes_fn(binary_fields, globals, cls.__bases__),
        'iter':     _create_iter_fn(binary_fields, globals, cls.__bases__),
        'init':     _create_init_fn(binary_attrs, globals, cls.__bases__)
    }

    # Add the generated functions
    for name, fn in generated_dunders.items():
        # If function's dunder is not implemented in the class, add it as default
        dunder_name = f'__{name}__'
        if dunder_name not in cls.__dict__:
            setattr(cls, dunder_name, fn)

        # Add the generated function to the class
        setattr(cls, f'_bs_{name}', fn)

    # Add other attributes, these are non-overriding
    size_fn = _create_size_fn(binary_fields, globals, cls.__bases__)
    other_attrs = {
        'deserialize':          _create_deserialize_fn(binary_fields, globals, cls),
        '__setattr__':          _set_binary_attr,
        '_init_binary_field':   _init_binary_field,
        '_bs_size':             size_fn,
        'size_in_bytes':        property(size_fn),
        'static_size':          _calc_static_size(cls)
    }

    for name, attr in other_attrs.items():
        if name not in cls.__dict__:
            setattr(cls, name, attr)

    _set_nested_classes_as_attributes(cls)

    return cls


def binary_struct(cls: type = None):
    """
    Return the class that was passed with auto-implemented dunder methods such as bytes,
    and a new c'tor for the class
    """

    def wrap(cls):
        return _process_class(cls)

    if cls is None:
        return wrap

    return wrap(cls)
