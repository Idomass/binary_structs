import pytest

from utils.buffers.typed_buffer import TypedBuffer
from utils.binary_field import uint8_t, uint32_t
from binary_struct import binary_struct, _process_class

# misc
def empty_decorator(cls):
    return cls

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

# TODO: Dynamic classes that start with the buffer
# Will cause problems
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
class MultipleNestedClass:
    nested: NestedClass
    magic: uint32_t

# List for parameterize tests
test_structs = [
    [
        EmptyClass,
        {}
    ],
    [
        SimpleClass,
        {'a': 89}
    ],
    [
        BufferClass,
        {'size': 423652, 'buf': range(3)}
    ],
    [
        DuplicateClass,
        {'magic': 0xcafebabe}
    ],
    [
        DynamicClass,
        {'magic': 0xef, 'buf': range(99)}
    ],
    [
        InheritedClass,
        {'size': 50, 'buf': range(9), 'magic': 0x12345678}
    ],
    [
        MultipleInheritedClass,
        {'size': 99, 'buf': range(15), 'a': 7 ,'magic': 0x90807060}
    ],

    [
        NestedClass,
        {'buffer': [5, [1]], 'magic': 0xdeadbeef}
    ],
    [
        MultipleNestedClass,
        {'nested': {'buffer': [5, [1]], 'magic': 0xdeadbeef}, 'magic': 0xcafebabe}
    ]
]

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

# Caching
@pytest.fixture(autouse=True)
def clear_cache():
    _process_class.cache_clear()
