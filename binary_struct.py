"""
This file has the code for the binary_struct decorator.

Binary struct is essanitialy a c-like struct, with the comforts that come with python.
The library supports serialization and deserialization of objects, with a clear and clean API.s

Basic API:
@binary_struct
class BufferWithSize:
    size: ctypes.c_uint32
    buf: [ctypes.c_uint8, 64]
"""


def binary_struct(cls=None):
    """
    Return the class that was passed with auto-implemented dunder methods such as bytes,
    and a new c'tor for the class
    """

    def wrap(cls):
        return cls

    if cls is None:
        return wrap

    return wrap(cls)
