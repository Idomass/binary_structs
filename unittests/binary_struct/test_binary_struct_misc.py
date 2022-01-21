import pytest

from copy import deepcopy
from binary_structs.utils.binary_field.binary_field import uint32_t
from binary_structs.utils.buffers.binary_buffer import BinaryBuffer, MaxSizeExceededError
from binary_structs.utils.buffers.typed_buffer import TypedBuffer
from conftest import EmptyClass, empty_decorator, test_structs

from binary_structs import binary_struct, big_endian, little_endian, uint8_t


@pytest.mark.skip(reason='#TODO Cant figure a way to pass it for now')
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

# Equal tests
available_decorators = [empty_decorator, big_endian, little_endian]

test_params = []
for cls_params in test_structs:
    for decorator in available_decorators:
        test_params.append(tuple([decorator] + cls_params))


@pytest.mark.parametrize('decorator, cls, params', test_params)
def test_equal(decorator, cls, params):
    new_cls = decorator(cls)
    instance1 = new_cls(**params)
    instance2 = new_cls(**params)

    assert instance1 == instance2

@pytest.mark.parametrize('decorator, cls, params', test_params)
def test_inequal(decorator, cls, params):
    # Doesn't apply to empty class
    if cls is not EmptyClass:
        new_cls = decorator(cls)
        instance1 = new_cls(**params)
        instance2 = new_cls()

        assert instance1 != instance2

def test_invalid_equal_not_binary_struct(SimpleClassFixture):
    class A:
        def __init__(self):
            self.a = uint8_t(5)

    a = A()
    b = SimpleClassFixture(5)

    assert b != a

def test_invalid_equal_different_structs(InheritedClassFixture):
    @binary_struct
    class A(InheritedClassFixture):
        pass

    a = A(3, [0] * 9, 0xdead)
    b = InheritedClassFixture(3, [0] * 9, 0xdead)

    assert a != b

# __str__ tests
@pytest.mark.parametrize('cls, params', test_structs)
def test_string_conversion(cls, params):
    print()
    print(cls(**params))

# Assignment support
def test_valid_item_assignment_simple(SimpleClassFixture):
    a = SimpleClassFixture()

    a.a = 58
    assert isinstance(a.a, uint8_t)
    assert a.a == 58

def test_valid_item_assignment_dyn_buf(DynamicClassFixture):
    a = DynamicClassFixture()

    a.buf = range(9)
    assert isinstance(a.buf, TypedBuffer)
    assert a.buf == list(range(9))

def test_valid_item_assignment_dyn_buf_bytes(DynamicClassFixture):
    a = DynamicClassFixture()

    a.buf = bytes(range(17))
    assert isinstance(a.buf, TypedBuffer)
    assert a.buf == list(range(17))

def test_invalid_item_assignement_wrong_type(DynamicClassFixture):
    a = DynamicClassFixture()

    with pytest.raises(TypeError):
        a.buf = ['1', '2']

def test_valid_item_assignment_bin_buf(BufferClassFixture):
    a = BufferClassFixture()

    a.buf = range(5)
    assert isinstance(a.buf, BinaryBuffer)
    assert a.buf == list(range(5)) + [0] * 27

def test_invalid_item_assignment_bin_buf_too_big(BufferClassFixture):
    a = BufferClassFixture()

    with pytest.raises(MaxSizeExceededError):
        a.buf = range(99)

def test_valid_item_assignment_bin_buf_bytes(BufferClassFixture):
    a = BufferClassFixture()

    a.buf = bytes(range(29))
    assert isinstance(a.buf, BinaryBuffer)
    assert a.buf == list(range(29)) + [0] * 3

def test_invalid_item_assignment_bin_buf_bytes_too_big(BufferClassFixture):
    a = BufferClassFixture()

    with pytest.raises(MaxSizeExceededError):
        a.buf = bytes(range(99))
