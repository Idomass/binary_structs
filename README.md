# Binary Structs
## General
The main idea behind BinaryStruct, is to have a pythonic and easy way to work with binary data.

The library uses `type hints` in order generate these functions:
- `__init__`    - An init function that enforces types
- `__bytes__`   - Allows to serialize the class
- `deserialize` - A `classmethod` that will create a new instance from binary data
- `__eq__`      - Allows comparsion between different instances
- `__str__`     - Converts struct to a string
- `__iter__`    - Allows converting the class into a `dict`
- `size_in_bytes`   - Pretty straightforward


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

We can also use `args`/`kwargs` initialization for nested class, for even more control
```python
magical_buf1 = MagicalBufferWithSize(magic=0xdeadbeef, data=[5, range(5)])
magical_buf2 = MagicalBufferWithSize(magic=0xdeadbeef, data={'buf': range(2)})
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

If we want to change the endianness of exsiting class without redefining it, we can simply use:
```python
@big_endian
class BEMagicalBufferWithSize(MagicalBufferWithSize):
    magic: uint32_t
    data: BufferWithSize
```
Both `magic` and `data` will be converted to Big endian versions in this example.

### Custom implementations
We can always add a custom implementation to override the code generation:
```python
@binary_struct
class BufferWithSize:
    size: uint32_t
    data: [uint8_t, 8]

    def __bytes__(self):
        return b'Hello world' + self._bs_bytes()
```
This implementation will greet the user before giving him the serialized data, VERY useful.

Note that we used the class's `_bs_bytes` in order to call the generated function. If a function is generated in
the class decleration.

## Implementation
### Abstract
In binary_structs, for each class we decorate The class will be reconstructed and a new parent class will be added, named `BinaryStruct`. `BinaryStruct` inherits from `BinaryField` interface.
The generated code will be created for `BinaryStruct`, and the original class will be duplicated and recreated
with a new parent class.

### BinaryField
Each field that is being used in a `BinaryStruct` must inherit from `BinaryField` class, and each class that is being processed
by `@binary_struct` decorator will have `BinaryField` added to its inheritance tree.

### TypedBuffer and BinaryBuffer
These types are generated for each definition using the `new_binary_buffer`/`new_typed_buffer` syntax.

When using the buffer syntax (`data: [uint8_t, 32]` or `data: [uint8_t]`), the decorator will create an instance for
a `BinaryBuffer` and a `TypedBuffer` respectively with the correct type.

A `TypedBuffer`, as the name suggests, enforces that each parameter that is being
passed to it has the same type as the underlying type it was declared with.
`TypedBuffer` implements the `BinaryField` interface

A `BinaryBuffer` is a `TypedBuffer` that also enforces size, and it will create empty instances of its underlying type when
it is created

# Dev
## Known issues
### Endianness conversion [WIP]
Endianness converstion had 2 main issues:
- A horrible amount of overhead was added:

    This happens because of the way `@binary_struct` decorator operates.
    It generates all the the code from the annotations types, that might have the wrong endianness.
    The endian decorators change the annotations recursively - for primitive types the use a pre-defined conversion
    dictionary, and for `BinaryFields` they rebuild the classes the same way `@binary_struct` would.
    This means that every class is being built twice!

- Nested `BinaryFields` cannot be referenced easily:

    Consider the following:
    ```python
    @binary_struct
    class Base:
        num: uint32_t

    @big_endian
    class Nested:
        base: Base
        num2: uint8_t
    ```
    After converting `Nested` to big endian, we will need to be able to initialize `Base`. But, `Base` cannot initialize
    `Nested` class, because `Base` was converted to a big-endian version of itself, and `@binary_structs` enforce types that are
    being passed to it.
    The only way to reference the converted `Base` class is:
    ```python
    # This gets worse when there are multiple inheritance levels
    NewBase = Nested.__annotations__['base'][0]
    ```

#### Attempted solution
As suggested, a caching system was added to handle the overhead, and performence skyrocketed since starting to use it.
Unfortunately, this got very complex after implementing default value support.

The nested fields issue have now 2 elegant solutions:
- Referencing using the `BinaryStruct`:
    We can reference converted structs using the class:
    ```python
    a = Nested(Nested.base(5), 3)
    ```
- Using the `args`/`kwargs` initialization
    ```python3
    a = Nested(base=[5], 3)
    ```

## Future ideas
- [ ] Github actions support
- [ ] Convertions support (`.h` files, `.so`, `ctypes`)
- [ ] Make the struct sequential in memory
- [ ] Hashing support
- [ ] Use sphinx docs
- [ ] Add `/` operator between `binary_struct` instances
- [ ] Add control over individual fields
- [ ] A `@binary_union` decorator
- [ ] Readonly classes/fields
- [ ] Redesign endianness convertions
