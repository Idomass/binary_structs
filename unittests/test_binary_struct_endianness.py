import pytest
import struct

from binary_struct import binary_struct
from endianness import big_endian, little_endian
from utils.binary_field import *


def test_valid_class_with_endian_empty():
    @big_endian
    @binary_struct
    class A():
        pass

def test_invalid_class_with_endian_decorator():
    with pytest.raises(TypeError):
        @big_endian
        class A:
            pass

def test_valid_class_with_endian_simple_inhertience(BufferClass):
    @big_endian
    class A(BufferClass):
        magic: uint8_t
        magic2: be_uint8_t

    a = A(5, [1, 2, 3], 7, 9)
    assert isinstance(a.size, be_uint32_t)
    assert isinstance(a.buf[0], be_uint8_t)
    assert isinstance(a.magic, be_uint8_t)
    assert a.size_in_bytes == 38

def test_valid_class_with_endian_simple_inhertience_old_still_valid(BufferClass):
    @big_endian
    class A(BufferClass):
        magic: uint8_t

    a = BufferClass(5, [1, 2, 3])
    assert isinstance(a.size, uint32_t)
    assert isinstance(a.buf[0], uint8_t)

def test_valid_serialization_simple_big_endian(BEBufferClass):
    a = BEBufferClass(20, [0x41] * 32)

    assert bytes(a) == struct.pack('>I32s', 20, b'A' * 32)
