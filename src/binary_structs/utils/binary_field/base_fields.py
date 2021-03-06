"""
This file include all "base" types that can be used inside of a binary struct.
Each type manages a region of memory.
"""

import re
import sys
from ctypes import c_int8, c_uint8, c_int16, c_uint16, c_int32, c_uint32, c_int64, c_uint64
from enum import Enum

INT_RE_EXPR = re.compile('(le|be)_(u*)int([0-9]+)_t')


class Endianness(Enum):
    NONE = ''
    BIG = 'be'
    LITTLE = 'le'
    HOST = LITTLE if sys.byteorder == 'little' else BIG


class PrimitiveTypeField:
    """
    Designed for primitive ctypes types, wraps them and adds functionalities
    """


def _generate_integer_class(cls):
    """
    Creates a new integer class, based on the given name.

    The generated class will inherit from the correct ctypes type, and will implement an new function
    that will build a new instance on an exported memory region.
    """

    endianness, sign, size_in_bits = re.match(INT_RE_EXPR, cls.__name__).groups()
    size_in_bytes = int(size_in_bits) // 8
    signed = not sign

    # Get the correct parent with the correct endianness
    ctypes_class = getattr(globals()[f'c_{sign}int{size_in_bits}'], f'__ctype_{endianness}__')

    def __eq__(self, other):
        return self.value == getattr(other, 'value', other)


    def __bitwise_operation(op1, op2, operation) -> bytes:
        op1_bytes = bytes(op1.memory)
        op2_bytes = bytes(op2.memory)

        bigger_buf_len = max(len(op1_bytes), len(op2_bytes))

        op1_bytes = op1_bytes + b'\x00' * (bigger_buf_len - len(op1_bytes))
        op2_bytes = op2_bytes + b'\x00' * (bigger_buf_len - len(op2_bytes))

        return bytes(getattr(int, operation)(a, b) for (a, b) in zip(op1_bytes, op2_bytes))


    def __and__(self, other) -> bytes:
        return __bitwise_operation(self, other, '__and__')


    def __or__(self, other) -> bytes:
        return __bitwise_operation(self, other, '__or__')


    def __xor__(self, other) -> bytes:
        return __bitwise_operation(self, other, '__xor__')


    def __invert__(self) -> bytes:
        return bytes(~x & 0xff for x in self.memory)

    def __str__(self) -> str:
        return str(self.value)


    @property
    def memory(self) -> memoryview:
        return memoryview(self).cast('B', (size_in_bytes,))


    int_dict = {
        # Attributes
        '_is_binary_field': True,
        'memory': memory,
        'static_size': size_in_bytes,
        'signed': signed,
        'size_in_bytes': size_in_bytes,

        # Functions
        '__eq__': __eq__,
        '__and__': __and__,
        '__or__': __or__,
        '__xor__': __xor__,
        '__invert__': __invert__,
        '__str__': __str__,
    }

    new_cls = type(cls.__name__, (ctypes_class, PrimitiveTypeField, ), int_dict)
    # Set an alias for deserialize for all class implementations
    setattr(new_cls,                'deserialize', new_cls.from_buffer)
    setattr(new_cls.__ctype_le__,   'deserialize', new_cls.__ctype_le__.from_buffer)
    setattr(new_cls.__ctype_be__,   'deserialize', new_cls.__ctype_be__.from_buffer)

    # From the python source code:
    # "Each *simple* type that supports different byte orders has an
    # __ctype_be__ attribute that specifies the same type in BIG ENDIAN
    # byte order, and a __ctype_le__ attribute that is the same type in
    # LITTLE ENDIAN byte order."
    # This means that our class have a big endain and a little endian versions.
    # Return the correct one
    return getattr(new_cls, f'__ctype_{endianness}__') if new_cls.static_size != 1 else new_cls


@_generate_integer_class
class le_int8_t:
    pass

@_generate_integer_class
class le_uint8_t:
    pass

@_generate_integer_class
class le_int16_t:
    pass

@_generate_integer_class
class le_uint16_t:
    pass

@_generate_integer_class
class le_int32_t:
    pass

@_generate_integer_class
class le_uint32_t:
    pass

@_generate_integer_class
class le_int64_t:
    pass

@_generate_integer_class
class le_uint64_t:
    pass

@_generate_integer_class
class be_int16_t:
    pass

@_generate_integer_class
class be_uint16_t:
    pass

@_generate_integer_class
class be_int32_t:
    pass

@_generate_integer_class
class be_uint32_t:
    pass

@_generate_integer_class
class be_int64_t:
    pass

@_generate_integer_class
class be_uint64_t:
    pass
