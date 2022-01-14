"""
This file exports the big_endian and little_endian decorators,
They are used to convert a BinaryStruct endiannes
"""

import logging

from copy import deepcopy
from binary_structs.utils import *
from binary_structs.binary_struct import binary_struct, _is_binary_struct


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


def _convert_endianness(cls: BinaryField, new_bases: tuple[type], endianness: Endianness):
    """
    Convert the endianness of a single class to the given endianness.
    The class is being rebuilt in order to not destroy the old one.
    """

    logging.debug(f'Converting endianness for {cls}')

    # Filter out previously generated functions
    is_a_valid_field = lambda field: not callable(field[1]) or not hasattr(field[1], 'bs_generated_func')
    new_dict = dict(filter(is_a_valid_field, cls.__dict__.items()))

    new_dict['__annotations__'] = dict(deepcopy(cls.__dict__.get('__annotations__', {})))
    new_dict[f'_{cls.__name__}__bs_old_id'] = id(cls)

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
        if issubclass(base, BinaryField):
            new_bases.append(_convert_parents_classes(base, endianness))

        else:
            # Ignore non-BinaryFields
            new_bases.append(base)

    return _convert_endianness(cls, tuple(new_bases) or (object,), endianness)  \
           if _is_binary_struct(cls) else type(cls.__name__, tuple(new_bases) or (object,), dict(cls.__dict__))

def endian_decorator(cls, endianness: Endianness):
    if not _is_binary_struct(cls):
        raise TypeError('Given class is not a BinaryField!')

    def wrap(cls):
        return _convert_parents_classes(cls, endianness)

    if cls is None:
        return wrap

    return wrap(cls)


def little_endian(cls: BinaryField = None):
    """
    Convert a BinaryField class to little_endian
    """

    return endian_decorator(cls, Endianness.LITTLE)


def big_endian(cls: BinaryField = None):
    """
    Convert a BinaryField class to big_endian
    """

    return endian_decorator(cls, Endianness.BIG)
