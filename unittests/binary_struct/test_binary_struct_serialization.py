import struct
import pytest

from endianness import big_endian, little_endian
from conftest import EmptyClass, SimpleClass, BufferClass, NestedClass, \
                     DuplicateClass, DynamicClass, InheritedClass, \
                     MultipleInheritedClass


def empty_decorator(cls):
    return cls

available_decorators = [
    [empty_decorator, '='],
    [big_endian, '>'],
    [little_endian, '<']
]

# List of BinaryStruct, parameters for the init,
# struct.pack format, and fitting arguements
available_structs = [
    [
        EmptyClass,
        {},
        '', []
    ],
    [
        SimpleClass,
        {'a': 89},
        'B', [89]
    ],
    [
        BufferClass,
        {'size': 423652, 'buf': range(3)},
        'I32s', [423652, bytes(range(3)) + b'\x00' * 29]
    ],
    [
        DuplicateClass,
        {'magic': 0xcafebabe},
        'I', [0xcafebabe]
    ],
    [
        DynamicClass,
        {'magic': 0xef, 'buf': range(99)},
        'B99s', [0xef, bytes(range(99))]
    ],
    [
        InheritedClass,
        {'size': 50, 'buf': range(9), 'magic': 0x12345678},
        'I32sI', [50, bytes(range(9)) + b'\x00' * 23, 0x12345678]
    ],
    [
        MultipleInheritedClass,
        {'size': 99, 'buf': range(15), 'a': 7 ,'magic': 0x90807060},
        'I32sBI', [99, bytes(range(15)) + b'\x00' * 17, 7, 0x90807060]
    ],

    [
        NestedClass,
        {'buffer': [5, [1]], 'magic': 0xdeadbeef},
        'I32sI', [5, b'\x01' + b'\x00' * 31, 0xdeadbeef]
    ]
]

# Make the new test_params
test_params = []
for cls_params in available_structs:
    for decorator_params in available_decorators:
        test_params.append(tuple(decorator_params + cls_params))

@pytest.mark.parametrize('decorator, endianness, cls, cls_params, struct_format, struct_params', test_params)
def test_serialization(decorator, endianness, cls, cls_params, struct_format, struct_params):
    binary_struct = decorator(cls)(**cls_params)

    assert bytes(binary_struct) == struct.pack(f'{endianness}{struct_format}', *struct_params)

@pytest.mark.parametrize('decorator, endianness, cls, cls_params, struct_format, struct_params', test_params)
def test_serialization_empty(decorator, endianness, cls, cls_params, struct_format, struct_params):
    binary_struct = decorator(cls)()

    assert bytes(binary_struct) == b'\x00' * binary_struct.size_in_bytes

@pytest.mark.parametrize('decorator, endianness, cls, cls_params, struct_format, struct_params', test_params)
def test_deserialization(decorator, endianness, cls, cls_params, struct_format, struct_params):
    new_cls = decorator(cls)
    binary_struct = new_cls(**cls_params)
    deserialized = new_cls().deserialize(struct.pack(f'{endianness}{struct_format}', *struct_params))

    assert deserialized == binary_struct

@pytest.mark.parametrize('decorator, endianness, cls, cls_params, struct_format, struct_params', test_params)
def test_deserialization_empty(decorator, endianness, cls, cls_params, struct_format, struct_params):
    new_cls = decorator(cls)
    binary_struct = new_cls()
    deserialized = new_cls().deserialize(b'\x00' * binary_struct.size_in_bytes)

    assert deserialized == binary_struct

@pytest.mark.parametrize('decorator, endianness, cls, cls_params, struct_format, struct_params', test_params)
def test_deserialization_too_small(decorator, endianness, cls, cls_params, struct_format, struct_params):
    # Does not apply to empty class
    if cls is not EmptyClass:
        new_cls = decorator(cls)()

        with pytest.raises(ValueError):
            new_cls.deserialize(b'\x00' * (new_cls.size_in_bytes - 1))

@pytest.mark.parametrize('decorator, endianness, cls, cls_params, struct_format, struct_params', test_params)
def test_serialization_and_deserialization(decorator, endianness, cls, cls_params, struct_format, struct_params):
    new_cls = decorator(cls)

    original_struct = new_cls(**cls_params)
    binary_struct = new_cls().deserialize(bytes(original_struct))

    assert binary_struct == original_struct
