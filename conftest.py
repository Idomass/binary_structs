import pytest
from binary_struct import binary_struct


@pytest.fixture
def SimpleClass():
    @binary_struct()
    class A:
        a: int

    return A

@pytest.fixture
def ComplexClass():
    @binary_struct
    class A:
        num: int
        line: str
        buf: bytes

    return A
