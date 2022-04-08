"""
This file implements BinaryBuffer class: a list with a type and a maximum size.
It is used by the binary_struct class instead of lists.
"""

from functools import lru_cache
from binary_structs.utils.buffers import new_typed_buffer


class MaxSizeExceededError(Exception):
    """
    Indicates that a SizedList had it max size exceed the given boundries.
    """


@lru_cache
def new_binary_buffer(underlying_type: type, size: int):
    """
    Generate a new binary buffer.
    A binary buffer is a typed buffer that enforces size
    """

    TypedBuffer = new_typed_buffer(underlying_type)

    class BinaryBuffer(TypedBuffer):
        """
        A list with a type and maximum size.
        Buffer will attempt to construct the object using the underlying type,
        and the passed parameter.
        """

        static_size = size

        def __init__(self, buf: list = []):
            """
            A buffer with the given size will be created with empty instances in order
            to complete the buffer
            """

            if len(buf) > size:
                raise MaxSizeExceededError('Given buffer is too big!')

            super().__init__(buf)

            # Fill with empty instances
            for index in range(len(self), size):
                super().insert(index, underlying_type())

        @classmethod
        def deserialize(cls, buf: bytes):
            new_buf = cls()
            underlying_size = underlying_type.static_size

            for index in range(size):
                new_element = underlying_type.deserialize(buf[:underlying_size])
                new_buf.__setitem__(index, new_element)

                buf = buf[underlying_size:]

            return new_buf

        def clear(self) -> None:
            super().clear()
            # Fill with empty instances
            for index in range(size):
                super().insert(index, underlying_type())

        def remove(self, value) -> None:
            raise ValueError('Cannot remove items from a fixed size list!')

        def insert(self, index, element) -> None:
            raise MaxSizeExceededError('Can\'t insert to an already full buffer')

        def append(self, element) -> None:
            raise MaxSizeExceededError('Can\'t append to an already full buffer')

        def extend(self, iterable) -> None:
            raise MaxSizeExceededError('Can\'t extend an already full buffer')

        def __iadd__(self, iterable):
            raise MaxSizeExceededError('Can\'t add to an already full buffer')

        def __imul__(self, n: int):
            raise MaxSizeExceededError('Can\'t multiply to an already full buffer')

        def __getitem__(self, index_or_slice):
            if isinstance(index_or_slice, slice):
                typed_buf = super().__getitem__(index_or_slice)

                return new_binary_buffer(underlying_type, len(typed_buf))(typed_buf)

            else:
                return super().__getitem__(index_or_slice)

        @staticmethod
        def from_bytes(buf: bytes):
            typed_buf = TypedBuffer.from_bytes(buf)

            return BinaryBuffer(typed_buf)

    return BinaryBuffer
