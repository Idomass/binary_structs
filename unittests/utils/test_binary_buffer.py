import pytest

from utils.binary_field import uint32_t, uint8_t
from utils.buffers.binary_buffer import BinaryBuffer, MaxSizeExceededError


def test_valid_init():
    a = BinaryBuffer(uint32_t, 50, list(range(3)))

    for element, expected_element in zip(a, list(range(3))):
        assert element.value == expected_element

    for element in a[3:]:
        assert element.value == 0

def test_invalid_init():
    with pytest.raises(MaxSizeExceededError):
        BinaryBuffer(uint32_t, 3, range(4))

def test_invalid_append():
    a = BinaryBuffer(uint32_t, 4)

    with pytest.raises(MaxSizeExceededError):
        a.append(5)

def test_invalid_extend():
    a = BinaryBuffer(uint8_t, 2)

    with pytest.raises(MaxSizeExceededError):
        a.extend([1, 2, 3])

def test_invalid_insert():
    a = BinaryBuffer(uint32_t, 2, [5, 6])

    with pytest.raises(MaxSizeExceededError):
        a.insert(1, 7)

    with pytest.raises(MaxSizeExceededError):
        a.insert(4, 7)

def test_invalid_iadd():
    a = BinaryBuffer(uint32_t, 3, range(2))

    with pytest.raises(MaxSizeExceededError):
        a += [1, 2]

def test_invalid_imul():
    a = BinaryBuffer(uint32_t, 4, [1, 2])

    with pytest.raises(MaxSizeExceededError):
        a *= 3

def test_valid_item_assignment():
    a = BinaryBuffer(uint8_t, 10, [0x41] * 10)

    a[0] = 0x0
    assert a[0].value == 0

def test_valid_serialization():
    a = BinaryBuffer(uint8_t, 10, [0x41] * 10)

    assert bytes(a) == b'A' * 10

def test_valid_serialization_not_full():
    a = BinaryBuffer(uint8_t, 15, [0x41] * 10)

    assert bytes(a) == b'A' * 10 + b'\x00' * 5

def test_valid_serialization_empty():
    a = BinaryBuffer(uint32_t, 0)

    assert bytes(a) == b''

def test_valid_size():
    a = BinaryBuffer(uint8_t, 10)

    assert a.size_in_bytes == 10

def test_valid_size_empty():
    a = BinaryBuffer(uint8_t, 0)

    assert a.size_in_bytes == 0

def test_valid_clear():
    a = BinaryBuffer(uint8_t, 10, [0x41] * 10)

    a.clear()
    assert a.size_in_bytes == 10
    for element in a:
        assert element.value == 0

def test_invalid_remove():
    with pytest.raises(ValueError):
        BinaryBuffer(uint8_t, 10, [0x41] * 10).remove(0x41)

def test_valid_deserialization_empty():
    a = BinaryBuffer(uint8_t, 0).deserialize(b'')

    assert a.size_in_bytes == 0

def test_valid_deserialization_non_empty():
    a = BinaryBuffer(uint8_t, 4).deserialize(b'\xff' * 4)

    assert a.size_in_bytes == 4
    for element in a:
        assert element.value == 0xff

def test_valid_deserialization_buffer_too_big():
    a = BinaryBuffer(uint8_t, 8).deserialize(b'\xde' * 10)

    assert a.size_in_bytes == 8
    for element in a:
        assert element.value == 0xde

def test_invalid_deserialization_buffer_too_small():
    with pytest.raises(ValueError):
        BinaryBuffer(uint8_t, 4).deserialize(b'\xff' * 2)
