import pytest

from utils.buffers.typed_buffer import TypedBuffer
from utils.binary_field import uint8_t, uint32_t
from binary_struct import binary_struct, _process_class


# buffers
@pytest.fixture
def typed_buffer():
    return TypedBuffer(uint8_t, [97] * 20)

# binary_structs
# Classes
class SomeBaseClass:
    def foo(self):
        return True

@binary_struct
class EmptyClass:
    pass

@binary_struct
class SimpleClass:
    a: uint8_t

@binary_struct
class BufferClass:
    size: uint32_t
    buf: [uint8_t, 32]

@binary_struct
class NestedClass:
    buffer: BufferClass
    magic: uint32_t

@binary_struct
class DuplicateClass:
    magic: uint32_t
    magic: uint32_t

@binary_struct
class DynamicClass:
    magic: uint8_t
    buf: [uint8_t]

@binary_struct
class InheritedClass(BufferClass):
    magic: uint32_t

@binary_struct
class MultipleInheritedClass(BufferClass, SimpleClass, SomeBaseClass):
    magic: uint32_t

@binary_struct
class InheritedAndNestedClass(NestedClass):
    buf2: BufferClass

@binary_struct
class MonsterClass(NestedClass, SimpleClass):
    dynamic: DynamicClass
    empty: EmptyClass
    magic2: uint8_t

# Fixtures
@pytest.fixture
def EmptyClassFixture():
    return EmptyClass

@pytest.fixture
def SimpleClassFixture():
    return SimpleClass

@pytest.fixture
def BufferClassFixture():
    return BufferClass

@pytest.fixture
def NestedClassFixture():
    return NestedClass

@pytest.fixture
def DuplicateClassFixture():
    return DuplicateClass

@pytest.fixture
def DynamicClassFixture():
    return DynamicClass

# Inheritence testing
@pytest.fixture
def InheritedClassFixture():
    return InheritedClass

@pytest.fixture
def MultipleInheritedClassFixture():
    return MultipleInheritedClass

@pytest.fixture
def InheritedAndNestedClassFixture():
    return InheritedAndNestedClass

@pytest.fixture
def MonsterClassFixture():
    return MonsterClass

# Caching
@pytest.fixture(autouse=True)
def clear_cache():
    _process_class.cache_clear()
