import pytest

from utils.binary_field import uint8_t
from utils.buffers.typed_buffer import TypedBuffer


def test_valid_init():
    a = TypedBuffer(uint8_t, [1, 2, 3])

    assert isinstance(a[0], uint8_t)
    assert a == [1, 2, 3]

def test_invalid_init():
    with pytest.raises(TypeError):
        TypedBuffer(uint8_t, ['BadValue'])

def test_valid_init_different_ctor():
    a = TypedBuffer(uint8_t, [97] * 50)

    for element in a:
        assert element.value == 97

def test_valid_append(typed_buffer):
    typed_buffer.append(uint8_t(50))

    assert typed_buffer[-1].value == 50

def test_invalid_append(typed_buffer):
    with pytest.raises(TypeError):
        typed_buffer.append('Bruh')

def test_valid_append_differnent_ctor(typed_buffer):
    typed_buffer.append(5)

    assert typed_buffer[-1].value == 5

def test_item_assignment_valid(typed_buffer):
    typed_buffer[0] = uint8_t(1)

    assert typed_buffer[0].value == 1

def test_item_assigment_invalid(typed_buffer):
    with pytest.raises(TypeError):
        typed_buffer[0] = 'Hello'

def test_item_assignment_valid_different_ctor(typed_buffer):
    typed_buffer[0] = 5

    assert typed_buffer[0].value == 5

def test_list_slicing_valid(typed_buffer):
    typed_buffer[:10] = [uint8_t(0)] * 10

    for i in range(10):
        assert typed_buffer[i].value == 0

    for j in range(10):
        assert typed_buffer[i + j + 1].value == 97

def test_list_slicing_invalid(typed_buffer):
    with pytest.raises(TypeError):
        typed_buffer[:5] = ['hello', 'world']

def test_list_slicing_valid_different_ctor(typed_buffer):
    typed_buffer[:10] = [0] * 10

    for i in range(10):
        assert typed_buffer[i].value == 0

    for j in range(10):
        assert typed_buffer[i + j + 1].value == 97

def test_valid_copy(typed_buffer):
    original_buffer = typed_buffer[:]

    assert original_buffer == typed_buffer

    typed_buffer[5] = 3
    assert original_buffer != typed_buffer

def test_valid_extend(typed_buffer):
    typed_buffer.extend([uint8_t(50)] * 5)

    for i in range(20):
        assert typed_buffer[i].value == 97

    for j in range(5):
        assert typed_buffer[i + 1 + j].value == 50

def test_invalid_extend(typed_buffer):
    with pytest.raises(TypeError):
        typed_buffer.extend(['Noder', 'neder'])

def test_valid_extend_different_ctor(typed_buffer):
    typed_buffer.extend([50] * 5)

    for i in range(20):
        assert typed_buffer[i].value == 97

    for j in range(5):
        assert typed_buffer[i + 1 + j].value == 50

def test_valid_iadd(typed_buffer):
    typed_buffer += [uint8_t(50)] * 5

    for i in range(20):
        assert typed_buffer[i].value == 97

    for j in range(5):
        assert typed_buffer[i + 1 + j].value == 50

def test_invalid_iadd(typed_buffer):
    with pytest.raises(TypeError):
        typed_buffer += ['Hello', 'world']

def test_valid_iadd_different_ctor(typed_buffer):
    typed_buffer += [50] * 5

    for i in range(20):
        assert typed_buffer[i].value == 97

    for j in range(5):
        assert typed_buffer[i + 1 + j].value == 50

def test_valid_insert(typed_buffer):
    typed_buffer.insert(10, uint8_t(0))

    for i in range(10):
        assert typed_buffer[i].value == 97

    assert typed_buffer[i + 1].value == 0

    for j in range(10):
        assert typed_buffer[i + 1 + 2].value == 97

def test_invalid_insert(typed_buffer):
    with pytest.raises(TypeError):
        typed_buffer.insert(5, 'hi')

def test_valid_insert_different_ctor(typed_buffer):
    typed_buffer.insert(10, 0)

    for i in range(10):
        assert typed_buffer[i].value == 97

    assert typed_buffer[i + 1].value == 0

    for j in range(10):
        assert typed_buffer[i + 1 + 2].value == 97

def test_valid_serialization_empty():
    assert bytes(TypedBuffer(uint8_t)) == b''

def test_valid_serialization(typed_buffer):
    assert bytes(typed_buffer) == b'a' * 20

def test_valid_size(typed_buffer):
    assert typed_buffer.size_in_bytes == 20

def test_valid_size_empty():
    a = TypedBuffer(uint8_t)

    assert a.size_in_bytes == 0
