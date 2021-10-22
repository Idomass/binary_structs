"""
This file has the code for the binary_struct decorator.

Binary struct is essanitialy a c-like struct, with the comforts that come with python.
The library supports serialization and deserialization of objects, with a clear and clean API.s

Basic API:
@binary_struct
class BufferWithSize:
    size: ctypes.c_uint32
    buf: [ctypes.c_uint8, 64]
"""

import sys
import logging

from utils.binary_field import BinaryField, PrimitiveTypeField
from utils.buffers.binary_buffer import BinaryBuffer as _binary_buffer
from utils.buffers.typed_buffer import TypedBuffer as _typed_buffer

from enum import Enum
from functools import lru_cache
from collections import OrderedDict


LINE = '-' * 100


class AnnotationType(Enum):
    """
    Types of available annotations
    """

    OTHER = 0
    TYPED_BUFFER = 1
    BINARY_BUFFER = 2


class BinaryStructHasher:
    """
    This class gets a type in init, and calculates a hash
    based on the given annotations and their order.
    """

    # TODO Custom implementation testing in required

    def __init__(self, kind: type) -> None:
        self._type = kind

        self._hash_value = hash(self.type) if issubclass(self.type, PrimitiveTypeField) \
                           else self._calculate_hash()

    @property
    def type(self):
        return self._type

    def _calculate_hash(self) -> int:
        """
        Calculate the hash using the given types annotations
        """

        hashes = []
        for base in self.type.__bases__:
            if base not in (BinaryField, object):
                hashes.append(hash(BinaryStructHasher(base)))

        for name, annotation in self.type.__dict__.get('__annotations__', {}).items():
            hashes.append(hash(name))

            annotation_type = _get_annotation_type(annotation)
            if annotation_type == AnnotationType.BINARY_BUFFER:
                underlying_type, size = annotation

                hashes.append(hash(size))

            elif annotation_type == AnnotationType.TYPED_BUFFER:
                underlying_type = annotation[0]

            elif annotation_type == AnnotationType.OTHER:
                underlying_type = annotation

            hashes.append(hash(BinaryStructHasher(underlying_type)))

        return hash(tuple(hashes))

    def __hash__(self) -> int:
        return self._hash_value

    def __eq__(self, other: object) -> bool:
        """
        Two BinaryStructHasher will be treated as equal if they have the same bases
        and the same annotations
        """

        # Check bases
        other_bases = tuple(base for base in other.type.__bases__ if base not in (object, BinaryField))
        self_bases  = tuple(base for base in self.type.__bases__ if base not in (object, BinaryField))

        logging.debug(f'{other_bases}, {self_bases}')

        return other_bases == self_bases


def _copy_cls(cls: type, new_bases: tuple) -> type:
    """
    Copy a class and return the newly created one
    This method will copy the annotations of the new class too
    """

    # copy dict except __weakref__, __dict__
    cls_dict = dict(cls.__dict__)
    cls_dict.pop('__weakref__', None)
    cls_dict.pop('__dict__', None)

    # deep copy __annotations__
    cls_dict['__annotations__'] = dict(cls.__dict__.get('__annotations__', {}))

    return type(cls.__name__, new_bases, cls_dict)

def _create_fn(name, local_params: list[str] = [], lines: list[str] = ['pass'], globals: dict = {},
               is_property: bool = False):
    """
    This function receives a name for the function, and returns a
    function with the given locals and globals
    """

    lines_as_str = '\n    ' + '\n    '.join(lines)
    fn_text = '@property\n' if is_property else ''
    fn_text += f'def {name}({", ".join(local_params)}):{lines_as_str}'
    logging.debug(f'Created new function:\n{fn_text}')

    ns = {}
    exec(fn_text, globals, ns)

    return ns[name]

def _insert_type_to_globals(kind: type, globals: dict) -> str:
    """
    Inserts the given type into the namespace
    """

    name = kind.__name__

    globals[name] = kind

    return name

def _get_annotations_recursively(cls: type) -> OrderedDict:
    """
    Returns a dictionary of annotations recuresively for each binary struct
    Used for inheritence tree when multiple layers of annotations are available
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
    Annotation can be a _binary_buffer, _typed_buffer or something else
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
        setattr(self, field_name, field_type())

    # Check if the correct type was passed
    elif isinstance(field_value, field_type):
        setattr(self, field_name, field_value)

    # Check for nested args initialization
    elif isinstance(field_value, list):
        setattr(self, field_name, field_type(*field_value))

    # Check for nested kwargs initialization
    elif isinstance(field_value, dict):
        setattr(self, field_name, field_type(**field_value))

    # Try to init with convertable value
    else:
        setattr(self, field_name, field_type(field_value))

def _init_var(name: str, annotation, globals: dict) -> list[str]:
    """
    Helper function for _create_init_fn that helps to init a variable.
    Returns the python code that is required to init that variable.
    """

    # Don't allow these type names
    if name in ('size_in_bytes', 'FORMAT'):
        raise AttributeError(f'Can\'t set attribute name to {name}')

    # TODO match syntax asap
    annotation_type = _get_annotation_type(annotation)
    if annotation_type == AnnotationType.BINARY_BUFFER:
        annotation, size = annotation
        type_name = _insert_type_to_globals(annotation, globals)

        init_var = [f'self.{name} = _binary_buffer({type_name}, {size}, {name} or [])']

    elif annotation_type == AnnotationType.TYPED_BUFFER:
        annotation = annotation[0]
        type_name = _insert_type_to_globals(annotation, globals)

        init_var = [f'self.{name} = _typed_buffer({type_name}, {name} or [])']

    elif annotation_type == AnnotationType.OTHER:
        type_name = _insert_type_to_globals(annotation, globals)

        init_var = [f'self._init_binary_field("{name}", {type_name}, {name})']

    # Make sure annotation implements BinaryField
    if not issubclass(annotation, BinaryField):
        raise TypeError('All fields must implement BinaryField!')

    return init_var, f'{name} = None'

def _create_init_fn(attributes: dict, globals: dict, bases: tuple[type]) -> str:
    """
    Create init function and return it.

    Each parameter has a default value of underlying_type()
    """

    init_txt = []
    init_parameters = ['self']

    # Init parent classes if they are binary fields
    for parent in bases:
        # Add a default value and an __init__ call for each parent attribute
        parent_annotations = _get_annotations_recursively(parent)

        init_parameters += [f'{name} = None' for name in parent_annotations.keys()]

        init_txt.append(f'{parent.__name__}.__init__(self, '
                        f'{", ".join(param for param in parent_annotations.keys())})')

    # Init variables
    for name, annotation in attributes.items():
        init_var_code, default_value = _init_var(name, annotation, globals)

        init_txt.extend(init_var_code)
        init_parameters.append(f'{name} = None')

    return _create_fn('__init__', init_parameters, init_txt or ['pass'], globals)

def _create_bytes_fn(attributes: dict, globals: dict, bases: tuple[type]) -> str:
    """
    Create bytes function and return it.
    The created function will call bytes() on every class member
    """

    lines = ['buf = b""']

    for parent in bases:
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
        'if not isinstance(other, type(self)):',
        '    return False'
    ]

    for base in bases:
        lines.append(f'if not {base.__name__}.__eq__(self, other):')
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
        lines += [f'parent_str = "\\n    " + "\\n    ".join('
                  f'line for line in {parent.__name__}.__str__(self).split("\\n"))']
        lines += [f'string += f"{parent.__name__}: {{parent_str}}\\n"']

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

def _filter_valid_bases(cls, globals: dict) -> tuple[type]:
    """
    Returns every valid BinaryStruct base in class.
    """

    bases_list = []
    for parent in cls.__bases__:
        if not _is_binary_struct(parent):
            continue

        _insert_type_to_globals(parent, globals)
        bases_list.append(parent)

    return tuple(bases_list)

def _set_annotations_as_attributes(cls):
    """
    Set class annotations as attributes, to allow easy access to underlying type
    Can be useful for class that had their endianness converted
    """

    for name, annotation_type in cls.__dict__.get('__annotations__', {}).items():
        kind = annotation_type[0] if isinstance(annotation_type, list) else annotation_type

        setattr(cls, name, kind)

@lru_cache
def _process_class(cls: BinaryStructHasher):
    """
    This function is the main logic unit, it parses the different parameters and
    returns a processed class
    """

    cls = cls.type

    logging.debug(LINE)
    logging.debug(f'Processing {cls}')

    globals = sys.modules[cls.__module__].__dict__.copy()
    globals['_binary_buffer'] = _binary_buffer
    globals['_typed_buffer'] = _typed_buffer

    annotations = cls.__dict__.get('__annotations__', {})
    logging.debug(f'Found annotations: {annotations}')

    # These will be used for creating the new class
    binary_struct_bases = _filter_valid_bases(cls, globals)

    logging.debug(f'Found binary bases: {binary_struct_bases}')

    eq_fn           = _create_equal_fn(annotations, globals, binary_struct_bases)
    str_fn          = _create_string_fn(annotations, globals, binary_struct_bases)
    init_fn         = _create_init_fn(annotations, globals, binary_struct_bases)
    bytes_fn        = _create_bytes_fn(annotations, globals, binary_struct_bases)
    size_fn         = _create_size_fn(annotations, globals, binary_struct_bases)
    size_property   = _create_fn('size_in_bytes', ['self'], ['return self._bs_size()'], globals, is_property=True)
    deserialize_fn  = _create_deserialize_fn(annotations, globals, binary_struct_bases)

    # BinaryStruct Inherits from each BinaryStruct subclass of cls
    fn_dict = {
        '_init_binary_field':   _init_binary_field,
        '__eq__':               eq_fn,
        '__str__':              str_fn,
        '__init__':             init_fn,
        '__bytes__':            bytes_fn,
        '_bs_size':             size_fn,
        'size_in_bytes':        size_property,
        'deserialize':          deserialize_fn,
        f'_{cls.__name__}__is_binary_struct':   True
    }

    new_cls_dict = cls.__dict__.copy()
    new_cls_dict.update(fn_dict)

    cls_bases = tuple() if cls.__bases__ == (object,) else cls.__bases__
    if not issubclass(cls, BinaryField):
        cls_bases += (BinaryField,)
    new_cls = type(cls.__name__, cls_bases, new_cls_dict)

    _set_annotations_as_attributes(new_cls)

    return _copy_cls(new_cls, cls_bases)

def binary_struct(cls: type = None):
    """
    Return the class that was passed with auto-implemented dunder methods such as bytes,
    and a new c'tor for the class
    """

    def wrap(cls):
        old_hits = _process_class.cache_info().hits
        new_cls = _process_class(BinaryStructHasher(cls))
        new_hits = _process_class.cache_info().hits

        # If cache was used, the class must be copied
        if new_hits > old_hits:
            logging.debug(f'Cache hit, copying {new_cls}')

            return _copy_cls(new_cls, new_cls.__bases__)
        else:
            return  new_cls

    if cls is None:
        return wrap

    return wrap(cls)
