import pytest

from endianness import big_endian
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
    class EmptyClass:
        pass

    return EmptyClass

@pytest.fixture
def SimpleClass():
    @binary_struct
    class SimpleClass:
        a: uint8_t

    return SimpleClass

@pytest.fixture
def BufferClass():
    @binary_struct
    class BufferClass:
        size: uint32_t
        buf: [uint8_t, 32]

    return BufferClass

@pytest.fixture
def NestedClass(BufferClass):
    @binary_struct
    class NestedClass:
        buffer: BufferClass
        magic: uint32_t

    return NestedClass

@pytest.fixture
def DuplicateClass():
    @binary_struct
    class DuplicateClass:
        magic: uint32_t
        magic: uint32_t

    return DuplicateClass

@pytest.fixture
def DynamicClass():
    @binary_struct
    class DynamicClass:
        magic: uint8_t
        buf: [uint8_t]

    return DynamicClass

@pytest.fixture
def InheritedClass(BufferClass):
    @binary_struct
    class InheritedClass(BufferClass):
        magic: uint32_t

    return InheritedClass

@pytest.fixture
def MultipleInheritedClass(BufferClass, SimpleClass):
    class SomeBaseClass:
        def foo(self):
            return True

    @binary_struct
    class MultipleInheritedClass(BufferClass, SimpleClass, SomeBaseClass):
        magic: uint32_t

    return MultipleInheritedClass

@pytest.fixture
def InheritedAndNestedClass(NestedClass, BufferClass):
    @binary_struct
    class InheritedAndNestedClass(NestedClass):
        buf2: BufferClass

    return InheritedAndNestedClass

@pytest.fixture
def MonsterClass(EmptyClass, NestedClass, SimpleClass, DynamicClass):
    @binary_struct
    class MonsterClass(NestedClass, SimpleClass):
        dynamic: DynamicClass
        empty: EmptyClass
        magic2: uint8_t

    return MonsterClass

@pytest.fixture
def BEBufferClass():
    @big_endian
    @binary_struct
    class BEBufferClass():
        size: uint32_t
        buf: [uint8_t, 32]

    return BEBufferClass

@pytest.fixture
def BENestedClass(BufferClass):
    @big_endian
    @binary_struct
    class BENestedClass:
        buffer: BufferClass
        magic: uint32_t

    return BENestedClass

@pytest.fixture
def BEMultipleInheritedClass(MultipleInheritedClass):
    @big_endian
    class BEMultipleInheritedClass(MultipleInheritedClass):
        pass

    return BEMultipleInheritedClass

@pytest.fixture
def BEInheritedAndNestedClass(InheritedAndNestedClass):
    @big_endian
    class BEInheritedAndNestedClass(InheritedAndNestedClass):
        pass

    return BEInheritedAndNestedClass
