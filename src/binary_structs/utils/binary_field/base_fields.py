"""
This file include all "base" types that can be used inside of a binary struct.
Each type manages a region of memory.
"""

import re

from ctypes import c_int8, c_uint8, c_int16, c_uint16, c_int32, c_uint32, c_int64, c_uint64


INT_RE_EXPR = re.compile('(u*)int([0-9]+)_t')


def _generate_integer_class(cls):
    """
    Creates a new integer class, based on the given name.

    The generated class will inherit from the correct ctypes type, and will implement an new function
    that will build a new instance on an exported memory region.
    """

    sign, size_in_bits = re.match(INT_RE_EXPR, cls.__name__).groups()
    size_in_bytes = int(size_in_bits) // 8
    signed = not sign

    ctypes_class = globals()[f'c_{sign}int{size_in_bits}']

    # Functions that will be added to the class
    def __new__(cls, *args, **kwargs):
        # Allocate memory and assign ctypes to handle it
        mem = memoryview(bytearray(size_in_bytes))
        self = cls.from_buffer(mem)

        # Assign memory to the new instance
        self._mem = mem

        return self

    @property
    def memory(self):
        return self._mem


    int_dict = {
        # Attributes
        'signed': signed,
        'size': size_in_bytes,
        'memory': memory,

        # Functions
        '__new__': __new__
    }

    return type(cls.__name__, (ctypes_class, ), int_dict)


@_generate_integer_class
class int8_t:
    pass

@_generate_integer_class
class uint8_t:
    pass

@_generate_integer_class
class int16_t:
    pass

@_generate_integer_class
class uint16_t:
    pass

@_generate_integer_class
class int32_t:
    pass

@_generate_integer_class
class uint32_t:
    pass

@_generate_integer_class
class int64_t:
    pass

@_generate_integer_class
class uint64_t:
    pass
