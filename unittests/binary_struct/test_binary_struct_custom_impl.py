import pytest

from utils.binary_field import uint8_t
from binary_struct import binary_struct
from conftest import available_decorators


decorators_without_format = [decorator[0] for decorator in available_decorators]

def test_valid_class_custom_fn_implementation_multiple_inheritence():
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
            self.TimesTwo__init__(times_two * 2)

    cls = decorator(TimesTwo)
    a = cls(5)

    assert a.times_two.value == 10

@pytest.mark.parametrize('decorator', decorators_without_format)
def test_valid_class_custom_implementation_init_with_inheritence(decorator):
    @binary_struct
    class A:
        a: uint8_t

        def __init__(self, a, msg1, msg2 = 5):
            self.A__init__(a)
            self.msg1 = msg1
            self.msg2 = msg2

    @binary_struct
    class B(A):
        b: uint8_t

    cls = decorator(B)
    b = cls(9, "Hello", b=16)

    assert b.msg1 == "Hello"
    assert b.msg2 == 5
    assert b.a.value == 9
    assert b.b.value == 16

@pytest.mark.parametrize('decorator', decorators_without_format)
def test_valid_class_custom_implementation_init_with_multiple_inheritence(decorator):
    @binary_struct
    class A:
        a: uint8_t

        def __init__(self, a, msg1):
            self.A__init__(a)
            self.msg1 = msg1

    @binary_struct
    class B:
        b: uint8_t

        def __init__(self, b, msg2 = 5):
            self.B__init__(b)
            self.msg2 = msg2

    @binary_struct
    class C(A, B):
        c: [uint8_t]

        def __init__(self, a, msg1, b, msg2, msg3):
            self.C__init__(a, msg1, b, msg2, range(3))
            self.msg3 = msg3

    cls = decorator(C)
    c = cls(5, "Hi", 0xff, "No", "Ok")

    assert c.a.value == 5
    assert c.b.value == 0xff
    assert c.c == list(range(3))
    assert c.msg1 == "Hi"
    assert c.msg2 == "No"
    assert c.msg3 == "Ok"

@pytest.mark.parametrize('decorator', decorators_without_format)
def test_valid_class_inheritence_custom_implementation(BufferClassFixture, decorator):
    @binary_struct
    class BiggerBuffer(BufferClassFixture):
        def __init__(self, size, buffer):
            self.BiggerBuffer__init__(size * 2, buffer * 2)

    cls = decorator(BiggerBuffer)
    a = cls(5, list(range(3)))

    assert a.size.value == 10
    assert a.buf == list(range(3)) * 2 + [0] * 26

@pytest.mark.parametrize('decorator', decorators_without_format)
def test_valid_class_multiple_inheritence_custom_implementation(decorator):
    @binary_struct
    class A:
        a: uint8_t = 0xff

        def __bytes__(self):
            return b'A' + self.A__bytes__()

    class B:
        def __bytes__(self):
            return b'B'

    @binary_struct
    class C(B, A):
        c: uint8_t = 0

        def __bytes__(self):
            return b'C' + self.C__bytes__() + super(type(self), self).__bytes__()

    cls = decorator(C)

    assert bytes(cls()) == b'CA\xff\x00B'

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
