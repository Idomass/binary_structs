"""
This file include all "base" types that can be used inside of a binary struct.
Each type manages a region of memory.
"""

import re

from ctypes import c_int8, c_uint8, c_int16, c_uint16, c_int32, c_uint32, c_int64, c_uint64


INT_RE_EXPR = re.compile('(le|be)_(u*)int([0-9]+)_t')


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


    # Functions that will be added to the class
    def __new__(cls, *args, **kwargs):
        # Allocate memory and assign ctypes to handle it
        mem = memoryview(bytearray(size_in_bytes))
        self = cls.from_buffer(mem)

        # Assign memory to the new instance
        self._mem = mem

        return self


    def __eq__(self, other):
        return self.value == getattr(other, 'value', other)


    def __invert__(self) -> bytes:
        return bytes(~x & 0xff for x in bytes(self))


    @classmethod
    def deserialize(cls, buf):
        new_cls = cls.from_buffer(buf)
        new_cls._mem = buf

        return new_cls


    @property
    def memory(self):
        return self._mem


    int_dict = {
        # Attributes
        '_is_binary_field': True,
        'static_size': size_in_bytes,
        'signed': signed,
        'size_in_bytes': size_in_bytes,
        'memory': memory,

        # Functions
        '__new__': __new__,
        '__eq__': __eq__,
        '__invert__': __invert__,
        'deserialize': deserialize
    }

    new_cls = type(cls.__name__, (ctypes_class, ), int_dict)

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
class be_int8_t:
    pass

@_generate_integer_class
class be_uint8_t:
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
