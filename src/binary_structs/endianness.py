"""
This file exports the big_endian and little_endian decorators,
They are used to convert a BinaryStruct endiannes
"""

import logging

from copy import deepcopy
from binary_structs.utils import *
from binary_structs.binary_struct import binary_struct, _is_binary_struct
from binary_structs.utils.buffers.binary_buffer import BufferField


def _convert_primitive_type_endianness(kind: PrimitiveTypeField, endianness: Endianness) -> PrimitiveTypeField:
    """
    Convert PrimitiveTypeFields to the given endianness.
    If no match is found, return the given kind
    """

    le_to_be = {
        le_int8_t: be_int8_t,
        le_uint8_t: be_uint8_t,
        le_int16_t: be_int16_t,
        le_uint16_t: be_uint16_t,
        le_int32_t: be_int32_t,
        le_uint32_t: be_uint32_t,
        le_int64_t: be_int64_t,
        le_uint64_t: be_uint64_t,
    }

    # The other way around
    be_to_le = (dict((reversed(item) for item in le_to_be.items())))
    conversion_dict = be_to_le if endianness == Endianness.LITTLE else le_to_be

    new_kind = conversion_dict.get(kind, kind)
    logging.debug(f'Converting {kind} into {new_kind}')

    return new_kind


def _convert_buffer(buffer: type, endianness: Endianness) -> type:
    """
    Convert a TypedBuffer/BinaryBuffer endianness

    # TODO This does not convert endianness
    """

    return new_binary_buffer(buffer.element_type, buffer.static_size)


def _convert_class_annotations_endianness(cls, endianness: Endianness):
    """
    Replace class annotations with the fitting endianness annotations
    This method will use _convert_primitive_type_endianness for PrimitiveTypeField,
    and will use _convert_parents_classes for other BinaryStructs
    """

    annotations = cls.__dict__.get('__annotations__', {})
    for annotation_name, annotation_type in annotations.items():
        kind = annotation_type[0] if isinstance(annotation_type, list) else annotation_type

        if issubclass(kind, PrimitiveTypeField):
            new_kind = _convert_primitive_type_endianness(kind, endianness)

        elif hasattr(kind, '_is_binary_field'):
            new_kind = _convert_parents_classes(kind, endianness)

        else:
            # Not our business, don't convert
            continue

        # Re-assign the annotation
        if isinstance(annotation_type, list):
            annotations[annotation_name][0] = new_kind

        else:
            annotations[annotation_name] = new_kind


def _convert_endianness(cls: type, new_bases: tuple[type], endianness: Endianness):
    """
    Convert the endianness of a single class to the given endianness.
    The class is being rebuilt in order to not destroy the old one.
    """

    logging.debug(f'Converting endianness for {cls} at {hex(id(cls))}')

    # A field is consider valid if it is not a generated function
    is_field_valid = lambda field: not hasattr(field, 'bs_generated_func')

    # Filter out previously generated functions
    new_dict = {field_name: field_value for field_name, field_value in cls.__dict__.items()
                if is_field_valid(field_value)}

    new_dict['__annotations__'] = dict(deepcopy(cls.__dict__.get('__annotations__', {})))

    new_dict.pop('__dict__', None)
    new_dict.pop('__weakref__', None)

    # Rebuild class
    cls = type(cls.__name__, new_bases, new_dict)
    _convert_class_annotations_endianness(cls, endianness)

    return binary_struct(cls)


def _convert_parents_classes(cls, endianness: Endianness = Endianness.HOST):
    """
    Converts parent classes reucursiverly for cls
    We search for BinaryStructs, and convert only them recursively.
    For other classes, we only replace the base classes if neccesary
    """

    new_bases = []
    for base in cls.__bases__:
        if hasattr(base, '_is_binary_field'):
            new_bases.append(_convert_parents_classes(base, endianness))

        else:
            new_bases.append(base)

    if _is_binary_struct(cls):
        return _convert_endianness(cls, tuple(new_bases) or (object,), endianness)

    elif cls is not BufferField and issubclass(cls, BufferField):
        return _convert_buffer(cls, endianness)

    else:
        # Rebuild the class, because it's parents might have been changed
        return type(cls.__name__, tuple(new_bases) or (object,), dict(cls.__dict__))


def endian_decorator(cls, endianness: Endianness):
    if not _is_binary_struct(cls):
        raise TypeError('Given class cannot be used in a binary struct!')

    def wrap(cls):
        return _convert_parents_classes(cls, endianness)

    if cls is None:
        return wrap

    return wrap(cls)


def little_endian(cls: type = None):
    """
    Convert a binary struct class to little_endian
    """

    return endian_decorator(cls, Endianness.LITTLE)


def big_endian(cls: type = None):
    """
    Convert a binary struct class to big_endian
    """

    return endian_decorator(cls, Endianness.BIG)
