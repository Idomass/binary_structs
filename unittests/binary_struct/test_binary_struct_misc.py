import pytest

from copy import deepcopy
from conftest import EmptyClass, empty_decorator, test_structs

from binary_structs import binary_struct, big_endian, little_endian,    \
                           le_uint8_t, le_uint8_t, le_uint32_t,         \
                           be_uint8_t, be_uint32_t


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
            self.a = le_uint8_t(5)

    a = A()
    b = SimpleClassFixture(5)

    assert b != a

def test_valid_equal_different_structs(InheritedClassFixture):
    @binary_struct
    class A(InheritedClassFixture):
        pass

    a = A(3, [0] * 9, 0xdead)
    b = InheritedClassFixture(3, [0] * 9, 0xdead)

    assert a == b

# __str__ tests
@pytest.mark.parametrize('cls, params', test_structs)
def test_string_conversion(cls, params):
    print()
    print(cls(**params))

# Assignment support
def test_valid_item_assignment_simple(SimpleClassFixture):
    a = SimpleClassFixture()

    a.a = 58
    assert isinstance(a.a, le_uint8_t)
    assert a.a == 58

def test_invalid_item_assignement_wrong_type(DynamicClassFixture):
    a = DynamicClassFixture(buf=[1, 2])

    with pytest.raises(TypeError):
        a.buf = ['1', '2']

def test_valid_item_assignment_bin_buf(BufferClassFixture):
    a = BufferClassFixture()

    a.buf = range(5)
    assert a.buf == list(range(5)) + [0] * 27

def test_invalid_item_assignment_bin_buf_too_big(BufferClassFixture):
    a = BufferClassFixture()

    with pytest.raises(IndexError):
        a.buf = range(99)

def test_valid_item_assignment_bin_buf_bytes(BufferClassFixture):
    a = BufferClassFixture()

    a.buf = bytes(range(29))
    assert a.buf == list(range(29)) + [0] * 3

def test_invalid_item_assignment_bin_buf_bytes_too_big(BufferClassFixture):
    a = BufferClassFixture()

    with pytest.raises(IndexError):
        a.buf = bytes(range(99))

def test_valid_item_assignment_nested(NestedClassFixture):
    a = NestedClassFixture()

    a.buffer = NestedClassFixture.buffer_type(5, range(16))
    assert isinstance(a.buffer, NestedClassFixture.buffer_type)

    assert a.buffer.size == 5
    assert a.buffer.buf == list(range(16)) + [0] * 16

def test_valid_item_assignment_nested_args(NestedClassFixture):
    a = NestedClassFixture()

    a.buffer = [0xde, range(12)]
    assert isinstance(a.buffer, NestedClassFixture.buffer_type)

    assert a.buffer.size == 0xde
    assert a.buffer.buf == list(range(12)) + [0] * 20

def test_invalid_item_assignment_nested_args(NestedClassFixture):
    a = NestedClassFixture()

    with pytest.raises(TypeError):
        a.buffer = [1, 2]

def test_valid_item_assignment_nested_kwargs(NestedClassFixture):
    a = NestedClassFixture()

    a.buffer = {'buf': b'AAAA'}
    assert isinstance(a.buffer, NestedClassFixture.buffer_type)

    assert a.buffer.size == 0
    assert a.buffer.buf == [0x41] * 4 + [0] * 28

def test_invalid_item_assignment_nested_kwargs(NestedClassFixture):
    a = NestedClassFixture()

    with pytest.raises(TypeError):
        a.buffer = {'bad': 32}


def test_valid_dict_conversion_simple(SimpleClassFixture):
    assert dict(SimpleClassFixture(a=7)) == {'a': le_uint8_t(7)}


def test_valid_dict_conversion_nested(NestedClassFixture, BufferClassFixture):
    nested = NestedClassFixture(buffer=[5, range(3)], magic=42)

    assert dict(nested) == {'buffer': BufferClassFixture(5, range(3)), 'magic': le_uint32_t(42)}


def test_valid_dict_conversion_inheritence(InheritedClassFixture):
    inherited = InheritedClassFixture(5, range(7), 9)

    assert dict(inherited) == {'size': le_uint32_t(5), 'buf': list(range(7)) + [0] * 25, 'magic': le_uint32_t(9)}


def test_valid_dict_conversion_simple_big(SimpleClassFixture):
    assert dict(big_endian(SimpleClassFixture)(a=7)) == {'a': be_uint8_t(7)}


def test_valid_dict_conversion_nested_big(NestedClassFixture, BufferClassFixture):
    nested = big_endian(NestedClassFixture)(buffer=[5, range(3)], magic=42)

    assert dict(nested) == {'buffer': big_endian(BufferClassFixture)(5, range(3)), 'magic': be_uint32_t(42)}


def test_valid_dict_conversion_inheritence_big(InheritedClassFixture):
    inherited = big_endian(InheritedClassFixture)(5, range(7), 9)

    assert dict(inherited) == {'size': be_uint32_t(5), 'buf': list(range(7)) + [0] * 25, 'magic': be_uint32_t(9)}


def test_valid_class_static_size(SimpleClassFixture):
    assert SimpleClassFixture.static_size == 1


def test_valid_class_static_size_dynamic(DynamicClassFixture):
    assert DynamicClassFixture.static_size == 1


def test_valid_class_static_size_inherited(InheritedClassFixture):
    assert InheritedClassFixture.static_size == 40


def test_valid_class_static_size_nested(NestedClassFixture):
    assert NestedClassFixture.static_size == 40


# Bugs
def test_valid_class_type_name_same_as_annotation(BufferClassFixture):
    @binary_struct
    class A:
        BufferClass: BufferClassFixture

    A()


def test_valid_class_2_buffers_dynamics_types_not_corrupted():
    @binary_struct
    class A:
        buf1: [le_uint8_t]
        buf2: [le_uint32_t]

    assert A.buf1_type.element_type is le_uint8_t
    assert A.buf2_type.element_type is le_uint32_t


def test_valid_class_2_buffers_dynamics_are_different():
    @binary_struct
    class A:
        buf1: [le_uint8_t]
        buf2: [le_uint32_t]

    a = A()

    assert a.buf1 is not a.buf2


def test_valid_class_2_binary_buffers_sizes_and_types_not_corrupted():
    @binary_struct
    class A:
        buf1: [le_uint8_t, 32]
        buf2: [le_uint32_t, 16]

    a = A()

    assert A.buf1_type.element_type is le_uint8_t
    assert A.buf2_type.element_type is le_uint32_t
    assert len(a.buf1) == 32
    assert len(a.buf2) == 16


def test_valid_dynamic_class_type_helper_updates(DynamicClassFixture):
    arr1 = DynamicClassFixture()
    assert isinstance(arr1.buf, arr1.buf_type)

    arr2 = DynamicClassFixture(buf=[1, 2, 3])
    assert isinstance(arr2.buf, arr2.buf_type)

    assert arr2.buf != arr1.buf
    assert arr1.buf_type is not arr2.buf_type
