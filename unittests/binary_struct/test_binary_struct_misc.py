import pytest

from copy import deepcopy
from conftest import EmptyClass, empty_decorator, test_structs

from utils.binary_field import uint8_t
from binary_struct import binary_struct
from endianness import big_endian, little_endian


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
