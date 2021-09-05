"""
Binary field is used by binary structs.
Each field in binary structs must implement:
    - serialization
    - deserialization
    - size property
    - endianness for ? types

Binary field enforces that each class implements these things.
1"""

import struct
import ctypes

from abc import abstractmethod
from typing import List


class BinaryField():
    @abstractmethod
    def deserialize(self, buffer):
        pass

    @abstractmethod
    def __bytes__(self):
        pass

    @property
    @abstractmethod
    def size_in_bytes(self):
        pass

    #TODO Must be a better way to implement this
    @staticmethod
    def is_binary_field(kind: type):
        return (hasattr(kind, 'deserialize') and callable(kind.deserialize) and
                hasattr(kind, '__bytes__') and callable(kind.__bytes__) and
                hasattr(kind, 'size_in_bytes') and isinstance(kind.size_in_bytes, property))


class PrimitiveTypeField(BinaryField):
    """
    Designed for primitive ctypes types
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

        return super().__eq__(number)

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

def big_endian(cls=None):
    def wrap(cls):
        cls.FORMAT = f'>{cls.FORMAT}'
        return cls

    if cls is None:
        return wrap

    return wrap(cls)

@big_endian
class be_int8_t(int8_t):
    pass

@big_endian
class be_uint8_t(uint8_t):
    pass

@big_endian
class be_int16_t(int16_t):
    pass

@big_endian
class be_uint16_t(uint16_t):
    pass

@big_endian
class be_int32_t(int32_t):
    pass

@big_endian
class be_uint32_t(uint32_t):
    pass

@big_endian
class be_int64_t(int64_t):
    pass

@big_endian
class be_uint64_t(uint64_t):
    pass
