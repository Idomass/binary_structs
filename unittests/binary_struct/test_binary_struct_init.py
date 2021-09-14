import pytest

from binary_struct import binary_struct
from utils.binary_field import uint32_t, uint8_t
from utils.buffers.binary_buffer import MaxSizeExceededError


def test_empty_class(EmptyClassFixture):
    EmptyClassFixture()

def test_empty_class_paranthesses():
    @binary_struct()
    class A:
        pass

    A()

def test_valid_simple_class(SimpleClassFixture):
    a = SimpleClassFixture(5)

    assert a.a.value == 5

def test_invalid_simple_class(SimpleClassFixture):
    with pytest.raises(TypeError):
        SimpleClassFixture(10, 7)

def test_invalid_decorated_twice():
    with pytest.raises(TypeError):
        @binary_struct
        @binary_struct
        class A:
            a: uint8_t

def test_valid_simple_class_assert_type(SimpleClassFixture):
    a = SimpleClassFixture(5)

    assert isinstance(a.a, uint8_t)

def test_valid_type_alias():
    tmp = uint32_t

    @binary_struct
    class A:
        b: tmp

    a = A(255)

    assert isinstance(a.b, uint32_t)
    assert a.b.value == 255

def test_invalid_wrong_values(BufferClassFixture):
    with pytest.raises(TypeError):
        BufferClassFixture('Noder', 15)

def test_valid_buffer(BufferClassFixture):
    a = BufferClassFixture(32, [97] * 32)

    for element in a.buf:
        assert element.value == 97

    assert isinstance(a.buf[0], uint8_t)

def test_invalid_length_buffer(BufferClassFixture):
    with pytest.raises(MaxSizeExceededError):
        BufferClassFixture(90, [100] * 90)

def test_valid_empty_buffer(BufferClassFixture):
    a = BufferClassFixture(5, [])

    for element in a.buf:
        assert element.value == 0

def test_invalid_buffer_overflow(BufferClassFixture):
    with pytest.raises(MaxSizeExceededError):
        a = BufferClassFixture(32, [67] * 32)
        a.buf.append(6)

def test_valid_nested_class(BufferClassFixture, NestedClassFixture):
    a = BufferClassFixture(5, range(5))
    b = NestedClassFixture(a, 0xdeadbeef)

    assert isinstance(b.buffer, BufferClassFixture)
    assert b.buffer is a

def test_valid_class_duplicate_members(DuplicateClassFixture):
    a = DuplicateClassFixture(0xff)

    assert isinstance(a.magic, uint32_t)
    assert a.magic.value == 0xff

def test_valid_class_dynamic_buffer(DynamicClassFixture):
    a = DynamicClassFixture(5, [97] * 50)

    assert a.magic.value == 5
    for element in a.buf:
        assert element.value == 97

def test_valid_2_classes_are_different(DynamicClassFixture, BufferClassFixture):
    assert DynamicClassFixture is not BufferClassFixture

def test_valid_class_custom_init_implementation():
    @binary_struct
    class A:
        times_two: uint8_t

        def __init__(self, times_two):
            # TODO Unfortunately I can't find a better solution
            super(type(self), self).__init__(times_two * 2)

    a = A(5)

    assert a.times_two.value == 10

def test_valid_class_with_size_in_bytes_attribute():
    with pytest.raises(AttributeError):
        @binary_struct
        class A:
            size_in_bytes: uint32_t

def test_valid_class_with_FORMAT_attribute():
    with pytest.raises(AttributeError):
        @binary_struct
        class A:
            FORMAT: uint32_t

def test_valid_class_init_with_no_params(BufferClassFixture):
    a = BufferClassFixture()

    assert a.size.value == 0
    for element in a.buf:
        assert element.value == 0
    assert a.size_in_bytes == 36

def test_valid_default_ctor_types_are_different():
    @binary_struct
    class A:
        a: uint32_t
        b: uint32_t

    a = A()

    assert a.a is not a.b

def test_valid_default_ctor_instances_are_different():
    @binary_struct
    class A:
        a: uint32_t
        b: uint32_t

    a = A()
    b = A()

    assert a.a is not b.b
    assert a.a is not b.a
    assert a.b is not b.b
