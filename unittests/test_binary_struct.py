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
