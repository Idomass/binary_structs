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

from binary_structs.utils import BinaryField, BinaryBuffer, TypedBuffer

from enum import Enum
from collections import OrderedDict


LINE = '-' * 100


class AnnotationType(Enum):
    """
    Types of available annotations
    """

    OTHER = 0
    TYPED_BUFFER = 1
    BINARY_BUFFER = 2


def _create_fn(name, local_params: list[str] = [], lines: list[str] = ['pass'], globals: dict = {}):
    """
    This function receives a name for the function, and returns a
    function with the given locals and globals
    """

    lines_as_str = '\n    ' + '\n    '.join(lines)
    fn_text = f'def {name}({", ".join(local_params)}):{lines_as_str}'
    logging.debug(f'Created new function:\n{fn_text}')

    ns = {}
    exec(fn_text, globals, ns)

    fn = ns[name]
    setattr(fn, 'bs_generated_func', True)

    return ns[name]


def _insert_type_to_globals(kind: type, globals: dict) -> str:
    """
    Inserts the given type into the namespace
    """

    name = kind.__name__

    globals[name] = kind

    return name


def _insert_bases_to_globals(cls: type, globals: dict):
    """
    Insert all of the class bases that are going to be used
    in the generated functions into the globals dict
    """

    for parent in cls.__bases__:
        _insert_type_to_globals(parent, globals)


def _get_annotations_recursively(cls: type) -> OrderedDict:
    """
    Returns a dictionary of annotations recuresively for each binary struct
    Used for inheritance tree when multiple layers of annotations are available
    """

    annotations = OrderedDict()
    for base in cls.__bases__:
        if _is_binary_struct(base):
            annotations.update(_get_annotations_recursively(base))

    if _is_binary_struct(cls):
        annotations.update(cls.__dict__.get('__annotations__', {}).copy())

    return annotations


def _get_annotation_type(annotation) -> AnnotationType:
    """
    Returns the type of a given annotation.
    Annotation can be a BinaryBuffer, TypedBuffer or something else
    """

    if isinstance(annotation, list):
        if len(annotation) == 2:
            return AnnotationType.BINARY_BUFFER

        elif len(annotation) == 1:
            return AnnotationType.TYPED_BUFFER

        else:
            raise ValueError('Buffer has wrong number of parameters!')

    else:
        return AnnotationType.OTHER


def _init_binary_field(self: type, field_name: str, field_type: BinaryField, field_value):
    """
    Helper function for initializing BinaryFields in a BinaryStruct
    Initialization process is described below
    """

    # Default value initialization
    if field_value is None:
        object.__setattr__(self, field_name, field_type())

    # Check if the correct type was passed or a comptabile one
    elif isinstance(field_value, field_type) or \
         getattr(field_type, f'_{field_type.__name__}__bs_old_id', -1) == id(type(field_value)):
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

    if type(field) is TypedBuffer:
        new_buf = TypedBuffer(field._underlying_type, field_value)

        object.__setattr__(self, field_name, new_buf)

    elif type(field) is BinaryBuffer:
        new_buf = BinaryBuffer(field._underlying_type, field._size, field_value)

        object.__setattr__(self, field_name, new_buf)

    else:
        self._init_binary_field(field_name, type(field), field_value)

def _init_var(name: str, annotation, globals: dict, default_value: type) -> list[str]:
    """
    Helper function for _create_init_fn that helps to init a variable.
    Returns the python code that is required to init that variable.
    """

    globals[f'{name}_default_value'] = default_value

    # Don't allow these type names
    if name in ('size_in_bytes', 'FORMAT'):
        raise AttributeError(f'Can\'t set attribute name to {name}')

    # TODO match syntax asap
    annotation_type = _get_annotation_type(annotation)
    if annotation_type == AnnotationType.BINARY_BUFFER:
        annotation, size = annotation
        type_name = _insert_type_to_globals(annotation, globals)

        init_var =  [f'{name} = BinaryBuffer({type_name}, {size}, '
                                           f'{name} or {name}_default_value or [])']
        init_var += [f'object.__setattr__(self, "{name}", {name})']

    elif annotation_type == AnnotationType.TYPED_BUFFER:
        annotation = annotation[0]
        type_name = _insert_type_to_globals(annotation, globals)

        init_var =  [f'{name} = TypedBuffer({type_name}, '
                                          f'{name} or {name}_default_value or [])']
        init_var += [f'object.__setattr__(self, "{name}", {name})']

    elif annotation_type == AnnotationType.OTHER:
        type_name = _insert_type_to_globals(annotation, globals)

        init_var = [f'self._init_binary_field("{name}", {type_name}, '
                                             f'{name} or {name}_default_value)']

    # Make sure annotation implements BinaryField
    if not issubclass(annotation, BinaryField):
        raise TypeError('All fields must implement BinaryField!')

    return init_var


def _create_init_fn(attributes: dict, globals: dict, bases: tuple[type]) -> str:
    """
    Create init function and return it.

    Each parameter has a default value of underlying_type()
    """

    init_txt = []
    init_args = ['self']
    init_kwargs = []

    # Init parent classes if they are binary fields
    for parent in bases:
        if not _is_parent_fn_callable(parent, '__init__'):
            continue

        for param in inspect.signature(parent.__init__).parameters.values():
            if param.name == 'self':
                continue

            if param.default is inspect._empty:
                init_args.append(param.name)

            else:
                init_kwargs.append(f'{param.name} = {param.default}')

        parent_variables = parent.__init__.__code__.co_varnames[1:]
        init_txt.append(f'{parent.__name__}.__init__(self, '
                        f'{", ".join(param for param in parent_variables)})')

    # Init variables
    for name, (annotation, default_value) in attributes.items():
        init_var_code = _init_var(name, annotation, globals, default_value)
        init_txt.extend(init_var_code)
        init_kwargs.append(f'{name} = None')

    return _create_fn('__init__', init_args + init_kwargs, init_txt or ['pass'], globals)


def _create_bytes_fn(attributes: dict, globals: dict, bases: tuple[type]) -> str:
    """
    Create bytes function and return it.
    The created function will call bytes() on every class member
    """

    lines = ['buf = b""']

    for parent in bases:
        if not _is_parent_fn_callable(parent, '__bytes__'):
            continue

        lines += [f'buf += {parent.__name__}.__bytes__(self)']

    # For class attributes
    for attr in attributes.keys():
        lines += [f'buf += bytes(self.{attr})']

    lines += ['return buf']

    return _create_fn('__bytes__', ['self'], lines, globals)


def _create_equal_fn(attributes: dict, globals: dict, bases: tuple[type]) -> str:
    """
    Create and __eq__ function for a BinaryStruct and return it as a string.
    This function will compare all fields that were declared in the annotations.
    """

    lines = [
        'if not isinstance(other, type(self)):'
        '    return False'
    ]

    for parent in bases:
        if not _is_parent_fn_callable(parent, '__eq__'):
            continue

        lines.append(f'if not {parent.__name__}.__eq__(self, other):')
        lines.append(f'    return False')

    for name in attributes.keys():
        lines.append(f'if self.{name} != other.{name}:')
        lines.append(f'    return False')
    lines.append('return True')

    return _create_fn('__eq__', ['self, other'], lines, globals)


def _create_string_fn(attributes: dict, globals: dict, bases: tuple[type]) -> str:
    """
    Create a function that converts the struct into a string, for visual purposes
    """

    lines = ['string = ""']

    # Add bases
    for parent in bases:
        if not _is_parent_fn_callable(parent, '__str__'):
            continue

        lines += [f'string += {parent.__name__}.__str__(self)']

    # Add class variables
    for attr in attributes.keys():
        lines += [f'attr_str = "\\n    " + "\\n    ".'
                  f'join(line for line in str(self.{attr}).split("\\n"))']
        lines += [f'string  += f"{attr}: {{attr_str}}\\n"']

    lines += ['return string']

    return _create_fn('__str__', ['self'], lines, globals)


def _create_deserialize_fn(attributes: dict, globals: dict, bases: tuple[type]) -> str:
    """
    Create a deserialize function for binary struct from a buffer
    The function will first deserialize parent classes, then the class attributes
    """

    lines = []

    # For this class bases
    for parent in bases:
        if not _is_parent_fn_callable(parent, 'deserialize'):
            continue

        lines.append(f'{parent.__name__}.deserialize(self, buf)')
        lines.append(f'buf = buf[{parent.__name__}._bs_size(self):]')

    # For this class attributes
    for name, annotation in attributes.items():
        annotation_type = _get_annotation_type(annotation)
        if annotation_type == AnnotationType.TYPED_BUFFER:
            lines.append(f'self.{name}.deserialize(buf)')

        else:
            lines.append(f'self.{name}.deserialize(buf[:self.{name}.size_in_bytes])')

        lines.append(f'buf = buf[self.{name}.size_in_bytes:]')

    return _create_fn('deserialize', ['self, buf'], lines + ['return self'], globals)


def _create_size_fn(attributes: dict, globals: dict, bases: tuple[type]) -> str:
    """
    Generates the size property and returns the function as a string
    Created function will search the size_in_bytes attribute of every derived class
    """

    lines = ['counter = 0']

    # Add bases
    for parent in bases:
        if not _is_parent_fn_callable(parent, '_bs_size'):
            continue

        lines += [f'counter += {parent.__name__}._bs_size(self)']

    # Add class variables
    for attr in attributes.keys():
        lines += [f'counter += self.{attr}.size_in_bytes']

    lines += ['return counter']

    return _create_fn('_bs_size', ['self'], lines, globals)


def _is_binary_struct(cls: type):
    """
    Returns if the given class is a binary struct
    """

    return issubclass(cls, BinaryField) and getattr(cls, f'_{cls.__name__}__is_binary_struct', False) == True


def _is_parent_fn_callable(parent: type, fn_name: str):
    return parent.__name__ != 'BinaryField' and inspect.isfunction(getattr(parent, fn_name, None))


def _set_nested_classes_as_attributes(cls):
    """
    Set nested classes as attributes, to allow easy access to underlying type.
    Can be useful for class that had their endianness converted
    """

    annotations = _get_annotations_recursively(cls)
    for attr_name, attr_type in annotations.items():
        new_attr_name = f'{attr_name}_type'

        if new_attr_name in annotations:
            raise AttributeError(f'Cannot set binary struct attribute to {new_attr_name}')

        setattr(cls, new_attr_name, attr_type)


def _process_class(cls):
    """
    This function is the main logic unit, it parses the different parameters and
    returns a processed class
    """

    logging.debug(LINE)
    logging.debug(f'Processing {cls}')

    globals = sys.modules[cls.__module__].__dict__.copy()
    globals['BinaryBuffer'] = BinaryBuffer
    globals['TypedBuffer'] = TypedBuffer

    annotations = cls.__dict__.get('__annotations__', {})
    logging.debug(f'Found annotations: {annotations}')

    # Make sure the created class is a subclass of BinaryField
    if not issubclass(cls, BinaryField):
        cls_bases = tuple() if cls.__bases__ == (object,) else cls.__bases__
        cls_bases += (BinaryField,)
        cls = type(cls.__name__, cls_bases, dict(cls.__dict__))

    # These will be used for creating the new class
    # They are the same as annotations, but they contain the default value too
    binary_attrs = OrderedDict()
    for attr_name, annotation in annotations.items():
        value = getattr(cls, attr_name) if hasattr(cls, attr_name) else None
        binary_attrs[attr_name] = (annotation, value)

    _insert_bases_to_globals(cls, globals)

    # Add generated functions
    generated_fns = {
        '__eq__':       _create_equal_fn(annotations, globals, cls.__bases__),
        '__str__':      _create_string_fn(annotations, globals, cls.__bases__),
        '__init__':     _create_init_fn(binary_attrs, globals, cls.__bases__),
        '__bytes__':    _create_bytes_fn(annotations, globals, cls.__bases__),
        '_bs_size':     _create_size_fn(annotations, globals, cls.__bases__),
        'deserialize':  _create_deserialize_fn(annotations, globals, cls.__bases__),
    }

    for name, fn in generated_fns.items():
        new_fn_name = f'{cls.__name__}{name}' if name in cls.__dict__ else name
        assert new_fn_name not in cls.__dict__, 'Illegal name used for function'
        setattr(cls, new_fn_name, fn)

    # Add other attributes
    other_attrs = {
        '__setattr__': _set_binary_attr,
        '_init_binary_field':   _init_binary_field,
        'size_in_bytes':        property(generated_fns['_bs_size']),
        f'_{cls.__name__}__is_binary_struct':   True
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
