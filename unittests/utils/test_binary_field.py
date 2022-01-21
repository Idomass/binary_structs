import pytest
import random

from binary_structs import BinaryField, uint8_t, int8_t, int16_t, uint16_t, \
                           int32_t, uint32_t, int64_t, uint64_t,            \
                           be_uint8_t, be_int8_t, be_int16_t, be_uint16_t,  \
                           be_int32_t, be_uint32_t, be_int64_t, be_uint64_t
from conftest import binary_fields

# tests are catograized to:
#   - underlying_type
#   - default value
#   - size
#   - deserialization buffer
test_buffer = [
    # little endian
    (int8_t, -128, 1, b'\x80'),
    (uint8_t, 250, 1, b'\xfa'),
    (int16_t, -11214, 2, b'\x32\xd4'),
    (uint16_t, 65001, 2, b'\xe9\xfd'),
    (int32_t, -12891289, 4, b'\x67\x4b\x3b\xff'),
    (uint32_t, 9384012, 4, b'\x4c\x30\x8f\x00'),
    (int64_t, -3712379149898, 8, b'\xff\xff\xfc\x9f\xa4\xf5\xa1\xb6'[::-1]),
    (uint64_t, 28427847382434, 8, b'\x00\x00\x19\xda\xdf\xbe\xb5\xa2'[::-1]),

    # big endian
    (be_int8_t, -128, 1, b'\x80'),
    (be_uint8_t, 250, 1, b'\xfa'),
    (be_int16_t, -11214, 2, b'\x32\xd4'[::-1]),
    (be_uint16_t, 65001, 2, b'\xe9\xfd'[::-1]),
    (be_int32_t, -12891289, 4, b'\x67\x4b\x3b\xff'[::-1]),
    (be_uint32_t, 9384012, 4, b'\x4c\x30\x8f\x00'[::-1]),
    (be_int64_t, -3712379149898, 8, b'\xff\xff\xfc\x9f\xa4\xf5\xa1\xb6'),
    (be_uint64_t, 28427847382434, 8, b'\x00\x00\x19\xda\xdf\xbe\xb5\xa2'),
]

@pytest.mark.parametrize('underlying_type, default_value, size, buf', test_buffer)
def test_valid_init(underlying_type, default_value, size, buf):
    a = underlying_type(default_value)

    assert a == default_value

@pytest.mark.parametrize('underlying_type, default_value, size, buf', test_buffer)
def test_valid_size(underlying_type, default_value, size, buf):
    a = underlying_type(default_value)

    assert a.size_in_bytes == size

@pytest.mark.parametrize('underlying_type, default_value, size, buf', test_buffer)
def test_valid_deserialization(underlying_type, default_value, size, buf):
    a = underlying_type()

    a.deserialize(buf)
    assert a == default_value

@pytest.mark.parametrize('underlying_type, default_value, size, buf', test_buffer)
def test_invalid_deserialization_empty(underlying_type, default_value, size, buf):
    a = underlying_type()

    with pytest.raises(ValueError):
        a.deserialize(b'')

@pytest.mark.parametrize('underlying_type, default_value, size, buf', test_buffer)
def test_valid_serialization(underlying_type, default_value, size, buf):
    a = underlying_type(default_value)

    assert bytes(a) == buf

@pytest.mark.parametrize('underlying_type, default_value, size, buf', test_buffer)
def test_valid_serialization_empty(underlying_type, default_value, size, buf):
    a = underlying_type()

    assert bytes(a) == b'\x00' * a.size_in_bytes

@pytest.mark.parametrize('underlying_type, default_value, size, buf', test_buffer)
def test_two_default_ctors_instances_are_different(underlying_type, default_value, size, buf):
    a = underlying_type()
    b = underlying_type()

    assert a is not b

@pytest.mark.parametrize('underlying_type, default_value, size, buf', test_buffer)
def test_eq_operator_self(underlying_type, default_value, size, buf):
    a = underlying_type(default_value)

    assert a == a

@pytest.mark.parametrize('underlying_type, default_value, size, buf', test_buffer)
def test_eq_operator(underlying_type, default_value, size, buf):
    a = underlying_type(default_value)
    b = underlying_type(default_value)

    assert a == b
    assert a == default_value
    assert a != default_value + 1

# Bitwise tests
bw_op = ['__and__', '__xor__', '__or__']
two_operands_list = [(kind1, kind2, op) for kind1 in binary_fields for kind2 in binary_fields for op in bw_op]

def _get_random_bytes_buffer(size, max_size):
    return bytes([random.randint(0x0, 0xff) for _ in range(size)]) + b'\x00' * (max_size - size)

@pytest.mark.parametrize('field_type', binary_fields)
def test_bitwise_not(field_type):
    num = field_type()
    buf = _get_random_bytes_buffer(num.size_in_bytes, num.size_in_bytes)
    num.deserialize(buf)

    assert ~num == bytes(~x & 0xff for x in buf)

@pytest.mark.parametrize('type1, type2, operand', two_operands_list)
def test_bitwise_operator2(type1, type2, operand):
    num1 = type1()
    num2 = type2()

    bigger_num_size = max(num1.size_in_bytes, num2.size_in_bytes)
    buf1 = _get_random_bytes_buffer(num1.size_in_bytes, bigger_num_size)
    buf2 = _get_random_bytes_buffer(num2.size_in_bytes, bigger_num_size)

    num1.deserialize(buf1[:num1.size_in_bytes])
    num2.deserialize(buf2[:num2.size_in_bytes])

    bitwised_buf = bytes(getattr(int, operand)(a, b) for (a, b) in zip(buf1, buf2))

    assert getattr(BinaryField, operand)(num1, num2) == getattr(BinaryField, operand)(num2, num1)
    assert bitwised_buf == getattr(BinaryField, operand)(num1, num2)
