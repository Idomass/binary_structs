"""
This file implements BinaryBuffer class.

The BinaryBuffer expands the API of ctypes's buffers.
"""

from functools import lru_cache
from typing import Iterable


@lru_cache
def new_binary_buffer(underlying_type: type, size: int):
    """
    Generate a new binary buffer.
    A binary buffer is a wrapper to ctypes buffers
    """

    class BinaryBuffer(underlying_type * size):
        _is_binary_field = True
        static_size = size
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


    BinaryBuffer.deserialize = BinaryBuffer.from_buffer

    return BinaryBuffer
