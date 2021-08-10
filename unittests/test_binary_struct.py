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
