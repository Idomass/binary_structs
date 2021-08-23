"""
This file has the implementation for TypedBuffer.
It is used by BinaryBuffer and binary_structs
"""
from typing import Iterable, SupportsIndex


class TypedBuffer(list):
    """
    TypedBuffer, is a list the enforces type of its elements
    """

    def __init__(self, underlying_type: type, buf: list = []):
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

    def __setitem__(self, index_or_slice, element):
        if isinstance(index_or_slice, slice):
            super().__setitem__(index_or_slice, [self._build_new_element(i) for i in element])

        else:
            super().__setitem__(index_or_slice, self._build_new_element(element))

    def append(self, element) -> None:
        super().insert(len(self), self._build_new_element(element))
