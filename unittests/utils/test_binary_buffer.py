import pytest

from os import urandom

from binary_structs.utils import *

binary_fields = [le_uint8_t, le_uint16_t, le_uint32_t, le_uint64_t,
                 le_int8_t, le_int16_t, le_int32_t, le_int64_t,
                 be_uint8_t, be_uint16_t, be_uint32_t, be_uint64_t,
                 be_int8_t, be_int16_t, be_int32_t, be_int64_t]


def test_valid_init():
    buf_type = new_binary_buffer(uint32_t, 50)
    arr = buf_type(*range(3))

    assert arr == [0, 1, 2] + [0] * 47


def test_invalid_init():
    with pytest.raises(IndexError):
        new_binary_buffer(uint32_t, 3)(*range(4))


def test_invalid_iadd():
    a = new_binary_buffer(uint32_t, 3)(*range(2))

    with pytest.raises(TypeError):
        a += [1, 2]


def test_invalid_imul():
    a = new_binary_buffer(uint32_t, 4)(*[1, 2])

    with pytest.raises(TypeError):
        a *= 3


def test_valid_item_assignment():
    a = new_binary_buffer(uint8_t, 10)(*[0x41] * 10)

    a[0] = 0x0
    assert a[0].value == 0


def test_valid_slicing():
    bin_buf = new_binary_buffer(uint32_t, 50)(*range(3))
    sub_buf = bin_buf[:]

    assert sub_buf is not bin_buf
    assert isinstance(sub_buf, type(bin_buf))
    assert sub_buf == bin_buf


def test_valid_slicing_empty():
    bin_buf = new_binary_buffer(uint32_t, 50)(*range(42))
    sub_buf = bin_buf[1000:]

    assert sub_buf == []


def test_valid_serialization():
    a = new_binary_buffer(uint8_t, 10)(*[0x41] * 10)

    assert bytes(a) == b'A' * 10


def test_valid_serialization_not_full():
    a = new_binary_buffer(uint8_t, 15)(*[0x41] * 10)

    assert bytes(a) == b'A' * 10 + b'\x00' * 5


def test_valid_serialization_empty():
    a = new_binary_buffer(uint32_t, 0)()

    assert bytes(a) == b''


def test_valid_size():
    a = new_binary_buffer(uint8_t, 10)()

    assert a.size_in_bytes == 10


def test_valid_size_empty():
    a = new_binary_buffer(uint8_t, 0)()

    assert a.size_in_bytes == 0


def test_valid_clear():
    a = new_binary_buffer(uint8_t, 10)(*[0x41] * 10)

    with pytest.raises(AttributeError):
        a.clear()


def test_invalid_remove():
    with pytest.raises(AttributeError):
        new_binary_buffer(uint8_t, 10)(*[0x41] * 10).remove(0x41)


def test_valid_deserialization_empty():
    a = new_binary_buffer(uint8_t, 0).deserialize(bytearray(b''))

    assert a.size_in_bytes == 0


def test_valid_deserialization_non_empty():
    a = new_binary_buffer(uint8_t, 4).deserialize(bytearray(b'\xff' * 4))

    assert a.size_in_bytes == 4
    assert a == [0xff] * 4


def test_valid_deserialization_buffer_too_big():
    a = new_binary_buffer(uint8_t, 8).deserialize(bytearray(b'\xde' * 10))

    assert a.size_in_bytes == 8
    assert a == [0xde] * 8


def test_invalid_deserialization_buffer_too_small():
    with pytest.raises(ValueError):
        new_binary_buffer(uint8_t, 4).deserialize(bytearray(b'\xff' * 2))


# Conversions
from_bytes_arr = [(field, urandom(field.static_size * 5)) for field in binary_fields]
from_bytes_arr += [(field, b'') for field in binary_fields]


@pytest.mark.parametrize('underlying_type, buf', from_bytes_arr)
def test_valid_deserialize(underlying_type, buf):
    size = len(buf) // underlying_type.static_size
    a = new_binary_buffer(underlying_type, size).deserialize(bytearray(buf))

    assert isinstance(a, new_binary_buffer(underlying_type, size))
    assert bytes(a) == buf


from_bytes_arr = [(field, urandom((field.static_size * 5) + 1)) for field in binary_fields if field.static_size != 1]
@pytest.mark.parametrize('underlying_type, buf', from_bytes_arr)
def test_valid_deserialize_ignore_suffix(underlying_type, buf):
    size = len(buf) // underlying_type.static_size
    arr = new_binary_buffer(underlying_type, size).deserialize(bytearray(buf))

    assert bytes(arr) == buf[:-1]
