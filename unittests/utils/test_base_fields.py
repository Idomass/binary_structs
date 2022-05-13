from random import randint
from typing import Tuple

import pytest
from binary_structs.utils.binary_field.base_fields import *

integer_types = (
    # class     size    signed
    (int8_t,    1,      True),
    (uint8_t,   1,      False),
    (int16_t,   2,      True),
    (uint16_t,  2,      False),
    (int32_t,   4,      True),
    (uint32_t,  4,      False),
    (int64_t,   8,      True),
    (uint64_t,  8,      False)
)


# Helper functions
def _get_min_max(int_signed: bool, size_in_bytes: int) -> Tuple[int, int]:
    """
    Returns minimum and maximum values for the given integer
    """

    if int_signed:
        max_value = 2 ** ((size_in_bytes * 8) - 1) - 1
        min_value = -max_value

    else:
        max_value = 2 ** (size_in_bytes * 8) - 1
        min_value = 0

    return min_value, max_value


# Tests
@pytest.mark.parametrize('int_type, int_size, int_signed', integer_types)
def test_int_init_empty(int_type, int_size, int_signed):
    assert int_type.size == int_size
    assert int_type.signed == int_signed

    num = int_type()
    assert isinstance(num, int_type)


@pytest.mark.parametrize('int_type, int_size, int_signed', integer_types)
def test_int_init_value(int_type, int_size, int_signed):
    min_value, max_value = _get_min_max(int_signed, int_size)
    rand_value = randint(min_value, max_value)

    # Test random value
    num = int_type(rand_value)
    assert num.value == rand_value

    # Test highest value
    num = int_type(max_value)
    assert num.value == max_value

    # Test lowest value
    num = int_type(min_value)
    assert num.value == min_value


@pytest.mark.parametrize('int_type, int_size, int_signed', integer_types)
def test_int_memory_serialization_equals(int_type, int_size, int_signed):
    min_value, max_value = _get_min_max(int_signed, int_size)
    num = int_type(randint(min_value, max_value))

    assert bytes(num) == num.memory
