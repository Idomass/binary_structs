"""
This file implements a list with a maximum size.
It is used by the binary_struct class instead of lists.

#TODO find a better way to hook checks
"""


class MaxSizeExceededError(Exception):
    """
    Indicates that a SizedList had it max size exceed the given
    boundries.
    """


class Buffer(list):
    """
    A list with type and maximum size.
    Buffer will attempt to construct the object using the underlying type,
    and the passed parameter.
    Useful for libraries that convert the list into a bytes representation
    """

    def __init__(self, underlying_type: type, max_size: int, /, buf: list = []):
        self._underlying_type = underlying_type
        self._max_size = max_size

        self._extend_buf(buf)

    def _add_to_buf(self, index: int, object) -> None:
        """
        A method used to add an element to the buffer
        """

        if len(self) == self._max_size:
            raise MaxSizeExceededError('Failed to insert to buffer, max size reached!')

        try:
            super().insert(index, self._underlying_type(object))

        except [ValueError, TypeError]:
            raise TypeError(f'Failed buiding {self._underlying_type} with type {type(object)}')

    def _extend_buf(self, iterable) -> None:
        """
        A method used to extend the buffer
        """

        for index, object in enumerate(iterable):
            self._add_to_buf(len(self) + index, object)

    def append(self, object) -> None:
        self._add_to_buf(len(self), object)

    def extend(self, iterable) -> None:
        self._extend_buf(iterable)

    def insert(self, index: int, object) -> None:
        self._add_to_buf(index, object)

    def __iadd__(self, iterable):
        self._extend_buf(iterable)

        return self

    def __imul__(self, n: int):
        if n * len(self) > self._max_size:
            raise MaxSizeExceededError('Failed multiplying buffer, max size reached!')

        return super().__imul__(n)

    def __bytes__(self) -> bytes:
        return b''.join(bytes(element) for element in self)
