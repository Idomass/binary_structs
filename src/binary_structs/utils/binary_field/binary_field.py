"""
Binary field is an interface used by binary structs.
Each field in binary structs must implement:
    - serialization
    - deserialization
    - size property

Binary field is an interface for such these things.

PrimitiveTypeField is a primitive-ctypes based field,
and this file adds the classic primitive types that
implement BinaryField interface
"""

import sys
import struct
import ctypes

from enum import Enum
from abc import abstractmethod


class Endianness(Enum):
    NONE = ''
    BIG = 'be'
    LITTLE = 'le'
    HOST = LITTLE if sys.byteorder == 'little' else BIG


class BinaryField:
    """
    An interface for memebers of a binary_struct.

    NOTE: You shouldn't use this interface in your classes,
    instead, use the binary_struct decorator
    """

    @abstractmethod
    def __bytes__(self) -> bytes:
        pass

    @abstractmethod
    def __eq__(self, other) -> bool:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    @property
    @abstractmethod
    def size_in_bytes(self):
        pass

    @staticmethod
    def __bitwise_operation(op1, op2, operation) -> bytes:
        op1_bytes = bytes(op1)
        op2_bytes = bytes(op2)

        bigger_buf_len = max(len(op1_bytes), len(op2_bytes))

        op1_bytes += b'\x00' * (bigger_buf_len - len(op1_bytes))
        op2_bytes += b'\x00' * (bigger_buf_len - len(op2_bytes))

        return bytes(getattr(int, operation)(a, b) for (a, b) in zip(op1_bytes, op2_bytes))

    def __and__(self, other) -> bytes:
        return BinaryField.__bitwise_operation(self, other, '__and__')

    def __or__(self, other) -> bytes:
        return BinaryField.__bitwise_operation(self, other, '__or__')

    def __xor__(self, other) -> bytes:
        return BinaryField.__bitwise_operation(self, other, '__xor__')

    def __invert__(self) -> bytes:
        return bytes(~x & 0xff for x in bytes(self))


class PrimitiveTypeField(BinaryField):
    """
    Designed for primitive ctypes types, implements BinaryField
    """

    def __init__(self, value: int = 0):
        # Check compatiblilty
        if isinstance(value, PrimitiveTypeField):
            if not isinstance(value, type(self)):
                raise TypeError('Incompatible type passed!')

            value = value.value

        ctypes_parent = type(self).__base__.__bases__[1]
        ctypes_parent.__init__(self, value)

    @classmethod
    def deserialize(cls, buffer):
        if len(buffer) < ctypes.sizeof(cls):
            raise ValueError('Given buffer is too small!')

        return cls(struct.unpack(cls.FORMAT, buffer[:ctypes.sizeof(cls)])[0])

    # TODO, get rid of it
    @property
    def size_in_bytes(self):
        return ctypes.sizeof(self)

    def __eq__(self, number) -> bool:
        if isinstance(number, int):
            return self.value == number

        elif isinstance(number, PrimitiveTypeField):
            return self.value == number.value

        else:
            super().__eq__(number)

    @abstractmethod
    def __str__(self) -> str:
        endianness = "be" if ">" in self.FORMAT else Endianness.HOST.value
        sign = "u" if self.FORMAT.isupper() else 'i'

        return f'{endianness}_{sign}{self.size_in_bytes * 8}(0x{(self.value & 0xff):02X})'

    def __bytes__(self) -> bytes:
        return struct.pack(self.FORMAT, self.value)


class tmpl_int8_t(PrimitiveTypeField, ctypes.c_int8):
    FORMAT = 'b'


class tmpl_uint8_t(PrimitiveTypeField, ctypes.c_uint8):
    FORMAT = 'B'


class tmpl_int16_t(PrimitiveTypeField, ctypes.c_int16):
    FORMAT = 'h'


class tmpl_uint16_t(PrimitiveTypeField, ctypes.c_uint16):
    FORMAT = 'H'


class tmpl_int32_t(PrimitiveTypeField, ctypes.c_int32):
    FORMAT = 'i'


class tmpl_uint32_t(PrimitiveTypeField, ctypes.c_uint32):
    FORMAT = 'I'


class tmpl_int64_t(PrimitiveTypeField, ctypes.c_int64):
    FORMAT = 'q'


class tmpl_uint64_t(PrimitiveTypeField, ctypes.c_uint64):
    FORMAT = 'Q'


def endian_field(cls, format: str):
    """
    Makes sure that a BinaryField is of the given endianness
    """

    def wrap(cls):
        cls.FORMAT = f'{format}{cls.FORMAT}'
        cls.static_size = ctypes.sizeof(cls)
        return cls

    if cls is None:
        return wrap

    return wrap(cls)


def big_endian_field(cls=None):
    return endian_field(cls, '>')


def little_endian_field(cls=None):
    return endian_field(cls, '<')


@big_endian_field
class be_int8_t(tmpl_int8_t):
    pass


@big_endian_field
class be_uint8_t(tmpl_uint8_t):
    pass


@big_endian_field
class be_int16_t(tmpl_int16_t):
    pass


@big_endian_field
class be_uint16_t(tmpl_uint16_t):
    pass


@big_endian_field
class be_int32_t(tmpl_int32_t):
    pass


@big_endian_field
class be_uint32_t(tmpl_uint32_t):
    pass


@big_endian_field
class be_int64_t(tmpl_int64_t):
    pass


@big_endian_field
class be_uint64_t(tmpl_uint64_t):
    pass


@little_endian_field
class le_int8_t(tmpl_int8_t):
    pass


@little_endian_field
class le_uint8_t(tmpl_uint8_t):
    pass


@little_endian_field
class le_int16_t(tmpl_int16_t):
    pass


@little_endian_field
class le_uint16_t(tmpl_uint16_t):
    pass


@little_endian_field
class le_int32_t(tmpl_int32_t):
    pass


@little_endian_field
class le_uint32_t(tmpl_uint32_t):
    pass


@little_endian_field
class le_int64_t(tmpl_int64_t):
    pass


@little_endian_field
class le_uint64_t(tmpl_uint64_t):
    pass
