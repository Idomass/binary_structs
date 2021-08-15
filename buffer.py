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
    Useful for libraries that convert the list into a bytes representation
    """

    def __init__(self, underlying_type: type, max_size: int, /, *args, **kwargs):
        self._underlying_type = underlying_type
        self._max_size = max_size

        super().__init__(*args, **kwargs)

        if len(self) > self._max_size:
            raise MaxSizeExceededError('Given list is bigger than given size!')

        if not all(isinstance(i, self._underlying_type) for i in self):
            raise TypeError(f'Type mismatch! wrong type passed to buffer with type {self._underlying_type}')

    def _extend_buf(self, _iterable):
        """
        A method used by extend and __iadd__ since they implement the same logic
        """

        if len(_iterable) + len(self) > self._max_size:
            raise MaxSizeExceededError('Failed extending buffer, max size reached!')

        if not all(isinstance(i, self._underlying_type) for i in _iterable):
            raise TypeError(f'Trying to add wrong type to a buffer with type {self._underlying_type}')

        return super().__iadd__(_iterable)

    def append(self, _object) -> None:
        if not isinstance(_object, self._underlying_type):
            raise TypeError(f'Trying to append {type(_object)} to a buffer with type {self._underlying_type}')

        if len(self) == self._max_size:
            raise MaxSizeExceededError('Failed to append to buffer, max size reached!')

        return super().append(_object)

    def extend(self, _iterable) -> None:
        self._extend_buf(_iterable)

    def insert(self, _index: int, _object) -> None:
        if len(self) == self._max_size:
            raise MaxSizeExceededError('Failed to insert to buffer, max size reached!')

        if not isinstance(_object, self._underlying_type):
            raise TypeError(f'Trying to insert {type(_object)} to a buffer with type {self._underlying_type}')

        return super().insert(_index, _object)

    def __iadd__(self, _iterable):
        return self._extend_buf(_iterable)

    def __imul__(self, n: int):
        if n * len(self) > self._max_size:
            raise MaxSizeExceededError('Failed multiplying buffer, max size reached!')

        return super().__imul__(n)
