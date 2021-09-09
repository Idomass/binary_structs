"""
This file implements BinaryBuffer: a list with a type and a maximum size.
It is used by the binary_struct class instead of lists.
"""

from utils.binary_field import BinaryField
from utils.buffers.typed_buffer import TypedBuffer


class MaxSizeExceededError(Exception):
    """
    Indicates that a SizedList had it max size exceed the given
    boundries.
    """


class BinaryBuffer(TypedBuffer):
    """
    A list with a type and maximum size.
    Buffer will attempt to construct the object using the underlying type,
    and the passed parameter.
    """

    def __init__(self, underlying_type: BinaryField, size: int, buf: list = []):
        """
        A buffer with the given size will be created with empty instances in order
        to complete the buffer
        """

        self._size = size
        if len(buf) > self._size:
            raise MaxSizeExceededError('Given buffer is too big!')

        super().__init__(underlying_type, buf)

        # Fill with empty instances
        for index in range(len(self), self._size):
            super().insert(index, self._underlying_type())

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
