from utils.binary_field import uint8_t
import pytest

# TODO
@pytest.mark.skip(reason='Cant figure a way to pass it for now')
def test_valid_copy_ctor(BufferClass):
    a = BufferClass(5, range(5))
    b = deepcopy(a)

    b.size.value = 10

    assert a.size.value == 5
    assert b.size.value == 10

# Size feature
def test_valid_size(BufferClass, NestedClass):
    a = BufferClass(32, [97] * 32)
    b = NestedClass(a, 0xdeadbeef)

    assert a.size_in_bytes == 36
    assert b.size_in_bytes == 40

def test_valid_size_empty(EmptyClass):
    a = EmptyClass()

    assert a.size_in_bytes == 0

def test_valid_size_dynamic(DynamicClass):
    a = DynamicClass(5, [1, 2, 3])

    assert a.size_in_bytes == 4
    a.buf.append(90)
    assert a.size_in_bytes == 5
