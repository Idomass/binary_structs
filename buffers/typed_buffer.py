"""
This file has the implementation for TypedBuffer.
It is used by BinaryBuffer and binary_structs.
It is used to enforce the type that is being added to
the buffer
"""

from utils.binary_field import BinaryField


class TypedBuffer(list):
    """
    TypedBuffer, is a list the enforces type of its elements
    """

    def __init__(self, underlying_type: BinaryField, buf: list = []):
        if not issubclass(underlying_type, BinaryField):
            raise TypeError('Field must implement BinaryField interface!')

        self._underlying_type = underlying_type

        for index, element in enumerate(buf):
            super().insert(index, self._build_new_element(element))

    def _build_new_element(self, element):
        """
        Validates that element is an instance of the underlying type
        Attempts to build the underlying type using element if not.

        raises TypeError if it cannot be converted into the underlying type
        """

        if isinstance(element, self._underlying_type):
            return element

        try:
            return self._underlying_type(element)

        except [ValueError, TypeError]:
            raise TypeError(f'Trying to add an element of {type(element)} to buffer of {self._underlying_type}\'s')

    def __setitem__(self, index_or_slice, element) -> None:
        if isinstance(index_or_slice, slice):
            return super().__setitem__(index_or_slice, [self._build_new_element(i) for i in element])

        else:
            return super().__setitem__(index_or_slice, self._build_new_element(element))

    def append(self, element) -> None:
        return super().append(self._build_new_element(element))

    def extend(self, iterable) -> None:
        return super().extend([self._build_new_element(element) for element in iterable])

    def insert(self, index, element) -> None:
        return super().insert(index, self._build_new_element(element))

    def __iadd__(self, iterable):
        return super().__iadd__([self._build_new_element(element) for element in iterable])

    def __bytes__(self) -> bytes:
        return b''.join(bytes(element) for element in self)

    @property
    def size_in_bytes(self):
        return sum(element.size_in_bytes for element in self)
