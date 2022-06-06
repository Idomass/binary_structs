from itertools import product

import pytest
from binary_structs.utils import *
from conftest import binary_fields


@pytest.mark.parametrize('field_type', binary_fields)
def test_valid_typed_buffer_build(field_type):
    typed_buf_cls = new_typed_buffer(field_type)
    typed_buf_instance = typed_buf_cls(*range(10))

    assert isinstance(typed_buf_instance, new_binary_buffer(field_type, 10))


@pytest.mark.parametrize('field_type, buffer', product(binary_fields, (b'', b'\x7f' * 8)))
def test_valid_typed_buffer_deserialize(field_type, buffer):
    typed_buf_cls = new_typed_buffer(field_type)
    typed_buf_instance = typed_buf_cls.deserialize(bytearray(buffer))

    assert bytes(typed_buf_instance) == buffer
    assert isinstance(typed_buf_instance, new_binary_buffer(field_type, len(buffer) // field_type.static_size))
