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
