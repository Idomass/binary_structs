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


class AnnotationType(Enum):
    OTHER = 0
    TYPED_BUFFER = 1
    BINARY_BUFFER = 2

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

def _get_annotations_recursively(cls: type) -> dict:
    """
    Returns a dictionary of annotations recuresively
    Used for inheritence tree when multiple layers of annotations are available
    """

    annotations = cls.__dict__.get('__annotations__', {}).copy()
    for base in cls.__bases__:
        annotations.update(_get_annotations_recursively(base))

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

def _init_var(name: str, annotation, globals: dict) -> tuple[list[str], str]:
    """
    Helper function for _create_init_fn that helps to init a variable.
    Returns a tuple:
        - python code that is required to init that variable.
        - default value for the parameters
    """

    # Don't allow these type names
    if name in ('size_in_bytes', 'FORMAT'):
        raise AttributeError(f'Can\'t set attribute name to {name}')

    logging.debug(f'Creating init var {name} with type {annotation}')

    # TODO match syntax asap
    annotation_type = _get_annotation_type(annotation)
    if annotation_type == AnnotationType.BINARY_BUFFER:
        annotation, size = annotation
        type_name = _insert_type_to_globals(annotation, globals)

        init_var = [f'self.{name} = _binary_buffer({type_name}, {size}, {name})']
        default_value = f'{name} = []'

    elif annotation_type == AnnotationType.TYPED_BUFFER:
        annotation = annotation[0]
        type_name = _insert_type_to_globals(annotation, globals)

        init_var = [f'self.{name} = _typed_buffer({type_name}, {name})']
        default_value = f'{name} = []'

    elif annotation_type == AnnotationType.OTHER:
        type_name = _insert_type_to_globals(annotation, globals)

        init_var =  [f'if isinstance({name}, {type_name}):']
        init_var += [f'    self.{name} = {name}']
        init_var += [f'else:']
        init_var += [f'    try:']
        init_var += [f'        self.{name} = {type_name}({name})']
        init_var += [f'    except (TypeError, ValueError):']
        init_var += [f'        raise TypeError("Got invalid type for {name}")']

        default_value = f'{name} = {type_name}()'

    # Make sure annotation implements BinaryField
    if not issubclass(annotation, BinaryField):
        raise TypeError('All fields must implement BinaryField!')

    return init_var, default_value

def _create_init_fn(attributes: dict, globals: dict, bases: list[tuple[str, type]]) -> str:
    """
    Create init function and return it.

    Each parameter has a default value of underlying_type()
    """

    init_txt = []
    init_parameters = ['self']

    # Init parent classes if they are binary fields
    for parent_name, parent_type in bases:
        # Add a default value and a super for each parent attribute
        parent_annotations = _get_annotations_recursively(parent_type)

        init_parameters += [_init_var(name, annotation, globals)[1] for name, annotation in parent_annotations.items()]

        init_txt.append(f'super({parent_name}, self).__init__({", ".join(param for param in parent_annotations.keys())})')

    # Init variables
    for name, annotation in attributes.items():
        init_var_code, default_value = _init_var(name, annotation, globals)

        init_txt.extend(init_var_code)
        init_parameters.append(default_value)

    return _create_fn('__init__', init_parameters, init_txt or ['pass'], globals)

def _create_bytes_fn(attributes: dict, globals: dict, bases: list[tuple[str, type]]) -> str:
    """
    Create bytes function and return it.
    The created function will call bytes() on every class member
    """

    lines = ['buf = b""']

    for parent_name, _ in bases:
        lines += [f'buf += super({parent_name}, self).__bytes__()']

    # For class attributes
    for attr in attributes.keys():
        lines += [f'buf += bytes(self.{attr})']

    lines += ['return buf']

    return _create_fn('__bytes__', ['self'], lines, globals)

def _create_size_fn(attributes: dict, globals: dict, bases: tuple = ()) -> str:
    """
    Generates the size property and returns the function as a string
    Created function will search the size_in_bytes attribute of every derived class
    """

    lines = ['counter = 0']

    # Add bases
    for parent_name, _ in bases:
        lines += [f'counter += super({parent_name}, self).size_in_bytes']

    # Add class variables
    for attr in attributes.keys():
        lines += [f'counter += self.{attr}.size_in_bytes']

    lines += ['return counter']

    return _create_fn('size_in_bytes', ['self'], lines, globals, is_property=True)

def _get_class_bases_list(cls, globals: dict) -> list[tuple[str, type]]:
    """
    Insert BinaryField class bases, each with name in the global scope,
    and the type itself
    """

    bases_list = []
    for parent in cls.__bases__:
        if not issubclass(parent, BinaryField):
            continue

        # Don't allow to decorate a binary struct without inheritence
        if parent.__name__ == 'BinaryStruct':
            raise TypeError('Cannot decorate more then once!')

        logging.debug(f'Processing {cls}: Found BinaryField base class {parent}')
        bases_list.append((_insert_type_to_globals(parent, globals), parent))

    return bases_list

class BinaryStructHasher:
    """
    This class gets a type in init, and calculates a hash
    based on the given annotations and their order.
    This hash calculation ignores inheritence, and can only work
    for simple BinaryStructs
    """

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
        other_bases = other.type.__bases__
        self_bases  = self.type.__bases__

        return self_bases == other_bases

@lru_cache
def _process_class(cls: BinaryStructHasher):
    """
    This function is the main logic unit, it parses the different parameters and
    returns a processed class
    """

    cls = cls.type

    globals = sys.modules[cls.__module__].__dict__.copy()
    globals['_binary_buffer'] = _binary_buffer
    globals['_typed_buffer'] = _typed_buffer

    annotations = cls.__dict__.get('__annotations__', {})
    logging.debug(f'Building {cls}: Found annotations: {annotations}')

    # This will be used for creating the new class
    cls_basenames_to_bases = _get_class_bases_list(cls, globals)
    binary_struct_bases = tuple(base for _, base in cls_basenames_to_bases)

    # BinaryStruct Inherits from each BinaryStruct subclass of cls
    logging.debug(f'Proccessing {cls}: Using {binary_struct_bases or (BinaryField,)} as base class')
    BinaryStruct = type('BinaryStruct', binary_struct_bases or (BinaryField,), {})

    init_fn = _create_init_fn(annotations, globals, cls_basenames_to_bases)
    setattr(BinaryStruct, '__init__', init_fn)

    bytes_fn = _create_bytes_fn(annotations, globals, cls_basenames_to_bases)
    setattr(BinaryStruct, '__bytes__', bytes_fn)

    size_property = _create_size_fn(annotations, globals, cls_basenames_to_bases)
    setattr(BinaryStruct, 'size_in_bytes', size_property)

    # Since NewBinaryClass Inherits only from BinaryStructs', add
    # the other bases to the new class
    other_bases = tuple(set(cls.__bases__)^set(binary_struct_bases))
    new_bases = other_bases if other_bases != (object,) else tuple()

    logging.debug(f'Building new class with bases: {(BinaryStruct,) + new_bases}')
    new_cls = _copy_cls(cls, (BinaryStruct,) + new_bases)

    return new_cls

def binary_struct(cls = None):
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
