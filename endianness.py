"""
This file exports the big_endian and little_endian decorators,
They are used to convert a NewBinaryStruct endiannes
"""

import sys
import logging

from enum import Enum

from binary_struct import _process_class
from utils.binary_field import *


# Endianness
class Endianness(Enum):
    BIG = 0
    LITTLE = 1
    HOST = LITTLE if sys.byteorder == 'little' else BIG

def _convert_primite_type_endianness(kind: PrimitiveTypeField, endianness: Endianness) -> PrimitiveTypeField:
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
    conversion_dict = be_to_le if endianness == Endianness.HOST else le_to_be

    new_kind = conversion_dict.get(kind, kind)
    logging.debug(f'Converting {kind} into {new_kind}')

    return new_kind

def _convert_class_annotations_endianness(cls, endianness: Endianness):
    """
    Replace class annotations with the fitting endianness annotations
    This method will use _convert_primite_type_endianness for PrimitiveTypeField,
    and will use _convert_parents_classes for other NewBinaryStructs
    """

    annotations = cls.__dict__.get('__annotations__', {})
    for annotation_name, annotation_type in annotations.items():
        kind = annotation_type[0] if isinstance(annotation_type, list) else annotation_type

        if issubclass(kind, PrimitiveTypeField):
            new_kind = _convert_primite_type_endianness(kind, kind)

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

    logging.debug(f'Processing {cls}: Found BinaryStruct class - {cls}')
    cls = _convert_class_annotations_endianness(cls, endianness)

    return _process_class(cls)

def _convert_parents_classes(cls, endianness: Endianness = Endianness.HOST):
    """
    Converts parent classes reucursiverly for cls
    We search for NewBinaryStructs, and convert only them recursively.
    For other classes, we only replace the base classes if neccesary
    """

    if not issubclass(cls, BinaryField):
        raise TypeError('Given class is not a BinaryField!')

    new_bases = []
    is_binary_struct = False
    for base in cls.__bases__:
        # Ignore non-BinaryFields
        if not issubclass(base, BinaryField):
            new_bases.append(base)

        elif base.__name__ == 'NewBinaryStruct':
            is_binary_struct = True
            # This means our base should be converted
            # First, convert its bases
            for binary_struct in base.__bases__:
                if binary_struct is BinaryField:
                    continue
                new_bases.append(_convert_parents_classes(binary_struct, endianness))

        else:
            # Our parent class is a class decorated using binary_struct
            # or a class that inherits from on of these
            new_bases.append(_convert_parents_classes(base, endianness))

    # Rebuild class using new bases
    tmp_cls = type(cls.__name__, tuple(new_bases) or (object,), dict(cls.__dict__))

    return _convert_endianness(tmp_cls, endianness) if is_binary_struct else tmp_cls

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
