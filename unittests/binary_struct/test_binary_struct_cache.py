from endianness import big_endian, little_endian
from binary_struct import BinaryStructHasher, binary_struct, _process_class
from utils.binary_field import be_uint8_t, int8_t, uint32_t, uint64_t, uint8_t


def test_cache_hit_empty():
    class Empty1:
        def foo(self):
            return True

    class Empty2:
        def bar(self):
            return True

    hash1 = BinaryStructHasher(Empty1)
    hash2 = BinaryStructHasher(Empty2)

    assert hash(hash1) == hash(hash2)
    assert hash1 == hash2

def test_cache_hit_primitive():
    hash1 = BinaryStructHasher(uint8_t)
    hash2 = BinaryStructHasher(uint8_t)

    assert hash(hash1) == hash(hash2)
    assert hash1 == hash2

def test_cache_miss_primitive():
    hash1 = BinaryStructHasher(uint8_t)
    hash2 = BinaryStructHasher(int8_t)

    assert hash(hash1) != hash(hash2)
    assert hash1 != hash2

def test_cache_hit_simple():
    class SimpleClass:
        a: int8_t

    class StillSimpleClass:
        a: int8_t

    hash1 = BinaryStructHasher(SimpleClass)
    hash2 = BinaryStructHasher(StillSimpleClass)

    assert hash(hash1) == hash(hash2)
    assert hash1 == hash2

def test_cache_miss_different_name():
    class SimpleClass:
        a: int8_t

    class StillSimpleClass:
        data: int8_t

    hash1 = BinaryStructHasher(SimpleClass)
    hash2 = BinaryStructHasher(StillSimpleClass)

    assert hash(hash1) != hash(hash2)

def test_cache_miss_simple():
    class SimpleClass:
        a: int8_t

    class StillSimpleClass:
        a: uint8_t

    hash1 = BinaryStructHasher(SimpleClass)
    hash2 = BinaryStructHasher(StillSimpleClass)

    assert hash(hash1) != hash(hash2)

def test_cache_hit_with_binary_buffer():
    class SizedBuffer:
        size: uint32_t
        data: [uint8_t, 32]

    class BufferWithSize:
        size: uint32_t
        data: [uint8_t, 32]

    hash1 = BinaryStructHasher(SizedBuffer)
    hash2 = BinaryStructHasher(BufferWithSize)

    assert hash(hash1) == hash(hash2)
    assert hash1 == hash2

def test_cache_miss_with_binary_buffer():
    class SizedBuffer:
        size: uint32_t
        data: [uint8_t, 32]

    class BufferWithSize:
        size: uint32_t
        data: [uint32_t, 32]

    hash1 = BinaryStructHasher(SizedBuffer)
    hash2 = BinaryStructHasher(BufferWithSize)

    assert hash(hash1) != hash(hash2)

def test_cache_hit_with_typed_buffer():
    class DynamicBuffer:
        size: uint32_t
        data: [uint8_t]

    class BufferDynamic:
        size: uint32_t
        data: [uint8_t]

    hash1 = BinaryStructHasher(DynamicBuffer)
    hash2 = BinaryStructHasher(BufferDynamic)

    assert hash(hash1) == hash(hash2)
    assert hash1 == hash2

def test_cache_miss_with_typed_buffer():
    class DynamicBuffer:
        size: uint32_t
        data: [uint32_t]

    class BufferDynamic:
        size: uint32_t
        data: [uint8_t]

    hash1 = BinaryStructHasher(DynamicBuffer)
    hash2 = BinaryStructHasher(BufferDynamic)

    assert hash(hash1) != hash(hash2)

def test_cache_hit_with_same_inheritence():
    class A:
        pass

    class B:
        pass

    class Simple(A, B):
        data: uint8_t

    class StillSimple(A, B):
        data: uint8_t

    hash1 = BinaryStructHasher(Simple)
    hash2 = BinaryStructHasher(StillSimple)

    assert hash(hash1) == hash(hash2)
    assert hash1 == hash2

def test_cache_miss_with_different_inheritence():
    class A:
        pass

    class B:
        pass

    class Simple(A):
        data: uint8_t

    class StillSimple(B):
        data: uint8_t

    hash1 = BinaryStructHasher(Simple)
    hash2 = BinaryStructHasher(StillSimple)

    assert hash(hash1) == hash(hash2)
    assert hash1 != hash2

def test_cache_hit_with_inheritence_name_duplication():
    class A:
        data: uint8_t

    class B:
        data: uint8_t

    class Simple(A, B):
        magic: uint8_t

    class StillSimple(B, A):
        magic: uint8_t

    hash1 = BinaryStructHasher(Simple)
    hash2 = BinaryStructHasher(StillSimple)

    assert hash(hash1) == hash(hash2)
    assert hash1 != hash2

def test_cache_miss_with_inheritence():
    class A:
        data: uint8_t

    class B(A):
        data2: uint8_t

    class C(A):
        data2: uint32_t

    class Simple(B):
        data3: uint8_t

    class StillSimple(C):
        data3: uint8_t

    hash1 = BinaryStructHasher(Simple)
    hash2 = BinaryStructHasher(StillSimple)

    assert hash(hash1) != hash(hash2)
    assert hash1 != hash2

def test_cache_miss_with_gap_in_inheritence():
    class A:
        data: uint8_t

    class B:
        data: uint8_t

    class C(A):
        pass

    class Simple(B):
        buf: [uint64_t]

    class SimpleButEmpty(C):
        buf: [uint64_t]

    hash1 = BinaryStructHasher(Simple)
    hash2 = BinaryStructHasher(SimpleButEmpty)

    assert hash(hash1) != hash(hash2)
    assert hash1 != hash2

# Cache tests for _process_class
def test_cache_hit_classes_are_different():
    @binary_struct
    class A:
        data: uint8_t

    @binary_struct
    class B:
        data: uint8_t

    assert B is not A
    assert _process_class.cache_info().hits == 1

def test_cache_hit_endianness_base_classes_are_different():
    @binary_struct
    class A:
        data: uint8_t

    @binary_struct
    class B:
        data: be_uint8_t

    @big_endian
    class C(B):
        pass

    assert C.__bases__[0] is not A
    assert _process_class.cache_info().hits == 1

def test_cache_hit_inheritence():
    # cache miss 1
    @binary_struct
    class A:
        a: uint32_t

    # cache miss 2
    B = big_endian(A)

    # cache miss 3
    @binary_struct
    class C:
        a: A
        b: [A]
        c: [A, 32]

    # cache hit for each A, 3 hits, 1 miss for D
    D = big_endian(C)
    # 1 cache hit for C, and 3 for A
    E = big_endian(C)

    assert E is not D
    assert _process_class.cache_info().misses == 4
    assert _process_class.cache_info().hits == 7
