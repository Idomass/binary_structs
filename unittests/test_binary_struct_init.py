import ctypes
from binary_struct import binary_struct


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

    assert a.a == 5
    assert isinstance(a.a, int)

def test_valid_complex_class(ComplexClass):
    a = ComplexClass(69, 'nice', b'\xde\xad\xbe\xef')

    assert a.num == 69
    assert isinstance(a.num, int)

    assert a.line == 'nice'
    assert isinstance(a.line, str)

    assert a.buf == b'\xde\xad\xbe\xef'
    assert isinstance(a.buf, bytes)

def test_valid_type_alias():
    tmp = bytes

    @binary_struct
    class A:
        b: tmp

    a = A(b'\xff')

    assert a.b == b'\xff'
    assert isinstance(a.b, bytes)

def test_valid_class_with_modules(ModuleClass):
    a = ModuleClass(12345678, 244)

    assert a.ptr.value == 12345678
    assert isinstance(a.ptr, ctypes.c_void_p)

    assert a.size.value == 244
    assert isinstance(a.size, ctypes.c_uint32)

def test_invalid_wrong_values(ModuleClass):
    try:
        ModuleClass('Noder', 15)
        assert False

    except TypeError:
        pass

def test_valid_buffer(BufferClass):
    a = BufferClass(32, [97] * 32)

    assert a.size.value == 32
    assert isinstance(a.size, ctypes.c_uint32)

    for element in a.buf:
        assert element.value == 97
    assert isinstance(a.buf[0], ctypes.c_uint8)

def test_invalid_length_buffer(BufferClass):
    try:
        BufferClass(90, [100] * 90)
        assert False

    except TypeError:
        pass