import pytest
import ctypes

from ctypes import c_void_p
from binary_struct import binary_struct

@pytest.fixture
def EmptyClass():
    @binary_struct
    class A:
        pass

    return A

@pytest.fixture
def SimpleClass():
    @binary_struct
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

@pytest.fixture
def ModuleClass():
    @binary_struct
    class A:
        ptr: c_void_p
        size: ctypes.c_uint32

    return A

@pytest.fixture
def BufferClass():
    @binary_struct
    class A:
        size: ctypes.c_uint32
        buf: [ctypes.c_uint8, 32]

    return A
