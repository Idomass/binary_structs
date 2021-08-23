import pytest
import ctypes

from binary_struct import binary_struct
from buffers.typed_buffer import TypedBuffer
from buffers.binary_buffer import BinaryBuffer


# buffers
@pytest.fixture
def typed_buffer():
    return TypedBuffer(ctypes.c_uint8, [97] * 20)

# binary_structs
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
        buf: BinaryBuffer
        magic: ctypes.c_uint32

    return A

@pytest.fixture
def BufferClass():
    @binary_struct
    class A:
        size: ctypes.c_uint32
        buf: [ctypes.c_uint8, 32]

    return A

@pytest.fixture
def NestedClass(BufferClass):
    @binary_struct
    class A:
        buffer: BufferClass
        magic: ctypes.c_uint32

    return A

@pytest.fixture
def DuplicateClass():
    @binary_struct
    class A:
        magic: ctypes.c_uint32
        magic: ctypes.c_uint32

    return A
