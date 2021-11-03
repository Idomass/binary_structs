import pytest

from utils.binary_field import uint16_t, uint32_t, uint64_t, uint8_t
from binary_struct import binary_struct, _filter_valid_bases


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

def test_valid_inheritence_non_binary_struct(BufferClassFixture):
    class A(BufferClassFixture):
        pass

    a = A(5, range(3))
    b = BufferClassFixture(5, range(3))

    assert a.size == b.size
    assert a.buf == b.buf

def test_valid_inheritence_mixed_chain(BufferClassFixture):
    class NotABase(BufferClassFixture):
        bad: int

    @binary_struct
    class B(NotABase):
        magic: uint32_t

    b = B(5, [0], 11)

    assert b.magic.value == 11
    assert b.size.value == 5
    assert b.buf == [0] * 32
    assert b.size_in_bytes == 40
    assert not hasattr(b, 'bad')

def test_valid_inheritence_binary_struct_on_top():
    class A:
        bad: int

    @binary_struct
    class B(A):
        real: uint32_t

    b = B(5)
    assert b.real.value == 5
    assert not hasattr(b, 'bad')

def test_valid_inheritence_different_chains(BufferClassFixture):
    class C:
        bad: uint16_t

    @binary_struct
    class A(BufferClassFixture, C):
        magic: uint64_t

    a = A(5, [1, 2], 99)
    assert not hasattr(a, 'bad')
