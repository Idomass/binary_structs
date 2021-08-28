import ctypes

from binary_struct import binary_struct
from buffers.binary_buffer import BinaryBuffer, MaxSizeExceededError


def test_empty_class(EmptyClass):
    EmptyClass()

def test_empty_class_paranthesses():
    @binary_struct()
    class A:
        pass

    A()

def test_valid_simple_class(SimpleClass):
    a = SimpleClass(5)

    assert a.a == 5

def test_invalid_simple_class(SimpleClass):
    try:
        SimpleClass(10, 7)
        assert False

    except TypeError:
        pass

def test_valid_simple_class_assert_type(SimpleClass):
    a = SimpleClass(5)

    assert isinstance(a.a, int)
    assert a.a == 5

def test_valid_complex_class(ComplexClass):
    a = ComplexClass(69, 'nice', b'\xde\xad\xbe\xef')

    assert isinstance(a.num, int)
    assert a.num == 69

    assert isinstance(a.line, str)
    assert a.line == 'nice'

    assert isinstance(a.buf, bytes)
    assert a.buf == b'\xde\xad\xbe\xef'

def test_valid_type_alias():
    tmp = bytes

    @binary_struct
    class A:
        b: tmp

    a = A(b'\xff')

    assert isinstance(a.b, bytes)
    assert a.b == b'\xff'

def test_valid_class_with_modules(ModuleClass):
    buf = BinaryBuffer(int, 10)
    a = ModuleClass(buf, 244)

    assert isinstance(a.buf, BinaryBuffer)
    assert a.buf == buf

    assert isinstance(a.magic, ctypes.c_uint32)
    assert a.magic.value == 244

def test_invalid_wrong_values(ModuleClass):
    try:
        ModuleClass('Noder', 15)
        assert False

    except AssertionError:
        pass

def test_valid_buffer(BufferClass):
    a = BufferClass(32, [97] * 32)

    for element in a.buf:
        assert element.value == 97

    assert isinstance(a.buf[0], ctypes.c_uint8)

def test_invalid_length_buffer(BufferClass):
    try:
        BufferClass(90, [100] * 90)
        assert False

    except TypeError:
        pass

def test_valid_empty_buffer(BufferClass):
    a = BufferClass(5, [])

    for element in a.buf:
        assert element.value == 0

def test_invalid_buffer_overflow(BufferClass):
    try:
        a = BufferClass(32, [67] * 32)

        a.buf.append(6)
        assert False

    except MaxSizeExceededError:
        pass

def test_valid_nested_class(BufferClass, NestedClass):
    a = BufferClass(5, range(5))
    b = NestedClass(a, 0xdeadbeef)

    assert isinstance(b.buffer, BufferClass)
    assert b.buffer == a

def test_valid_class_duplicate_members(DuplicateClass):
    a = DuplicateClass(0xff)

    assert isinstance(a.magic, ctypes.c_uint32)
    assert a.magic.value == 0xff
