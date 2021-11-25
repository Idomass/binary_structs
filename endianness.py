"""
This file exports the big_endian and little_endian decorators,
They are used to convert a BinaryStruct endiannes
"""

import logging

from utils.binary_field import *
from binary_struct import binary_struct, _copy_cls, _is_binary_struct


# Endianness
def _convert_primitive_type_endianness(kind: PrimitiveTypeField, endianness: Endianness) -> PrimitiveTypeField:
    """
    Convert PrimitiveTypeFields to the given endianness.
    If no match is found, return the given kind
    """

    le_to_be = {
        int8_t: be_int8_t,
        uint8_t: be_uint8_t,
        int16_t: be_int16_t,
        uint16_t: be_uint16_t,
        int32_t: be_int32_t,
        uint32_t: be_uint32_t,
        int64_t: be_int64_t,
        uint64_t: be_uint64_t,
    }
    # The other way around
    be_to_le = (dict((reversed(item) for item in le_to_be.items())))
    conversion_dict = be_to_le if endianness == Endianness.LITTLE else le_to_be

    new_kind = conversion_dict.get(kind, kind)
    logging.debug(f'Converting {kind} into {new_kind}')

    return new_kind

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

        elif issubclass(kind, BinaryField):
            new_kind = _convert_parents_classes(kind, endianness)

        else:
            # Not our business, don't convert
            continue

        # Re-assign the annotation
        if isinstance(annotation_type, list):
            annotations[annotation_name][0] = new_kind

        else:
            annotations[annotation_name] = new_kind

    return cls

def _convert_endianness(cls: BinaryField, endianness: Endianness):
    """
    Convert the endianness of a single class to the given endianness
    """

    logging.debug(f'Converting endianness for {cls}')
    cls = _convert_class_annotations_endianness(cls, endianness)

    # Filter out previously generated functions
    is_a_valid_field = lambda field: not callable(field[1]) or not hasattr(field[1], 'bs_generated_func')
    new_cls_dict = dict(filter(is_a_valid_field, cls.__dict__.items()))

    return binary_struct(type(cls.__name__, cls.__bases__, new_cls_dict))

def _convert_parents_classes(cls, endianness: Endianness = Endianness.HOST):
    """
    Converts parent classes reucursiverly for cls
    We search for BinaryStructs, and convert only them recursively.
    For other classes, we only replace the base classes if neccesary
    """

    if not issubclass(cls, BinaryField):
        raise TypeError('Given class is not a BinaryField!')

    new_bases = []
    for base in cls.__bases__:
        if _is_binary_struct(base):
            new_bases.append(_convert_parents_classes(base, endianness))

        else:
            # Ignore non-BinaryFields
            new_bases.append(base)

    # Rebuild class using new bases
    tmp_cls = _copy_cls(cls, tuple(new_bases) or (object,))

    return _convert_endianness(tmp_cls, endianness) if _is_binary_struct(cls) else tmp_cls

def little_endian(cls: BinaryField = None):
    """
    Convert a BinaryField class to little_endian
    """

    def wrap(cls):
        return _convert_parents_classes(cls, Endianness.LITTLE)

    if cls is None:
        return wrap

    return wrap(cls)

def big_endian(cls: BinaryField = None):
    """
    Convert a BinaryField class to big_endian
    """

    def wrap(cls):
        return _convert_parents_classes(cls, Endianness.BIG)

    if cls is None:
        return wrap

    return wrap(cls)
