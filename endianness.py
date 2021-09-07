"""
This file exports the big_endian and little_endian decorators,
They are used to convert a NewBinaryStruct endiannes

NOTE: Only types from PrimitiveTypeField will be converted
"""

import sys
import logging

from enum import Enum

from binary_struct import _process_class
from utils.binary_field import *


# Endianness
class Endianness(Enum):
    Big = 0
    Little = 1
    Host = Little if sys.byteorder == 'little' else Big

def _replace_class_annotations_endianness(cls, endianness: Endianness):
    """
    Replace class annotations with the fitting endianness annotations
    This method will find and replace any PrimitiveTypeField, and will replace it with
    the correct endianness type
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

    conversion_dict = be_to_le if endianness == Endianness.Host else le_to_be

    # convert annotations and reprocess the class
    annotations = cls.__dict__.get('__annotations__', {})
    for annotation_name, annotation_type in annotations.items():
        if isinstance(annotation_type, list):
            annotations[annotation_name][0] = conversion_dict.get(annotation_type[0], annotation_type[0])

        else:
            annotations[annotation_name] = conversion_dict.get(annotation_type, annotation_type)

    return cls

def _convert_endianness(cls: BinaryField, endianness: Endianness):
    """
    Convert the endianness of a single class to the given endianness
    """

    logging.debug(f'Processing {cls}: Found BinaryStruct class - {cls}')
    cls = _replace_class_annotations_endianness(cls, endianness)

    return _process_class(cls)

def _convert_parents_classes(cls, endianness: Endianness = Endianness.Host):
    """
    Converts parent classes reucursiverly for cls
    """

    if not issubclass(cls, BinaryField):
        raise TypeError('Given class is not a BinaryField!')

    new_bases = []
    old_bases = []
    for base in cls.__bases__:
        # Ignore non-BinaryFields
        if not issubclass(base, BinaryField):
            old_bases.append(base)

        elif base.__name__ == 'NewBinaryStruct':
            # This means our class should be converted
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
    tmp_cls = type(cls.__name__, tuple(new_bases + old_bases) or (object,), dict(cls.__dict__))

    return _convert_endianness(tmp_cls, endianness)

def little_endian(cls: BinaryField = None):
    """
    Convert a BinaryField class to little_endian
    """

    def wrap(cls):
        return _convert_endianness(cls, Endianness.Little)

    if cls is None:
        return wrap

    return wrap(cls)

def big_endian(cls: BinaryField = None):
    """
    Convert a BinaryField class to big_endian
    """

    def wrap(cls):
        return _convert_parents_classes(cls, Endianness.Big)

    if cls is None:
        return wrap

    return wrap(cls)
