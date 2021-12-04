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
    def deserialize(self, buffer):
        pass

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

    def deserialize(self, buffer):
        if len(buffer) < self.size_in_bytes:
            raise ValueError('Given buffer is too small!')

        self.__init__(struct.unpack(self.FORMAT, buffer)[0])

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


class int8_t(ctypes.c_int8, PrimitiveTypeField):
    FORMAT = 'b'


class uint8_t(ctypes.c_uint8, PrimitiveTypeField):
    FORMAT = 'B'


class int16_t(ctypes.c_int16, PrimitiveTypeField):
    FORMAT = 'h'


class uint16_t(ctypes.c_uint16, PrimitiveTypeField):
    FORMAT = 'H'


class int32_t(ctypes.c_int32, PrimitiveTypeField):
    FORMAT = 'i'


class uint32_t(ctypes.c_uint32, PrimitiveTypeField):
    FORMAT = 'I'


class int64_t(ctypes.c_int64, PrimitiveTypeField):
    FORMAT = 'q'


class uint64_t(ctypes.c_uint64, PrimitiveTypeField):
    FORMAT = 'Q'


def big_endian_field(cls=None):
    """
    Makes sure that a BinaryField is big endian
    """

    def wrap(cls):
        cls.FORMAT = f'>{cls.FORMAT}'
        return cls

    if cls is None:
        return wrap

    return wrap(cls)


@big_endian_field
class be_int8_t(int8_t):
    pass


@big_endian_field
class be_uint8_t(uint8_t):
    pass


@big_endian_field
class be_int16_t(int16_t):
    pass


@big_endian_field
class be_uint16_t(uint16_t):
    pass


@big_endian_field
class be_int32_t(int32_t):
    pass


@big_endian_field
class be_uint32_t(uint32_t):
    pass


@big_endian_field
class be_int64_t(int64_t):
    pass


@big_endian_field
class be_uint64_t(uint64_t):
    pass
