import struct
import pytest

from conftest import EmptyClass, available_decorators, test_structs

# List of struct.pack format, and fitting arguements for the test_structs list
structs_formats = [
    # EmptyClass,
    ['', []],
    # SimpleClass,
    ['B', [89]],
    # BufferClass
    ['I32s', [423652, bytes(range(3)) + b'\x00' * 29]],
    # DuplicateClass
    ['I', [0xcafebabe]],
    # DynamicClass
    ['B99s', [0xef, bytes(range(99))]],
    # InheritedClass
    ['I32sI', [50, bytes(range(9)) + b'\x00' * 23, 0x12345678]],
    # MultipleInheritedClass
    ['I32sBI', [99, bytes(range(15)) + b'\x00' * 17, 7, 0x90807060]],
    # NestedClass
    ['I32sI', [5, b'\x01' + b'\x00' * 31, 0xdeadbeef]],
    # MultipleNestedClass
    ['I32sII', [5, b'\x01' + b'\x00' * 31, 0xdeadbeef, 0xcafebabe]]
]

# Make the new test_params
test_params = []
for index, cls_params in enumerate(test_structs):
    for decorator_params in available_decorators:
        test_params.append(tuple(decorator_params + cls_params + structs_formats[index]))

@pytest.mark.parametrize('decorator, endianness, cls, cls_params, struct_format, struct_params', test_params)
def test_serialization(decorator, endianness, cls, cls_params, struct_format, struct_params):
    binary_struct = decorator(cls)(**cls_params)

    assert bytes(binary_struct) == struct.pack(f'{endianness}{struct_format}', *struct_params)

@pytest.mark.parametrize('decorator, endianness, cls, cls_params, struct_format, struct_params', test_params)
def test_serialization_empty(decorator, endianness, cls, cls_params, struct_format, struct_params):
    binary_struct = decorator(cls)()

    assert bytes(binary_struct) == b'\x00' * binary_struct.static_size

@pytest.mark.parametrize('decorator, endianness, cls, cls_params, struct_format, struct_params', test_params)
def test_deserialization(decorator, endianness, cls, cls_params, struct_format, struct_params):
    new_cls = decorator(cls)
    binary_struct = new_cls(**cls_params)
    deserialized = new_cls.deserialize(struct.pack(f'{endianness}{struct_format}', *struct_params))

    assert deserialized == binary_struct

@pytest.mark.parametrize('decorator, endianness, cls, cls_params, struct_format, struct_params', test_params)
def test_deserialization_empty(decorator, endianness, cls, cls_params, struct_format, struct_params):
    new_cls = decorator(cls)
    binary_struct = new_cls()
    deserialized = new_cls.deserialize(b'\x00' * binary_struct.static_size)

    assert deserialized == binary_struct

@pytest.mark.parametrize('decorator, endianness, cls, cls_params, struct_format, struct_params', test_params)
def test_deserialization_too_small(decorator, endianness, cls, cls_params, struct_format, struct_params):
    # Does not apply to empty class
    if cls is not EmptyClass:
        new_cls = decorator(cls)()

        with pytest.raises(ValueError):
            decorator(cls).deserialize(b'\x00' * (new_cls.static_size - 1))

@pytest.mark.parametrize('decorator, endianness, cls, cls_params, struct_format, struct_params', test_params)
def test_serialization_and_deserialization(decorator, endianness, cls, cls_params, struct_format, struct_params):
    new_cls = decorator(cls)

    original_struct = new_cls(**cls_params)
    binary_struct = new_cls.deserialize(bytes(original_struct))

    assert binary_struct == original_struct
