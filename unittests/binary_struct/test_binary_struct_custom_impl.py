import pytest

from binary_structs import binary_struct, uint8_t
from conftest import available_decorators


decorators_without_format = [decorator[0] for decorator in available_decorators]

# Fixture
@pytest.fixture
def CustomInitClsFixture():
    @binary_struct
    class CustomInitCls:
        a: uint8_t

        def __init__(self, a, b) -> None:
            pass

    return CustomInitCls


# Tests
def test_valid_class_custom_fn_implementation_multiple_inheritance():
    class B:
        def foo(self):
            return True

    class C:
        def bar(self):
            return True

    @binary_struct
    class A(B, C):
        pass

    a = A()
    assert a.foo()
    assert a.bar()


@pytest.mark.parametrize('decorator', decorators_without_format)
def test_valid_class_custom_implementation_init(decorator):
    @binary_struct
    class TimesTwo:
        times_two: uint8_t

        def __init__(self, times_two):
            self._bs_init(times_two * 2)

    cls = decorator(TimesTwo)
    a = cls(5)

    assert a.times_two.value == 10

@pytest.mark.parametrize('decorator', decorators_without_format)
def test_valid_class_custom_implementation_init_with_inheritance(decorator):
    @binary_struct
    class A:
        a: uint8_t

    @binary_struct
    class B(A):
        b: uint8_t

        def __init__(self, a, b):
            a *= 5
            b *= 3
            self._bs_init(a, b)

    cls = decorator(B)
    b = cls(9, b=16)

    assert b.a.value == 45
    assert b.b.value == 48


@pytest.mark.parametrize('decorator', decorators_without_format)
def test_valid_class_custom_implementation_init_with_multiple_inheritance(decorator):
    @binary_struct
    class A:
        a: uint8_t

    @binary_struct
    class B:
        b: uint8_t

    @binary_struct
    class C(A, B):
        c: [uint8_t]

        def __init__(self, a, b):
            self._bs_init(a, b, range(3))

    cls = decorator(C)
    c = cls(5, 0xff)

    assert c.a.value == 5
    assert c.b.value == 0xff
    assert c.c == list(range(3))


@pytest.mark.parametrize('decorator', decorators_without_format)
def test_valid_class_multiple_inheritance_custom_implementation(decorator):
    @binary_struct
    class A:
        a: uint8_t = 0xff

        def __bytes__(self):
            return b'A' + A._bs_bytes(self)

    class B:
        def __bytes__(self):
            return b'B'

    @binary_struct
    class C(B, A):
        c: uint8_t = 0

        def __bytes__(self):
            return b'C' + C._bs_bytes(self)

    cls = decorator(C)

    assert bytes(cls()) == b'CBA\xff\x00'


@pytest.mark.parametrize('decorator', decorators_without_format)
def test_valid_class_custom_implementation_size_property(decorator):
    @binary_struct
    class A:
        a: [uint8_t]

        @property
        def size_in_bytes(self):
            return 5 + self._bs_size()

    cls = decorator(A)
    a = cls(range(7))

    assert a.size_in_bytes == 12


@pytest.mark.parametrize('decorator', decorators_without_format)
def test_valid_class_mixed_chain(decorator):
    @binary_struct
    class A:
        a: uint8_t

    class B(A):
        # This is not a binary structs, its init will be skipped
        def __init__(self):
            assert False

    @binary_struct
    class C(B):
        b: uint8_t

    cls = decorator(C)
    c = cls(1, 2)

    assert c.a.value == 1
    assert c.b.value == 2


@pytest.mark.parametrize('decorator', decorators_without_format)
def test_valid_class_custom_init_deserialize_inherited(decorator, CustomInitClsFixture):
    @binary_struct
    class B(CustomInitClsFixture):
        b: uint8_t

    cls = decorator(B)
    cls.deserialize(b'XD')


@pytest.mark.parametrize('decorator', decorators_without_format)
def test_valid_class_custom_init_deserialize_nested(decorator, CustomInitClsFixture):
    @binary_struct
    class B:
        a: CustomInitClsFixture
        b: uint8_t

    cls = decorator(B)
    cls.deserialize(b'XD')
