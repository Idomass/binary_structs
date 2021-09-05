import pytest

from utils.binary_field import uint8_t, int8_t, int16_t, uint16_t, \
                               int32_t, uint32_t, int64_t, uint64_t, \
                               be_uint8_t, be_int8_t, be_int16_t, be_uint16_t,\
                               be_int32_t, be_uint32_t, be_int64_t, be_uint64_t


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
