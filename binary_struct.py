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

import logging

from utils.binary_field import BinaryField, PrimitiveTypeField
from utils.buffers.binary_buffer import BinaryBuffer
from utils.buffers.typed_buffer import TypedBuffer

from enum import Enum
from functools import lru_cache
from collections import OrderedDict

LINE = '--------------------------------------------'


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

    def __init__(self, kind: type) -> None:
        self._type = kind

        self._hash_value = hash(self.type) if issubclass(self.type, PrimitiveTypeField) \
                           else self._calculate_hash()

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

    @property
    def type(self) -> type:
        return self._type

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


def _get_new_binary_struct(bases: tuple[type], annotations: dict) -> type:
    """
    Generates a new BinaryStruct based on the given bases tuple
    """

    class BinaryStruct(*bases):
        _binary_attrs = {}
        _binary_bases = tuple(list(bases).remove(BinaryField) or []) if BinaryField in bases else bases
        __annotations__ = annotations

        def _init_cls(self, **binary_params: dict):
            for parent in __class__._binary_bases:
                # Pass only relevant parameters
                parent_params = {key: binary_params[key] for key in _get_annotations(parent)}

                super(parent, self).__init__(**parent_params)

            for name, (annotation, default_value) in __class__._binary_attrs.items():
                field_value = binary_params[name] if default_value is None else default_value

                annotation_type = _get_annotation_type(annotation)
                if annotation_type == AnnotationType.BINARY_BUFFER:
                    annotation, size = annotation
                    setattr(self, name, BinaryBuffer(annotation, size, field_value or []))

                elif annotation_type == AnnotationType.TYPED_BUFFER:
                    annotation = annotation[0]
                    setattr(self, name, TypedBuffer(annotation, field_value or []))

                elif annotation_type == AnnotationType.OTHER:
                    self._init_binary_field(name, annotation, field_value)

        def _init_binary_field(self, field_name: str, field_type: BinaryField, field_value):
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

        def deserialize(self, buf: bytes):
            for base in __class__._binary_bases:
                super(base, self).deserialize(buf)
                buf = buf[super(base, self).size_in_bytes:]

            for attr_name in __class__._binary_attrs:
                attr = getattr(self, attr_name)

                if isinstance(attr, TypedBuffer):
                    attr.deserialize(buf)
                else:
                    attr.deserialize(buf[:attr.size_in_bytes])
                buf = buf[attr.size_in_bytes:]

            return self

        @property
        def size_in_bytes(self) -> int:
            counter = sum(super(parent, self).size_in_bytes for parent in __class__._binary_bases)
            counter += sum(getattr(self, attr_name).size_in_bytes for attr_name in __class__._binary_attrs)

            return counter

        def __bytes__(self) -> bytes:
            data = b''.join(super(parent, self).__bytes__() for parent in __class__._binary_bases)
            data += b''.join(bytes(getattr(self, attr_name)) for attr_name in __class__._binary_attrs)

            return data

        def __eq__(self, other) -> bool:
            if not isinstance(other, type(self)):
                return False

            # Check parent classes
            if not all(super(parent, self).__eq__(other) for parent in __class__._binary_bases):
                return False

            return all(getattr(self, attr_name) == getattr(other, attr_name) for attr_name in __class__._binary_attrs)

        def __str__(self) -> str:
            result = ''
            for base in __class__._binary_bases:
                parent_str = '\n     ' + '\n     '.join(
                            line for line in super(base, self).__str__().split('\n'))

                result += f'{base.__name__}: {parent_str}\n'

            for attr in __class__._binary_attrs:
                attr_str = '\n    ' + '\n    '.join(
                           line for line in str(getattr(self, attr)).split('\n'))

                result += f'{attr}: {attr_str}\n'

            return result

    return BinaryStruct

def _copy_cls(cls: type, new_bases: tuple = None) -> type:
    """
    Copy a class and return the newly created one
    This method will copy the annotations of the new class too
    """

    if new_bases is None:
        new_bases = cls.__bases__

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

def _get_annotations(cls: type) -> OrderedDict:
    """
    Returns an OrderedDict of annotations for all valid binary_struct frames
    in the inheritence tree
    """

    annotations = OrderedDict()

    # A base might not be a binary struct, but one of his parents
    for base in _get_binary_struct_frames_recursively(cls):
        annotations.update(base.__dict__.get('__annotations__', {}))

    # Add class annotations if class is a BinaryStruct
    if cls.__name__ == 'BinaryStruct':
        annotations.update(cls.__dict__.get('__annotations__', {}))

    return annotations

def _get_annotation_type(annotation) -> AnnotationType:
    """
    Returns the type of a given annotation.
    Annotation can be a _binary_buffer, _typed_buffer or something else.
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

def _get_binary_struct_frames_recursively(cls) -> tuple[type]:
    """
    Similar to _filter_valid_bases, but returns the frames of the
    BinaryStruct (the original decorated class) instead of the base.

    cls must be a BinaryField, and not a BinaryStruct
    """

    frame_list = []
    for base in cls.__bases__:
        # Ignore non BinaryField paths
        if not issubclass(base, BinaryField):
            continue

        frame_list.extend(_get_binary_struct_frames_recursively(base))

        if base.__name__ == 'BinaryStruct':
            frame_list.append(base)

    return tuple(frame_list)

def _create_init_fn(cls):
    """
    Create bytes function and return it.
    The created function will call bytes() on every class member
    """

    init_params = []
    init_txt = ['init_dict = {}']

    # Add parents parameters
    for parent in cls._binary_bases:
        for attr_name in _get_annotations(parent):
            init_params.append(f'{attr_name} = None')
            init_txt.append(f'init_dict["{attr_name}"] = {attr_name}')

    # Add class parameters
    for attr_name in cls._binary_attrs:
        init_params.append(f'{attr_name} = None')
        init_txt.append(f'init_dict["{attr_name}"] = {attr_name}')

    init_txt.append(f'__class__._init_cls(self, **init_dict)')

    return _create_fn('__init__', ['self'] + init_params, init_txt, {'__class__': cls})

def _filter_valid_bases(cls) -> tuple[type]:
    """
    Returns every valid BinaryStruct decendant base in class.
    """

    bases_list = []
    for parent in cls.__bases__:
        if not issubclass(parent, BinaryField):
            continue

        # Don't allow to decorate a binary struct without inheritence
        if parent.__name__ == 'BinaryStruct':
            raise TypeError('Cannot decorate more then once!')

        bases_list.append(parent)

    return tuple(bases_list)

def _set_nested_classes_as_attributes(cls):
    """
    Set nested classes as attributes, to allow easy access to underlying type.
    Can be useful for class that had their endianness converted
    """

    for attr_name, (attr_type, _) in cls._binary_attrs.items():
        new_attr_name = f'{attr_name}_type'

        if new_attr_name in cls._binary_attrs:
            raise AttributeError(f'Cannot set binary struct attribute to {new_attr_name}')

        setattr(cls, new_attr_name, attr_type)

@lru_cache
def _process_class(cls: BinaryStructHasher):
    """
    This function is the main logic unit, it parses the different parameters and
    returns a processed class
    """

    cls = cls.type

    logging.debug(LINE)
    logging.debug(f'Proccessing class {cls}')

    # These will be used for creating the new class
    binary_struct_bases = _filter_valid_bases(cls)
    logging.debug(f'Found bases: {binary_struct_bases}')

    cls_annotations = cls.__dict__.get('__annotations__', {})
    # Don't allow these type names
    if any(name in ('size_in_bytes', 'FORMAT') for name in cls_annotations.keys()):
        raise AttributeError(f'Can\'t set attribute, invalid name!')

    NewBinaryStruct = _get_new_binary_struct(binary_struct_bases or (BinaryField,),
                                             cls_annotations)

    # Build binary attributes from annotations
    binary_attrs = {}
    for attr_name, annotation in cls_annotations.items():
        value = getattr(cls, attr_name) if hasattr(cls, attr_name) else None
        binary_attrs[attr_name] = (annotation, value)

    logging.debug(f'Setting attributes: {binary_attrs}')

    NewBinaryStruct._binary_attrs = binary_attrs
    setattr(NewBinaryStruct, '__init__', _create_init_fn(NewBinaryStruct))

    # Since NewBinaryClass Inherits only from BinaryStructs', add
    # the other bases to the new class
    new_bases = tuple(base for base in cls.__bases__ if base not in binary_struct_bases)
    new_bases = new_bases if new_bases != (object,) else tuple()
    new_bases = (NewBinaryStruct,) + new_bases

    logging.debug(f'Building new class with bases: {new_bases}')
    new_cls = _copy_cls(cls, new_bases)

    _set_nested_classes_as_attributes(new_cls)

    return new_cls

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
