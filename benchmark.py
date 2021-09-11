import pytest

from binary_struct import binary_struct
from endianness import big_endian
from utils.binary_field import uint32_t, uint8_t, uint16_t

# For Caching test
class LightClass:
    a: uint8_t
    b: [uint16_t]
    c: [uint32_t, 64]

A = binary_struct(LightClass)
class HeavyClass(A):
    d: A
    e: [A]
    f: [A, 64]


@pytest.mark.parametrize('cls', [LightClass, HeavyClass])
def test_binary_struct_performance(benchmark, cls):
    benchmark(binary_struct, cls)

@pytest.mark.parametrize('cls', [LightClass, HeavyClass])
def test_endianness_performance(benchmark, cls):
    decorated = binary_struct(cls)

    benchmark(big_endian, decorated)
