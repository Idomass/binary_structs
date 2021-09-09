import pytest

from copy import deepcopy
from binary_struct import binary_struct
from utils.binary_field import uint32_t, uint8_t
from buffers.binary_buffer import MaxSizeExceededError


def test_empty_class(EmptyClass):
    EmptyClass()

def test_empty_class_paranthesses():
    @binary_struct()
    class A:
        pass

    A()

def test_valid_simple_class(SimpleClass):
    a = SimpleClass(5)

    assert a.a.value == 5

def test_invalid_simple_class(SimpleClass):
    with pytest.raises(TypeError):
        SimpleClass(10, 7)

def test_invalid_decorated_twice():
    with pytest.raises(TypeError):
        @binary_struct
        @binary_struct
        class A:
            a: uint8_t

def test_valid_simple_class_assert_type(SimpleClass):
    a = SimpleClass(5)

    assert isinstance(a.a, uint8_t)

def test_valid_type_alias():
    tmp = uint32_t

    @binary_struct
    class A:
        b: tmp

    a = A(255)

    assert isinstance(a.b, uint32_t)
    assert a.b.value == 255

def test_invalid_wrong_values(BufferClass):
    with pytest.raises(TypeError):
        BufferClass('Noder', 15)

def test_valid_buffer(BufferClass):
    a = BufferClass(32, [97] * 32)

    for element in a.buf:
        assert element.value == 97

    assert isinstance(a.buf[0], uint8_t)

def test_invalid_length_buffer(BufferClass):
    with pytest.raises(MaxSizeExceededError):
        BufferClass(90, [100] * 90)

def test_valid_empty_buffer(BufferClass):
    a = BufferClass(5, [])

    for element in a.buf:
        assert element.value == 0

def test_invalid_buffer_overflow(BufferClass):
    with pytest.raises(MaxSizeExceededError):
        a = BufferClass(32, [67] * 32)
        a.buf.append(6)

def test_valid_nested_class(BufferClass, NestedClass):
    a = BufferClass(5, range(5))
    b = NestedClass(a, 0xdeadbeef)

    assert isinstance(b.buffer, BufferClass)
    assert b.buffer == a

def test_valid_class_duplicate_members(DuplicateClass):
    a = DuplicateClass(0xff)

    assert isinstance(a.magic, uint32_t)
    assert a.magic.value == 0xff

# TODO
@pytest.mark.skip(reason='Cant figure a way to pass it for now')
def test_valid_class_copy_ctor(BufferClass):
    a = BufferClass(5, range(5))
    b = deepcopy(a)

    b.size.value = 10

    assert a.size.value == 5
    assert b.size.value == 10

def test_valid_class_dynamic_buffer(DynamicClass):
    a = DynamicClass(5, [97] * 50)

    assert a.magic.value == 5
    for element in a.buf:
        assert element.value == 97

def test_valid_2_classes_are_different(DynamicClass, BufferClass):
    assert DynamicClass is not BufferClass

def test_valid_class_custom_init_implementation():
    @binary_struct
    class A:
        times_two: uint8_t

        def __init__(self, times_two):
            # TODO Unfortunately I can't find a better solution
            super(type(self), self).__init__(times_two * 2)

    a = A(5)

    assert a.times_two.value == 10

def test_valid_class_size(BufferClass, NestedClass):
    a = BufferClass(32, [97] * 32)
    b = NestedClass(a, 0xdeadbeef)

    assert a.size_in_bytes == 36
    assert b.size_in_bytes == 40

def test_valid_class_size_empty(EmptyClass):
    a = EmptyClass()

    assert a.size_in_bytes == 0

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

def test_valid_class_init_with_no_params(BufferClass):
    a = BufferClass()

    assert a.size.value == 0
    for element in a.buf:
        assert element.value == 0
    assert a.size_in_bytes == 36
