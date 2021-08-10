import pytest
from binary_struct import binary_struct


@pytest.fixture
def SimpleClass():
    @binary_struct()
    class A:
        a: int

    return A

