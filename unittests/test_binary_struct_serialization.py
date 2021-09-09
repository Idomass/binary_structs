import struct


def test_valid_serialization(BufferClass):
    a = BufferClass(20, [0x41] * 20)

    assert bytes(a) == struct.pack('I32s', 20, b'A' * 20 + b'\x00' * 12)

def test_valid_serialization_empty(EmptyClass):
    a = EmptyClass()

    assert bytes(a) == b''

def test_valid_serialization_nested_class(BufferClass, NestedClass):
    a = BufferClass(20, [0x41] * 20)
    b = NestedClass(a, 0xdeadbeef)

    assert bytes(b) == struct.pack('I32s', 20, b'A' * 20 + b'\x00' * 12) + b'\xef\xbe\xad\xde'

def test_dynamic_class_serialization(DynamicClass):
    a = DynamicClass(10, [97] * 50)

    assert bytes(a) == struct.pack('B50s', 10, b'a' * 50)

    a.buf += [0x41] * 20
    assert bytes(a) == struct.pack('B70s', 10, b'a' * 50 + b'A' * 20)

def test_valid_class_init_with_no_params(BufferClass):
    a = BufferClass()

    assert bytes(a) == b'\x00' * 36

def test_valid_class_with_inheritence_serialization(InheritedClass):
    a = InheritedClass(32, [97] * 32, 0xff)

    assert bytes(a) == struct.pack('I32sI', 32,  b'a' * 32, 0xff)

def test_valid_class_with_multiple_inheritence_serialization(MultipleInheritedClass):
    a = MultipleInheritedClass(32, [97] * 32, 5, 0xff)

    assert bytes(a) == struct.pack('I32sB', 32,  b'a' * 32, 5) + struct.pack('I', 0xff)

def test_valid_class_nested_and_inherited_serialization(InheritedAndNestedClass, BufferClass):
    a = BufferClass(32, [97] * 32)
    b = BufferClass(16, [0x41] * 16)
    c = InheritedAndNestedClass(a, 0xdeadbeef, b)

    assert bytes(c) == struct.pack('I32s', 32,  b'a' * 32) + struct.pack('I', 0xdeadbeef) \
           + struct.pack('I32s', 16,  b'A' * 16 + b'\x00' * 16)

def test_valid_class_init_with_monster_class_serialization(MonsterClass, DynamicClass, BufferClass, EmptyClass):
    a = BufferClass(3, [1, 2, 3])
    b = DynamicClass(0x7f, [1])
    c = EmptyClass()

    monster = MonsterClass(a, 0xcafebabe, 32, b, c, 0xff)

    assert bytes(monster) == struct.pack('I32s', 3, b'\x01\x02\x03' + b'\x00') + \
                             struct.pack('I', 0xcafebabe) + \
                             struct.pack('BBBB', 32, 0x7f, 1, 0xff)
