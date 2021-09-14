import pytest

from binary_struct import binary_struct
from utils.binary_field import uint8_t


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

def test_valid_class_nested_and_inherited(InheritedAndNestedClassFixture, BufferClassFixture):
    a = BufferClassFixture(32, [97] * 32)
    b = BufferClassFixture(16, [0x41] * 16)
    c = InheritedAndNestedClassFixture(a, 0xdeadbeef, b)

    assert c.magic.value == 0xdeadbeef
    assert c.buffer.size == 32
    assert c.buffer.buf == a.buf

    assert c.buf2.size == 16
    assert c.buf2.buf == b.buf

def test_valid_class_init_with_monster_class(MonsterClassFixture, DynamicClassFixture, BufferClassFixture, EmptyClassFixture):
    a = BufferClassFixture(3, [1, 2, 3])
    b = DynamicClassFixture(0xdeadbeef, [1])
    c = EmptyClassFixture()

    monster = MonsterClassFixture(a, 0xcafebabe, 32, b, c, 0xff)

    assert monster.size_in_bytes == a.size_in_bytes + b.size_in_bytes + c.size_in_bytes \
                                    + 4 + 1 + 1

def test_valid_class_init_with_kwargs(MonsterClassFixture, DynamicClassFixture):
    dynamic = DynamicClassFixture(5, [1, 2, 3])
    a = MonsterClassFixture(magic2=90)
    b = MonsterClassFixture(dynamic=dynamic)

    assert a.magic2 == 90
    assert b.dynamic is dynamic
