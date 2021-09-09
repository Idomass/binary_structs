# Binary Structs
## General
The main idea behind BinaryStruct, is to have a pythonic and easy way to work with binary data.

The library uses `type hints` in order auto-implement a serialization function, deserialization function,
an `__init__` method, and more.


## API examples
binary_structs exports 3 main decorators: `binary_struct`, `big_endian`, `little_endian`.

### `@binary_struct`
The of `@binary_struct` usage is simple:
```python
from binary_structs import binary_struct, uint8_t, uint32_t

@binary_struct
class BufferWithSize:
    size: uint32_t
    data: [uint8_t, 8]

buf = BufferWithSize(16, list(range(8)))
```
This will declare a struct with 2 fields, size of the type `uint32_t` and a buffer of `uint8_t` with the size 8.

We can now access `buf` fields:
```python
In:     buf.data[3].value
Out:    3
```

We can now use `buf` to serialize:
```python
In:     bytes(buf)
Out:    b'\x10\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07'
```

Get its size:
```python
In:     buf.size_in_bytes
Out:    12
```
Note that when using this Syntax, `data` attribute will be a list with a size of 8, containing `uint8_t` types.
If we want to have no size limit on `data`, we can use the next annotation:
```python
data: [uint8_t]
```

### Inheritence
We can inherit from binary structs, and add to it custom fields:
```python
@binary_struct
class MagicalBufferWithSize(BufferWithSize):
    magic: uint32_t

magical_buf = MagicalBufferWithSize(magic=0xdeadbeef)
```
The class that we inherited from will be appended to the start of our class.
Note that we did not initialized BufferWithSize fields, and they got initialized with the default values
of their fields.

Serializing `magical_buf` now and getting its size will return:
```python
In:     bytes(magical_buf)
Out:    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xef\xbe\xad\xde'

In:     magical_buf.size_in_bytes
Out:    16
```

### Nesting classes
We can also nest other classes in our classes, if we want to:
```python
@binary_struct
class MagicalBufferWithSize:
    magic: uint32_t
    data: BufferWithSize

buf = BufferWithSize(size=5)
magical_buf = MagicalBufferWithSize(magic=0xdeadbeef, data=buf)
```

### `@big_endian` and `@little_endian`
We can change the endianness of our `BufferWithSize` easily, using the `@big_endian`/`@little_endian` decorator.
Of course we can do that to the Nested version and the Inherited version.

```python
from binary_structs import big_endian

@big_endian
@binary_struct
class BufferWithSize:
    size: uint32_t
    data: [uint8_t, 8]

buf = BufferWithSize(16, list(range(8)))
```

As we can see, `size` attribute has changed its endianness:
```python
In:     bytes(buf)
Out:    b'\x00\x00\x00\x10\x00\x01\x02\x03\x04\x05\x06\x07'
```

If we want to change the endianity of exsiting class without redefining it, we can simply use:
```python
@big_endian
class BEMagicalBufferWithSize(MagicalBufferWithSize):
    magic: uint32_t
    data: BufferWithSize
```
Both `magic` and `data` will be converted to Big endian versions in this example.

### Custom implementations
We can always add a custom implementation to override the auto-implementation:
```python
class BufferWithSize:
    size: uint32_t
    data: [uint8_t, 8]

    def __bytes__(self):
        return b'Hello world' + super(type(self), self).__bytes__()
```
This implementation will greet the user before giving him the serialized data, VERY useful.

Note that we used super, and for some reason it worked. This is thanks to the (probably) over complex implementation of
BinaryStruct

## Implementation
### Abstract
In binary_structs, for each class we decorate The class will be reconstructed and a new parent class will be added, named `NewBinaryStruct`. `NewBinaryStruct` inherits from `BinaryField` interface.
The generated code will be created for `NewBinaryStruct`, and the original class will be duplicated and recreated
with a new parent class.

### BinaryField
`BinaryField` is the interface that allows classes to be used inside a `@binary_struct` class.
Each field must have a `size_in_bytes` attribute, an `__bytes__` function and a `deserialize(buf)` function.

BinaryField has a sub-type, named `PrimitiveTypeField` which implement these function for `ctypes`.
So the primitive types we already used are a `BinaryField` as well.

### Example
This decleration that we already saw:
```python
class BufferWithSize:
    size: uint32_t
    data: [uint8_t, 8]
```

Will generate the following class:
```python
class NewBinaryStruct(BinaryField):
    def __init__(self, size = uint32_t(), data = []):
        # Generated code
        pass

    def __bytes__(self):
        # More generated code
        pass

    def deserialize(buf):
        # Even more generated code
        pass

class BufferWithSize(NewBinaryStruct):
    pass
```
`NewBinaryStruct` is not added to the global variables, so you don't need to worry about referencing it.
This is necessary for allowing the `super()` syntax, and for keeping the original class intact.

### TypedBuffer and BinaryBuffer
When using the buffer syntax (`data: [uint8_t, 32]` or `data: [uint8_t]`), the decorator will create an instance for
a `BinaryBuffer` and a `TypedBuffer` respectively.

A `TypedBuffer`, as the name suggests, enforces that each parameter that is being
passed to it has the same type as the underlying type it was declared with.
`TypedBuffer` implements the `BinaryField` interface

A `BinaryBuffer` is a `TypedBuffer` that also enforces size, and it will create empty instances of its underlying type when
it is created

## WIP/TODO Features
- [ ] Test coverage for `little_endian`
- [ ] More test cases for inheritence
- [ ] Add `__str__` and `__repr__`
- [ ] Add `+` operator between `binary_struct`
- [ ] Full Deserialization support
- [ ] A `@binary_union` decorator
- [ ] Bitwise operations
