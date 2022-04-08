import pytest

from os import urandom

from conftest import binary_fields
from binary_structs import new_typed_buffer, uint32_t, uint8_t, le_uint8_t

# Fixtures
@pytest.fixture
def typed_buffer():
    return new_typed_buffer(le_uint8_t)([97] * 20)

# Tests
def test_valid_init():
    a = new_typed_buffer(uint8_t)([1, 2, 3])

    assert isinstance(a[0], uint8_t)
    assert a == [1, 2, 3]

def test_invalid_init():
    with pytest.raises(TypeError):
        new_typed_buffer(uint8_t)(['BadValue'])

def test_valid_init_different_ctor():
    a = new_typed_buffer(uint8_t)([97] * 50)

    assert a == [97] * 50

def test_valid_append(typed_buffer):
    typed_buffer.append(le_uint8_t(50))

    assert typed_buffer[-1].value == 50

def test_invalid_append(typed_buffer):
    with pytest.raises(TypeError):
        typed_buffer.append('Bruh')

def test_valid_append_differnent_ctor(typed_buffer):
    typed_buffer.append(5)

    assert typed_buffer[-1].value == 5

def test_item_assignment_valid(typed_buffer):
    typed_buffer[0] = le_uint8_t(1)

    assert typed_buffer[0].value == 1

def test_item_assigment_invalid(typed_buffer):
    with pytest.raises(TypeError):
        typed_buffer[0] = 'Hello'

def test_item_assignment_valid_different_ctor(typed_buffer):
    typed_buffer[0] = 5

    assert typed_buffer[0].value == 5

def test_list_slicing_valid(typed_buffer):
    typed_buffer[:10] = [le_uint8_t(0)] * 10

    assert typed_buffer[:10] == [0] * 10
    assert typed_buffer[10:] == [97] * 10

def test_list_slicing_valid_empty(typed_buffer):
    assert typed_buffer[25:] == []

def test_list_slicing_invalid(typed_buffer):
    with pytest.raises(TypeError):
        typed_buffer[:5] = ['hello', 'world']

def test_list_slicing_valid_different_ctor(typed_buffer):
    typed_buffer[:10] = [0] * 10

    assert typed_buffer[:10] == [0] * 10
    assert typed_buffer[10:] == [97] * 10

def test_valid_copy(typed_buffer):
    original_buffer = typed_buffer[:]

    assert original_buffer == typed_buffer

    typed_buffer[5] = 3
    assert original_buffer != typed_buffer

def test_valid_extend(typed_buffer):
    typed_buffer.extend([le_uint8_t(50)] * 5)

    assert typed_buffer[:20] == [97] * 20
    assert typed_buffer[20:] == [50] * 5

def test_invalid_extend(typed_buffer):
    with pytest.raises(TypeError):
        typed_buffer.extend(['Noder', 'neder'])

def test_valid_extend_different_ctor(typed_buffer):
    typed_buffer.extend([50] * 5)

    assert typed_buffer[:20] == [97] * 20
    assert typed_buffer[20:] == [50] * 5

def test_valid_iadd(typed_buffer):
    typed_buffer += [le_uint8_t(50)] * 5

    assert typed_buffer[:20] == [97] * 20
    assert typed_buffer[20:] == [50] * 5

def test_invalid_iadd(typed_buffer):
    with pytest.raises(TypeError):
        typed_buffer += ['Hello', 'world']

def test_valid_iadd_different_ctor(typed_buffer):
    typed_buffer += [50] * 5

    assert typed_buffer[:20] == [97] * 20
    assert typed_buffer[20:] == [50] * 5

def test_valid_insert(typed_buffer):
    typed_buffer.insert(10, le_uint8_t(0))

    assert typed_buffer[:10] == [97] * 10
    assert typed_buffer[10] == 0
    assert typed_buffer[11:] == [97] * 10

def test_invalid_insert(typed_buffer):
    with pytest.raises(TypeError):
        typed_buffer.insert(5, 'hi')

def test_valid_insert_different_ctor(typed_buffer):
    typed_buffer.insert(10, 0)

    assert typed_buffer[:10] == [97] * 10
    assert typed_buffer[10] == 0
    assert typed_buffer[11:] == [97] * 10

def test_valid_slicing(typed_buffer):
    sub_buf = typed_buffer[:]

    assert sub_buf is not typed_buffer
    assert isinstance(sub_buf, type(typed_buffer))
    assert sub_buf == typed_buffer

def test_valid_slicing_empty(typed_buffer):
    sub_buf = typed_buffer[1000:]

    assert isinstance(sub_buf, type(typed_buffer))
    assert sub_buf == []

def test_valid_serialization_empty():
    assert bytes(new_typed_buffer(uint8_t)()) == b''

def test_valid_serialization(typed_buffer):
    assert bytes(typed_buffer) == b'a' * 20

def test_valid_size(typed_buffer):
    assert typed_buffer.size_in_bytes == 20

def test_valid_size_empty():
    a = new_typed_buffer(uint8_t)()

    assert a.size_in_bytes == 0

def test_valid_deserialization_empty():
    typed_buffer = new_typed_buffer(uint32_t).deserialize(b'')

    assert typed_buffer.size_in_bytes == 0

def test_valid_deserialization_non_empty():
    typed_buffer = new_typed_buffer(uint8_t).deserialize(b'\xde\xad')

    assert typed_buffer.size_in_bytes == 2
    assert typed_buffer[0] == 0xde
    assert typed_buffer[1] == 0xad

def test_invalid_deserialization_buffer_to_small():
    with pytest.raises(ValueError):
        new_typed_buffer(uint32_t)().deserialize(b'\xde\xad\xbe\xef\xff')

# Conversions
from_bytes_arr = [(field, urandom(field.static_size * 5)) for field in binary_fields]
from_bytes_arr += [(field, b'') for field in binary_fields]

@pytest.mark.parametrize('underlying_type, buf', from_bytes_arr)
def test_valid_from_bytes(underlying_type, buf):
    a = new_typed_buffer(underlying_type).from_bytes(buf)

    assert bytes(a) == buf

from_bytes_arr = [(field, urandom((field.static_size * 5) + 1)) for field in binary_fields if field.static_size != 1]
@pytest.mark.parametrize('underlying_type, buf', from_bytes_arr)
def test_invalid_from_bytes(underlying_type, buf):
    with pytest.raises(AssertionError):
        new_typed_buffer(underlying_type).from_bytes(buf)
