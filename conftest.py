import pytest

from binary_struct import binary_struct
from buffers.typed_buffer import TypedBuffer
from utils.binary_field import uint8_t, uint32_t


# buffers
@pytest.fixture
def typed_buffer():
    return TypedBuffer(uint8_t, [97] * 20)

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
        a: uint8_t

    return A

@pytest.fixture
def BufferClass():
    @binary_struct
    class A:
        size: uint32_t
        buf: [uint8_t, 32]

    return A

@pytest.fixture
def NestedClass(BufferClass):
    @binary_struct
    class A:
        buffer: BufferClass
        magic: uint32_t

    return A

@pytest.fixture
def DuplicateClass():
    @binary_struct
    class A:
        magic: uint32_t
        magic: uint32_t

    return A

@pytest.fixture
def DynamicClass():
    @binary_struct
    class A:
        magic: uint8_t
        buf: [uint8_t]

    return A

@pytest.fixture
def InheritedClass(BufferClass):
    @binary_struct
    class A(BufferClass):
        magic: uint32_t

    return A

@pytest.fixture
def MultipleInheritedClass(BufferClass, SimpleClass):
    @binary_struct
    class A(BufferClass, SimpleClass):
        magic: uint32_t

    return A

@pytest.fixture
def InheritedAndNestedClass(NestedClass, BufferClass):
    @binary_struct
    class A(NestedClass):
        buf2: BufferClass

    return A

@pytest.fixture
def MonsterClass(EmptyClass, NestedClass, SimpleClass, DynamicClass):
    @binary_struct
    class A(NestedClass, SimpleClass):
        dynamic: DynamicClass
        empty: EmptyClass
        bruh: uint8_t

    return A
