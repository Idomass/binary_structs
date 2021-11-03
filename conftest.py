import pytest

from endianness import big_endian, little_endian
from utils.binary_field import uint8_t, uint32_t
from utils.buffers.typed_buffer import TypedBuffer
from binary_struct import binary_struct, _process_class

# misc
def empty_decorator(cls):
    return cls

available_decorators = [
    [empty_decorator, '='],
    [big_endian, '>'],
    [little_endian, '<']
]

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

# Default values
@binary_struct
class DefaultValueClass:
    default_value: uint8_t = 5

@binary_struct
class DefaultTypedBufferClass:
    buf: [uint8_t] = range(5)

@binary_struct
class DefaultBinaryBufferClass:
    buf: [uint8_t, 10] = range(5)

@binary_struct
class DefaultNestedClass:
    nested: BufferClass = BufferClass(5, range(3))

@binary_struct
class DefaultNestedArgsClass:
    nested: BufferClass = [5, range(7)]

@binary_struct
class DefaultNestedKWargsClass:
    nested: BufferClass = {'size': 5}

@binary_struct
class DefaultInheritedClass(DefaultNestedClass):
    pass

default_structs = [
    DefaultValueClass(5),
    DefaultBinaryBufferClass(list(range(5)) + [0] * 5),
    DefaultTypedBufferClass(list(range(5))),
    DefaultNestedClass([5, range(3)]),
    DefaultNestedArgsClass([5, range(7)]),
    DefaultNestedKWargsClass(nested={'size': 5}),
    DefaultInheritedClass([5, range(3)]),
]

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

@pytest.fixture
def DefaultTypedBufferClassFixture():
    return DefaultTypedBufferClass

# Caching
@pytest.fixture(autouse=True)
def clear_cache():
    _process_class.cache_clear()
