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
from buffer import Buffer as _binary_buffer


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

def _init_var(name: str, kind: type or List[type, int]) -> List[str]:
    """
    Helper function for _create_init_fn that helps to init a variable.
    Returns the python code that is required to init that variable.
    """

    init_var = []
    if isinstance(kind, list):
        underlying_type, size = kind

        type_name =  underlying_type if underlying_type.__module__ == 'builtins' \
                     else f'{underlying_type.__module__}.{underlying_type.__name__}'

        # TODO: try to replace it with a function that its text will be copied instead
        init_var.append(f'if {size} < len({name}):')
        init_var.append(f'   raise TypeError("List is bigger than given size!")')
        init_var.append(f'self.{name} = _binary_buffer({type_name}, {size}, {name})')

    else:
        module_name =  '' if kind.__module__ == 'builtins' else f'{kind.__module__}.'
        init_var = [f'self.{name} = {module_name}{kind.__name__}({name})']

    return init_var

def _create_init_fn(attributes: dict = {}, globals: dict = {}):
    """
    Create init function and return it.
    The created function will set the class annotations
    """

    init_txt = []
    for name, kind in attributes.items():
        init_txt.extend(_init_var(name, kind))

    return _create_fn('__init__', ['self'] + list(attributes.keys()), init_txt, globals)

def _process_class(cls=None):
    """
    This function is the main logic unit, it parses the different parameters and
    returns a processed class
    """

    globals = sys.modules[cls.__module__].__dict__.copy()
    globals['_binary_buffer'] = _binary_buffer

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
