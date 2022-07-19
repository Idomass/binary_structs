"""
This file implements BinaryBuffer class.

The BinaryBuffer expands the API of ctypes's buffers.
"""

from functools import lru_cache
from typing import Iterable


class BufferField:
    """
    Deperecated, used for backwards-compatibility
    """


@lru_cache
def new_binary_buffer(underlying_type: type, size: int):
    """
    Generate a new binary buffer.
    A binary buffer is a wrapper to ctypes buffers
    """

    if hasattr(underlying_type, f'_{underlying_type.__name__}__is_binary_struct'):
        # PATCH, return a tuple with empty instances in order to support a list of binary structs API
        class BinaryTuple(tuple):
            _is_binary_field = True
            element_type = underlying_type
            static_size = size * underlying_type.static_size
            size_in_bytes = size * underlying_type.static_size

            def __new__(cls, *iterable, **kwargs):
                init_arr = []

                for element in iterable:
                    if isinstance(element, underlying_type):
                        init_arr.append(element)

                    elif getattr(type(element), 'binary_fields', {}) == underlying_type.binary_fields:
                        init_arr.append(element)

                    # Support args initialization
                    elif isinstance(element, list):
                        init_arr.append(underlying_type(*element))

                    # Support kwargs initialization
                    elif isinstance(element, dict):
                        init_arr.append(underlying_type(**element))

                    else:
                        # Try to build new element
                        init_arr.append(underlying_type(element))

                # Fill the rest of the buffer with empty instances, by calling _bs_init
                for _ in range(len(init_arr), size):
                    new_instance = underlying_type.__new__(underlying_type)
                    new_instance._bs_init()
                    init_arr.append(new_instance)

                return super().__new__(cls, init_arr)


            def __bytes__(self) -> bytes:
                return b''.join(bytes(x) for x in self)


            def __str__(self) -> str:
                return str(bytes(self))


            @classmethod
            def deserialize(cls, buf: bytearray):
                assert len(buf) >= BinaryTuple.static_size, 'Given buffer is too small!'

                init_arr = []
                for element_index in range(0, BinaryTuple.static_size, underlying_type.static_size):
                    init_arr.append(underlying_type.deserialize(buf[element_index:]))

                return cls.__new__(cls, *init_arr)

        return BinaryTuple

    class BinaryBuffer(BufferField, underlying_type * size):
        _is_binary_field = True
        element_type = underlying_type
        static_size = size * underlying_type.static_size
        size_in_bytes = size * underlying_type.static_size


        def __eq__(self, iterable: Iterable) -> bool:
            """
            Check if the given iterable is equal to this class.
            Check if bytes representation is equal
            """

            if not isinstance(iterable, type(self)):
                iterable = BinaryBuffer(*iterable)

            return memoryview(self) == memoryview(iterable)


        def __getitem__(self, index_or_slice):
            """
            Return a slice as a binary buffer instead of a list.
            """

            if isinstance(index_or_slice, slice):
                as_list = super().__getitem__(index_or_slice)

                return new_binary_buffer(underlying_type, len(as_list))(*as_list)

            return super().__getitem__(index_or_slice)


        def __str__(self) -> str:
            return str(bytes(self))


    BinaryBuffer.deserialize = BinaryBuffer.from_buffer

    return BinaryBuffer
