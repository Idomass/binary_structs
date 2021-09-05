import pytest

from utils.binary_field import BinaryField, uint32_t, uint8_t
from buffers.binary_buffer import BinaryBuffer, MaxSizeExceededError


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
