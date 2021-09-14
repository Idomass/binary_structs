import struct
import pytest

from binary_struct import binary_struct
from endianness import big_endian, little_endian
from utils.binary_field import uint64_t


def empty_decorator(cls):
    return cls

test_params = [(empty_decorator, '='), (big_endian, '>'), (little_endian, '<')]

# List of struct, params (kwargs), binary_data
# available_struct = [
#     (EmptyClassFixture, {}, b''),

# ]


# Serialization and Deserialization Tests
def test_valid_serialization_empty(EmptyClassFixture):
    a = EmptyClassFixture()

    assert bytes(a) == b''

# TODO test with different structs
def test_valid_class_serialization_with_no_params(BufferClassFixture):
    a = BufferClassFixture()

    assert bytes(a) == b'\x00' * 36

@pytest.mark.parametrize('decorator, format', test_params)
def test_valid_serialization_simple(BufferClassFixture, decorator, format):
    EndianClass = decorator(BufferClassFixture)
    a = EndianClass(20, [0x41] * 32)

    assert bytes(a) == struct.pack(f'{format}I32s', 20, b'A' * 32)

def test_dynamic_class_serialization(DynamicClassFixture):
    a = DynamicClassFixture(10, [97] * 50)

    assert bytes(a) == struct.pack('B50s', 10, b'a' * 50)

    a.buf += [0x41] * 20
    assert bytes(a) == struct.pack('B70s', 10, b'a' * 50 + b'A' * 20)

@pytest.mark.parametrize('decorator, format', test_params)
def test_valid_serialization_simple_inheritence(BufferClassFixture, decorator, format):
    @binary_struct
    class A(BufferClassFixture):
        magic: uint64_t

    EndianClass = decorator(A)
    a = EndianClass(5, [1, 2, 3], 0xdeadbeef)

    assert bytes(a) == struct.pack(f'{format}I32sQ', 5, b'\x01\x02\x03' + b'\x00' * 29, 0xdeadbeef)

@pytest.mark.parametrize('decorator, format', test_params)
def test_valid_serialization_nested_class(NestedClassFixture, decorator, format):
    EndianClass = decorator(NestedClassFixture)
    a = EndianClass.buffer(32, [97] * 32)
    b = EndianClass(a, 0xdeadbeef)

    assert bytes(b) == struct.pack(f'{format}I32sI', 32, b'a' * 32, 0xdeadbeef)

@pytest.mark.parametrize('decorator, format', test_params)
def test_valid_serialization_with_multiple_inheritence(MultipleInheritedClassFixture, decorator, format):
    EndianClass = decorator(MultipleInheritedClassFixture)
    a = EndianClass(32, [97] * 32, 5, 0xff)

    assert bytes(a) == struct.pack(f'{format}I32sBI', 32,  b'a' * 32, 5, 0xff)

@pytest.mark.parametrize('decorator, format', test_params)
def test_valid_serialization_nested_class_default_value(NestedClassFixture, decorator, format):
    EndianClass = decorator(NestedClassFixture)
    b = EndianClass(magic=0xdeadbeef)

    assert bytes(b) == struct.pack(f'{format}I32sI', 0, b'\x00' * 32, 0xdeadbeef)

@pytest.mark.parametrize('decorator, format', test_params)
def test_valid_serialization_nested_and_inherited(InheritedAndNestedClassFixture, decorator, format):
    EndianClass = decorator(InheritedAndNestedClassFixture)
    a = EndianClass.buffer(32, [97] * 32)
    b = EndianClass.buf2(16, [0x41] * 16)
    c = EndianClass(a, 0xdeadbeef, b)

    assert bytes(c) == struct.pack(f'{format}I32sII32s', 32,  b'a' * 32, 0xdeadbeef,
                                   16,  b'A' * 16 + b'\x00' * 16)

@pytest.mark.parametrize('decorator, format', test_params)
def test_valid_serialization_monster_class(MonsterClassFixture, decorator, format):
    EndianClass = decorator(MonsterClassFixture)
    a = EndianClass.buffer(3, [1, 2, 3])
    b = EndianClass.dynamic(0x7f, [1])
    c = EndianClass.empty()

    monster = EndianClass(a, 0xcafebabe, 32, b, c, 0xff)

    assert bytes(monster) == struct.pack(f'{format}I32sIBBBB', 3, b'\x01\x02\x03' + b'\x00', 0xcafebabe,
                                         32, 0x7f, 1, 0xff)


# Deserialization
def test_valid_deserialization_empty(EmptyClassFixture):
    a = EmptyClassFixture().deserialize(b'')

    assert isinstance(a, EmptyClassFixture)

def test_valid_deserialization_simple(SimpleClassFixture):
    a = SimpleClassFixture().deserialize(b'\xff')

    assert a.a.value == 0xff

def test_valid_deserialization_buffer_too_small(SimpleClassFixture):
    with pytest.raises(ValueError):
        SimpleClassFixture().deserialize(b'')

def test_valid_deserialization_buffer(BufferClassFixture):
    a = BufferClassFixture().deserialize(struct.pack('I32s', 20, b'A' * 32))

    assert a.size == 20
    for element in a.buf:
        assert element.value == 0x41

def test_invalid_deserialization_buffer_too_small(BufferClassFixture):
    with pytest.raises(ValueError):
        BufferClassFixture().deserialize(struct.pack('I31s', 20, b'A' * 31))

def test_valid_deserialization_dynamic_class(DynamicClassFixture):
    a = DynamicClassFixture().deserialize(struct.pack('B50s', 10, b'a' * 50))

    assert a.size_in_bytes == 51
    assert a.buf.size_in_bytes == 50
    assert a.magic.value == 10
    for element in a.buf:
        assert element.value == 97

def test_valid_class_with_inheritence_serialization(InheritedClassFixture):
    a = InheritedClassFixture().deserialize(struct.pack('I32sI', 32,  b'a' * 32, 0xff))

    assert a.size.value == 32
    for element in a.buf:
        assert element.value == 97
    assert a.magic.value == 0xff

def test_valid_deserialization_multiple_inheritence(MultipleInheritedClassFixture):
    a = MultipleInheritedClassFixture().deserialize(struct.pack('<I32sBI', 32,  b'a' * 32, 5, 0xdeadbeef))

    assert a.size.value == 32
    for element in a.buf:
        assert element.value == 97
    assert a.a.value == 5
    assert a.magic.value == 0xdeadbeef

def test_valid_deserialization_nested_and_inherited(InheritedAndNestedClassFixture):
    a = InheritedAndNestedClassFixture().deserialize(struct.pack('I32sII32s', 32,  b'a' * 32,
                                              0xdeadbeef, 16, b'A' * 16 + b'\x00' * 16))

    assert a.buffer.size.value == 32
    for element in a.buffer.buf:
        assert element.value == 97

    assert a.magic.value == 0xdeadbeef

    assert a.buf2.size.value == 16
    for element in a.buf2.buf[:16]:
        assert element.value == 0x41
    for element in a.buf2.buf[16:]:
        assert element.value == 0

@pytest.mark.skip(reason='Dynamic class must have size indicator in order to deserialize')
def test_valid_deserialization_monster_class(MonsterClassFixture):
    a = MonsterClassFixture.deserialize(struct.pack('I32sIBBBB', 3, b'\x01\x02\x03' + b'\x00', 0xcafebabe,
                                         32, 0x7f, 1, 0xff))

    # Nested class
    assert a.buffer.size.value == 3
    for element in a.buffer.buf[:3]:
        assert element.value == 3
    for element in a.buffer.buf[3:]:
        assert element.value == 0
    assert a.magic.value == 0xcafebabe

    # Simple class
    assert a.a.value == 32

    # Dynamic
    # TODO, can't be tested because of the dynamic class
