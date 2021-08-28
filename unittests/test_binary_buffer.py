import pytest
import ctypes

import logging

from buffers.binary_buffer import BinaryBuffer, MaxSizeExceededError


def test_valid_init():
    a = BinaryBuffer(ctypes.c_uint, 50, list(range(3)))

    for element, expected_element in zip(a, list(range(3))):
        assert element.value == expected_element

    for element in a[3:]:
        assert element.value == 0

def test_invalid_init():
    with pytest.raises(MaxSizeExceededError):
        BinaryBuffer(ctypes.c_uint, 3, range(4))

def test_invalid_append():
    a = BinaryBuffer(ctypes.c_uint, 4)

    with pytest.raises(MaxSizeExceededError):
        a.append(5)

def test_invalid_extend():
    a = BinaryBuffer(str, 2)

    with pytest.raises(MaxSizeExceededError):
        a.extend(['Noder', 'Neder', 'Nadir'])

def test_invalid_insert():
    a = BinaryBuffer(str, 2, ['Hi', 'There'])

    with pytest.raises(MaxSizeExceededError):
        a.insert(1, 'Bruh')

    with pytest.raises(MaxSizeExceededError):
        a.insert(4, 'Bruh')

def test_invalid_iadd():
    a = BinaryBuffer(ctypes.c_uint, 3, range(2))

    with pytest.raises(MaxSizeExceededError):
        a += [1, 2]

def test_invalid_imul():
    a = BinaryBuffer(ctypes.c_uint, 4, [1, 2])

    with pytest.raises(MaxSizeExceededError):
        a *= 3

def test_valid_item_assignment():
    a = BinaryBuffer(ctypes.c_uint8, 10, [0x41] * 10)

    a[0] = 0x0
    assert a[0].value == 0

def test_valid_serialization():
    a = BinaryBuffer(ctypes.c_uint8, 10, [0x41] * 10)

    assert bytes(a) == b'A' * 10

def test_valid_serialization_not_full():
    a = BinaryBuffer(ctypes.c_uint8, 15, [0x41] * 10)

    assert bytes(a) == b'A' * 10 + b'\x00' * 5

def test_valid_serialization_empty():
    a = BinaryBuffer(ctypes.c_uint, 0)

    assert bytes(a) == b''
