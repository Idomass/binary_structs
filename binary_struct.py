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
import logging
from typing import List


def _create_fn(name, local_params: List[str] = [], lines: List[str] = ['pass'], globals: dict = {}):
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

def _create_init_fn(attributes: dict = {}, globals: dict = {}):
    """
    Create init function and return it.
    The created function will set the class annotations
    """

    init_txt = []
    for name, kind in attributes.items():
        module_name =  '' if kind.__module__ == 'builtins' else f'{kind.__module__}.'
        init_txt.append(f'self.{name} = {module_name}{kind.__name__}({name})')

    return _create_fn('__init__', ['self'] + list(attributes.keys()), init_txt, globals)

def _process_class(cls=None):
    """
    This function is the main logic unit, it parses the different parameters and
    returns a processed class
    """

    globals = sys.modules[cls.__module__].__dict__
    if hasattr(cls, '__annotations__'):
        init_fn = _create_init_fn(cls.__annotations__, globals)

        setattr(cls, '__init__', init_fn)

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
