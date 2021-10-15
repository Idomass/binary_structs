import pytest

from utils.binary_field import uint8_t
from binary_struct import binary_struct, _filter_valid_bases


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

def test_valid_class_init_with_inheritence(InheritedClassFixture):
    a = InheritedClassFixture(32, [97] * 32, 0xff)

    assert a.size == 32
    for element in a.buf:
        assert element.value == 97
    assert a.magic == 0xff
    assert a.size_in_bytes == 40

def test_valid_class_init_with_multiple_inheritence(MultipleInheritedClassFixture):
    a = MultipleInheritedClassFixture(32, [97] * 32, 5, 0xff)

    assert a.size == 32
    for element in a.buf:
        assert element.value == 97
    assert a.a == 5
    assert a.magic == 0xff
    assert a.foo()
    assert a.size_in_bytes == 41

def test_valid_class_with_multiple_inheritence_decorated_for_each(BufferClassFixture):
    @binary_struct
    class A(BufferClassFixture):
        magic: uint8_t

    @binary_struct
    class B(A):
        pass

    @binary_struct
    class C(B):
        pass

    a = C(32, [97] * 32, 3)

    assert a.size.value == 32
    for element in a.buf:
        assert element.value == 97
    assert a.magic.value == 3
    assert a.size_in_bytes == 37

def test_invalid_class_inherited_name_conflict(BufferClassFixture, DynamicClassFixture):
    with pytest.raises(SyntaxError):
        @binary_struct
        class A(BufferClassFixture, DynamicClassFixture):
            pass

def test_valid_inheritenece_does_not_duplicate_bases(InheritedClassFixture, BufferClassFixture):
    assert BufferClassFixture not in InheritedClassFixture.__bases__
