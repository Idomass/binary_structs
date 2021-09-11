import pytest
import struct

from utils.binary_field import *
from binary_struct import binary_struct
from endianness import Endianness, big_endian, little_endian


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

def test_valid_class_simple_inhertience(BufferClass):
    @big_endian
    @binary_struct
    class A(BufferClass):
        magic: uint8_t
        magic2: be_uint8_t

    a = A(5, [1, 2, 3], 7, 9)
    assert isinstance(a.size, be_uint32_t)
    assert isinstance(a.buf[0], be_uint8_t)
    assert isinstance(a.magic, be_uint8_t)
    assert isinstance(a.magic2, be_uint8_t)
    assert a.size_in_bytes == 38

def test_valid_class_simple_inhertience_not_binary_struct(BufferClass):
    @big_endian
    class A(BufferClass):
        magic: uint8_t

    a = A(5, [1, 2, 3])
    assert isinstance(a.size, be_uint32_t)
    assert isinstance(a.buf[0], be_uint8_t)
    assert not hasattr(a, 'magic')
    assert a.size_in_bytes == 36

def test_valid_class_simple_inhertience_old_still_valid(BufferClass):
    A = big_endian(BufferClass)

    a = BufferClass(5, [1, 2, 3])
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

    @binary_struct
    class C(A):
        pass

    D = big_endian(C)

    assert C.__bases__[0].__bases__[0] is A

def test_valid_class_longer_inheritence_tree(BufferClass):
    class A(BufferClass):
        pass

    class B(A):
        pass

    @big_endian
    class C(B):
        pass

    a = C(5, [1, 2, 3])
    assert isinstance(a.size, uint32_t)
    assert isinstance(a.buf[0], uint8_t)

def test_valid_class_unrelated_inheritence_is_still_valid(BufferClass):
    class A:
        pass

    @big_endian
    @binary_struct
    class B(BufferClass, A):
        pass

    assert B.__bases__[1] is A

def test_valid_class_nested_class_default_value(NestedClass):
    EndianClass = big_endian(NestedClass)
    b = EndianClass(magic=0xdeadbeef)

    assert b.magic.value == 0xdeadbeef
    assert b.buffer.size.value == 0
    for element in b.buffer.buf:
        assert element.value == 0

def test_valid_class_nested_class(NestedClass):
    EndianClass = big_endian(NestedClass)
    a = EndianClass.buffer(32, [97] * 32)
    b = EndianClass(a, 0xdeadbeef)

    assert isinstance(b.buffer.size, be_uint32_t)
    assert isinstance(b.buffer.buf[0], be_uint8_t)
    assert isinstance(b.magic, be_uint32_t)
    assert b.size_in_bytes == a.size_in_bytes + 4

def test_valid_class_nested_twice(NestedClass):
    EndianClass = big_endian(NestedClass)

    @big_endian
    @binary_struct
    class A:
        nested: EndianClass

    a = A.nested.buffer(32, [97] * 32)
    b = A.nested(a, 0xdeadbeef)
    c = A(b)

    assert isinstance(c.nested.buffer.size, be_uint32_t)
    assert isinstance(c.nested.buffer.buf[0], be_uint8_t)
    assert isinstance(c.nested.magic, be_uint32_t)
    assert c.size_in_bytes == a.size_in_bytes + 4

# Serialization and Deserialization Tests
@pytest.mark.parametrize('decorator, format', [(big_endian, '>'), (little_endian, '<')])
def test_valid_serialization_simple(BufferClass, decorator, format):
    EndianClass = decorator(BufferClass)
    a = EndianClass(20, [0x41] * 32)

    assert bytes(a) == struct.pack(f'{format}I32s', 20, b'A' * 32)

@pytest.mark.parametrize('decorator, format', [(big_endian, '>'), (little_endian, '<')])
def test_valid_serialization_simple_inheritence(BufferClass, decorator, format):
    @binary_struct
    class A(BufferClass):
        magic: uint64_t

    EndianClass = decorator(A)
    a = EndianClass(5, [1, 2, 3], 0xdeadbeef)

    assert bytes(a) == struct.pack(f'{format}I32sQ', 5, b'\x01\x02\x03' + b'\x00' * 29, 0xdeadbeef)

@pytest.mark.parametrize('decorator, format', [(big_endian, '>'), (little_endian, '<')])
def test_valid_serialization_nested_class(NestedClass, decorator, format):
    EndianClass = decorator(NestedClass)
    a = EndianClass.buffer(32, [97] * 32)
    b = EndianClass(a, 0xdeadbeef)

    assert bytes(b) == struct.pack(f'{format}I32sI', 32, b'a' * 32, 0xdeadbeef)

@pytest.mark.parametrize('decorator, format', [(big_endian, '>'), (little_endian, '<')])
def test_valid_serialization_with_multiple_inheritence(MultipleInheritedClass, decorator, format):
    EndianClass = decorator(MultipleInheritedClass)
    a = EndianClass(32, [97] * 32, 5, 0xff)

    assert bytes(a) == struct.pack(f'{format}I32sBI', 32,  b'a' * 32, 5, 0xff)

@pytest.mark.parametrize('decorator, format', [(big_endian, '>'), (little_endian, '<')])
def test_valid_serialization_nested_class_default_value(NestedClass, decorator, format):
    EndianClass = decorator(NestedClass)
    b = EndianClass(magic=0xdeadbeef)

    assert bytes(b) == struct.pack(f'{format}I32sI', 0, b'\x00' * 32, 0xdeadbeef)

@pytest.mark.parametrize('decorator, format', [(big_endian, '>'), (little_endian, '<')])
def test_valid_serialization_nested_and_inherited(InheritedAndNestedClass, decorator, format):
    EndianClass = decorator(InheritedAndNestedClass)
    a = EndianClass.buffer(32, [97] * 32)
    b = EndianClass.buf2(16, [0x41] * 16)
    c = EndianClass(a, 0xdeadbeef, b)

    assert bytes(c) == struct.pack(f'{format}I32sII32s', 32,  b'a' * 32, 0xdeadbeef,
                                   16,  b'A' * 16 + b'\x00' * 16)

@pytest.mark.parametrize('decorator, format', [(big_endian, '>'), (little_endian, '<')])
def test_valid_serialization_monster_class(MonsterClass, decorator, format):
    EndianClass = decorator(MonsterClass)
    a = EndianClass.buffer(3, [1, 2, 3])
    b = EndianClass.dynamic(0x7f, [1])
    c = EndianClass.empty()

    monster = EndianClass(a, 0xcafebabe, 32, b, c, 0xff)

    assert bytes(monster) == struct.pack(f'{format}I32sIBBBB', 3, b'\x01\x02\x03' + b'\x00', 0xcafebabe,
                                         32, 0x7f, 1, 0xff)
