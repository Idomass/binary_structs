import pytest

from binary_structs import *


# Initialization testing
def test_valid_class_empty():
    @big_endian
    @binary_struct
    class A():
        pass

def test_invalid_class_decorator():
    with pytest.raises(TypeError):
        @big_endian
        class A:
            pass

def test_valid_class_decorated_twice():
    @big_endian
    @little_endian
    @binary_struct
    class A:
        a: be_int16_t

    a = A(0xff)
    assert isinstance(a.a, be_int16_t)
    assert a.a.value == 0xff
    assert a.size_in_bytes == 2
    assert bytes(a) == b'\x00\xff'

def test_valid_class_simple_inhertience(BufferClassFixture):
    @big_endian
    @binary_struct
    class A(BufferClassFixture):
        magic: uint8_t
        magic2: be_uint8_t

    a = A(5, [1, 2, 3], 7, 9)
    assert isinstance(a.size, be_uint32_t)
    assert isinstance(a.buf[0], be_uint8_t)
    assert isinstance(a.magic, be_uint8_t)
    assert isinstance(a.magic2, be_uint8_t)
    assert a.size_in_bytes == 38

def test_valid_class_simple_inhertience_not_binary_struct(BufferClassFixture):
    with pytest.raises(TypeError):
        @big_endian
        class A(BufferClassFixture):
            magic: uint8_t

def test_valid_class_simple_inhertience_old_still_valid(BufferClassFixture):
    A = big_endian(BufferClassFixture)

    a = BufferClassFixture(5, [1, 2, 3])
    assert isinstance(a.size, uint32_t)
    assert isinstance(a.buf[0], uint8_t)

def test_valid_class_old_still_valid():
    @binary_struct
    class A:
        magic: uint32_t

    B = big_endian(A)

    a = A(5)
    assert isinstance(a.magic, uint32_t)

def test_valid_class_old_still_valid_nested():
    @binary_struct
    class A:
        magic: uint32_t

    @binary_struct
    class C:
        a: A

    D = big_endian(C)

    assert C.__annotations__['a'] is A

def test_valid_class_old_still_valid_inheritence():
    @binary_struct
    class A:
        magic: uint32_t
        a: uint32_t
        b: [uint8_t]
        c: [uint8_t, 32]

    @binary_struct
    class B(A):
        pass

    C = big_endian(B)

    assert B.__base__ is A
    assert A.a_type == uint32_t
    assert A.b_type == [uint8_t]
    assert A.c_type == [uint8_t, 32]

def test_valid_class_longer_inheritence_tree(BufferClassFixture):
    class A(BufferClassFixture):
        pass

    class B(A):
        pass

    @big_endian
    @binary_struct
    class C(B):
        pass

    assert C.__base__.__base__.__base__ is not BufferClassFixture

    a = C(5, [1, 2, 3])
    assert isinstance(a.size, be_uint32_t)
    assert isinstance(a.buf[0], be_uint8_t)

def test_valid_class_unrelated_inheritence_is_still_valid(BufferClassFixture):
    class A:
        pass

    @big_endian
    @binary_struct
    class B(BufferClassFixture, A):
        pass

    assert B.__bases__[1] is A

def test_valid_class_nested_class_default_value(NestedClassFixture):
    EndianClass = big_endian(NestedClassFixture)
    b = EndianClass(magic=0xdeadbeef)

    assert b.magic.value == 0xdeadbeef
    assert b.buffer.size.value == 0
    for element in b.buffer.buf:
        assert element.value == 0

def test_valid_class_nested_class(NestedClassFixture):
    EndianClass = big_endian(NestedClassFixture)
    a = EndianClass.buffer_type(32, [97] * 32)
    b = EndianClass(a, 0xdeadbeef)

    assert isinstance(b.buffer.size, be_uint32_t)
    assert isinstance(b.buffer.buf[0], be_uint8_t)
    assert isinstance(b.magic, be_uint32_t)
    assert b.size_in_bytes == a.size_in_bytes + 4

def test_valid_class_nested_twice(NestedClassFixture):
    EndianClass = big_endian(NestedClassFixture)

    @big_endian
    @binary_struct
    class A:
        nested: EndianClass

    a = A.nested_type.buffer_type(32, [97] * 32)
    b = A.nested_type(a, 0xdeadbeef)
    c = A(b)

    assert isinstance(c.nested.buffer.size, be_uint32_t)
    assert isinstance(c.nested.buffer.buf[0], be_uint8_t)
    assert isinstance(c.nested.magic, be_uint32_t)
    assert c.size_in_bytes == a.size_in_bytes + 4

def test_valid_attr_init(NestedClassFixture):
    EndianClass = big_endian(NestedClassFixture)

    a = EndianClass.buffer_type(5, range(3))
    b = EndianClass(a, 500)

    assert b.buffer == a

def test_valid_mixed_inheritence_chain(BufferClassFixture):
    class A(BufferClassFixture):
        bad: int

    @big_endian
    @binary_struct
    class B(A):
        bruh: uint32_t

    a = B(100, [])

    assert not hasattr(a, 'bad')
