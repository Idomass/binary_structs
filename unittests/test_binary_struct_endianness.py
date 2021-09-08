import pytest
import struct

from binary_struct import binary_struct
from endianness import big_endian, little_endian
from utils.binary_field import *


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
    assert a.size_in_bytes == 38

def test_valid_class_simple_inhertience_not_binary_struct(BufferClass):
    @big_endian
    class A(BufferClass):
        magic: uint8_t
        magic2: be_uint8_t

    a = A(5, [1, 2, 3])
    assert isinstance(a.size, be_uint32_t)
    assert isinstance(a.buf[0], be_uint8_t)
    assert not hasattr(a, 'magic')
    assert a.size_in_bytes == 36

def test_valid_class_simple_inhertience_old_still_valid(BufferClass):
    @big_endian
    @binary_struct
    class A(BufferClass):
        magic: uint8_t

    a = BufferClass(5, [1, 2, 3])
    assert isinstance(a.size, uint32_t)
    assert isinstance(a.buf[0], uint8_t)

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

def test_valid_class_nested_class(BENestedClass):
    # TODO, is there a better solution?
    a = BENestedClass.__annotations__['buffer'](32, [97] * 32)
    b = BENestedClass(a, 0xdeadbeef)

    assert isinstance(b.buffer.size, be_uint32_t)
    assert isinstance(b.buffer.buf[0], be_uint8_t)
    assert isinstance(b.magic, be_uint32_t)
    assert b.size_in_bytes == a.size_in_bytes + 4

# Serialization and Deserialization Tests
def test_valid_serialization_simple(BEBufferClass):
    a = BEBufferClass(20, [0x41] * 32)

    assert bytes(a) == struct.pack('>I32s', 20, b'A' * 32)

def test_valid_serialization_simple_inheritence(BufferClass):
    @big_endian
    @binary_struct
    class A(BufferClass):
        magic: uint64_t

    a = A(5, [1, 2, 3], 0xdeadbeef)

    assert bytes(a) == struct.pack('>I32sQ', 5, b'\x01\x02\x03' + b'\x00' * 29, 0xdeadbeef)
