import ctypes
from binary_struct import binary_struct


def test_initialization_empty_class():
    @binary_struct
    class A:
        pass

    A()

def test_initialization_empty_class_paranthesses():
    @binary_struct()
    class A:
        pass

    A()

def test_initialization_valid_simple_class(SimpleClass):
    a = SimpleClass(5)

    assert a.a == 5

def test_initialization_invalid_simple_class(SimpleClass):
    try:
        SimpleClass(10, 7)

    except TypeError:
        pass

def test_initialization_valid_simple_class_assert_type(SimpleClass):
    a = SimpleClass(5)

    assert a.a == 5
    assert isinstance(a.a, int)

def test_initialization_valid_complex_class(ComplexClass):
    a = ComplexClass(69, 'nice', b'\xde\xad\xbe\xef')

    assert a.num == 69
    assert isinstance(a.num, int)

    assert a.line == 'nice'
    assert isinstance(a.line, str)

    assert a.buf == b'\xde\xad\xbe\xef'
    assert isinstance(a.buf, bytes)

def test_initialization_valid_type_alias():
    tmp = bytes

    @binary_struct
    class A:
        b: tmp

    a = A(b'\xff')

    assert a.b == b'\xff'
    assert isinstance(a.b, bytes)

def test_initialization_valid_class_with_modules(ModuleClass):
    a = ModuleClass(12345678, 0x62)

    assert bytes(a.ptr) == b'Na\xbc\x00\x00\x00\x00\x00'
    assert isinstance(a.ptr, ctypes.c_void_p)

    assert bytes(a.size) == b'\x62\x00\x00\x00'
    assert isinstance(a.size, ctypes.c_uint32)
