import struct


def test_valid_serialization(BufferClass):
    a = BufferClass(20, [0x41] * 20)

    assert bytes(a) == struct.pack('I20s', 20, b'A' * 20)

def test_valid_serialization_empty(EmptyClass):
    a = EmptyClass()

    assert bytes(a) == b''
