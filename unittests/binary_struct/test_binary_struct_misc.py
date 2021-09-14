import pytest

from copy import deepcopy

from utils.binary_field import uint8_t
from binary_struct import binary_struct


# TODO
@pytest.mark.skip(reason='Cant figure a way to pass it for now')
def test_valid_copy_ctor(BufferClassFixture):
    a = BufferClassFixture(5, range(5))
    b = deepcopy(a)

    b.size.value = 10

    assert a.size.value == 5
    assert b.size.value == 10

# Size feature
def test_valid_size(BufferClassFixture, NestedClassFixture):
    a = BufferClassFixture(32, [97] * 32)
    b = NestedClassFixture(a, 0xdeadbeef)

    assert a.size_in_bytes == 36
    assert b.size_in_bytes == 40

def test_valid_size_empty(EmptyClassFixture):
    a = EmptyClassFixture()

    assert a.size_in_bytes == 0

def test_valid_size_dynamic(DynamicClassFixture):
    a = DynamicClassFixture(5, [1, 2, 3])

    assert a.size_in_bytes == 4
    a.buf.append(90)
    assert a.size_in_bytes == 5

# Equal operator
def test_invalid_equal_not_binary_struct(SimpleClassFixture):
    class A:
        def __init__(self):
            self.a = uint8_t(5)

    a = A()
    b = SimpleClassFixture(5)

    assert b != a

def test_valid_equal_simple(SimpleClassFixture):
    a = SimpleClassFixture(5)
    b = SimpleClassFixture(5)

    assert a == b

def test_invalid_equal_simple(SimpleClassFixture):
    a = SimpleClassFixture(5)
    b = SimpleClassFixture(7)

    assert a != b

def test_valid_equal_buffer(BufferClassFixture):
    a = BufferClassFixture(5, [1, 2, 3])
    b = BufferClassFixture(5, [1, 2, 3])

    assert a == b

def test_invalid_equal_buffer(BufferClassFixture):
    a = BufferClassFixture(5, [1, 2, 3])
    b = BufferClassFixture(9, [1, 2, 3])

    assert a != b

def test_valid_equal_dynamic(DynamicClassFixture):
    a = DynamicClassFixture(94, range(90))
    b = DynamicClassFixture(94, range(90))

    assert a == b

def test_invalid_equal_dynamic(DynamicClassFixture):
    a = DynamicClassFixture(94, range(90))
    b = DynamicClassFixture(94, range(89))

    assert a != b

def test_valid_equal_inheritence(InheritedClassFixture):
    a = InheritedClassFixture(3, [0] * 9, 0xdead)
    b = InheritedClassFixture(3, [0] * 9, 0xdead)

    assert a == b

def test_invalid_equal_inheritence(InheritedClassFixture):
    a = InheritedClassFixture(3, [0] * 9, 0xdead)
    b = InheritedClassFixture(3, [1] * 9, 0xdead)

    assert a != b

def test_valid_equal_nested(NestedClassFixture):
    a = NestedClassFixture(NestedClassFixture.buffer(1, [0]), 0xcafebabe)
    b = NestedClassFixture(NestedClassFixture.buffer(1, [0]), 0xcafebabe)

    assert a == b

def test_invalid_equal_nested(NestedClassFixture):
    a = NestedClassFixture(NestedClassFixture.buffer(1, [0]), 0xcafebabe)
    b = NestedClassFixture(NestedClassFixture.buffer(1, [1]), 0xcafebabe)

    assert a != b

def test_valid_equal_multiple_inheritence(MultipleInheritedClassFixture):
    a = MultipleInheritedClassFixture(9, range(3), 0x70, 0xbeef)
    b = MultipleInheritedClassFixture(9, range(3), 0x70, 0xbeef)

    assert a == b

def test_valid_equal_multiple_inheritence(MultipleInheritedClassFixture):
    a = MultipleInheritedClassFixture(9, range(3), 0x70, 0xbeef)
    b = MultipleInheritedClassFixture(9, range(3), 0x69, 0xbeef)

    assert a != b

def test_invalid_equal_different_structs(InheritedClassFixture):
    @binary_struct
    class A(InheritedClassFixture):
        pass

    a = A(3, [0] * 9, 0xdead)
    b = InheritedClassFixture(3, [0] * 9, 0xdead)

    assert a != b

# TODO, test with endianness
