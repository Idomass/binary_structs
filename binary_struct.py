"""
This file has the code for the binary_struct decorator.

Binary struct is essanitialy a c-like struct, with the comforts that come with python.
The library supports serialization and deserialization of objects, with a clear and clean API.s

Basic API:
@binary_struct
class BufferWithSize:
    size: ctypes.c_uint32
    buf: [ctypes.c_uint8, 64]
"""
import sys
import string
import random
import logging

from utils.binary_field import BinaryField
from buffers.binary_buffer import BinaryBuffer as _binary_buffer
from buffers.typed_buffer import TypedBuffer as _typed_buffer


def _create_fn(name, local_params: list[str] = [], lines: list[str] = ['pass'], globals: dict = {}):
    """
    This function receives a name for the function, and returns a
    function with the given locals and globals
    """

    lines_as_str = '\n    ' + '\n    '.join(lines)
    fn_text = f'def {name}({", ".join(local_params)}):{lines_as_str}'
    logging.debug(f'Created new function:\n{fn_text}')

    ns = {}
    exec(fn_text, globals, ns)

    return ns[name]

def _insert_type_to_globals(kind: type, globals: dict = {}) -> str:
    """
    Inserts the given type into the namespace
    Returns the temporary name
    """

    rand_str = ''.join(random.choice(string.ascii_letters) for _ in range(16))
    name = f'__{rand_str}BINARY_STRUCT_TMP{kind.__name__}'

    if globals.get(name, False):
        raise AttributeError('Temporary variable name already exist!')

    globals[name] = kind

    return name

def _init_var(name: str, kind: type or list[type, int], globals: dict = {}) -> list[str]:
    """
    Helper function for _create_init_fn that helps to init a variable.
    Returns the python code that is required to init that variable.
    """

    logging.debug(f'Creating init var {name} with type {kind}')

    # TODO match syntax asap
    if isinstance(kind, list):
        if len(kind) == 2:
            # BinaryBuffer
            kind, size = kind
            type_name = _insert_type_to_globals(kind, globals)

            init_var =  [f'if {size} < len({name}):']
            init_var += [f'   raise TypeError("list is bigger than given size!")']
            init_var += [f'self.{name} = _binary_buffer({type_name}, {size}, {name})']

        elif len(kind) == 1:
            # TypedBuffer
            kind = kind[0]
            type_name = _insert_type_to_globals(kind, globals)

            init_var = [f'self.{name} = _typed_buffer({type_name}, {name})']

        else:
            raise ValueError('Buffer has wrong number of parameters!')

    else:

        type_name = _insert_type_to_globals(kind, globals)

        init_var =  [f'try:']
        init_var += [f'    self.{name} = {type_name}({name})']
        init_var += [f'except (TypeError, ValueError):']
        init_var += [f'    if not isinstance({name}, {type_name}):']
        init_var += [f'        raise TypeError("Got invalid type for {name}")']
        init_var += [f'    self.{name} = {name}']

    # Make sure kind implements BinaryField
    if not BinaryField.is_binary_field(kind):
        raise TypeError('All fields must implement BinaryField!')

    return init_var

def _create_init_fn(attributes: dict = {}, globals: dict = {}) -> str:
    """
    Create init function and return it.
    The created function will set the class annotations
    """

    init_txt = []
    for name, kind in attributes.items():
        init_txt.extend(_init_var(name, kind, globals))

    return _create_fn('__init__', ['self'] + list(attributes.keys()), init_txt or ['pass'], globals)

def _create_bytes_fn(attributes: dict = {}, globals: dict = {}) -> str:
    """
    Create bytes function and return it.
    The created function will call bytes() on every class member
    """

    lines = ['buf = b""']
    for attr in attributes.keys():
        lines += [f'buf += bytes(self.{attr})']

    lines += ['return buf']

    return _create_fn('__bytes__', ['self'], lines, globals)

def _process_class(cls=None):
    """
    This function is the main logic unit, it parses the different parameters and
    returns a processed class
    """

    logging.debug(f'Processing class {cls.__name__}')

    globals = sys.modules[cls.__module__].__dict__.copy()
    globals['_binary_buffer'] = _binary_buffer
    globals['_typed_buffer'] = _typed_buffer

    annotations = cls.__dict__.get('__annotations__', {})

    init_fn = _create_init_fn(annotations, globals)
    setattr(cls, '__init__', init_fn)

    bytes_fn = _create_bytes_fn(annotations, globals)
    setattr(cls, '__bytes__', bytes_fn)

    # TODO placeholders, implement it
    deserialize_fn = _create_fn('deserialize', ['self'], ['pass'], globals)
    setattr(cls, 'deserialize', deserialize_fn)

    @property
    def empty(self):
        return 5

    setattr(cls, 'size_in_bytes', empty)

    return cls

def binary_struct(cls=None):
    """
    Return the class that was passed with auto-implemented dunder methods such as bytes,
    and a new c'tor for the class
    """

    def wrap(cls):
        return _process_class(cls)

    if cls is None:
        return wrap

    return wrap(cls)
