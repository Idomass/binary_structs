"""
A typed buffer, is a binary buffer that it's size is determined on initialization
"""

from binary_structs.utils.buffers.binary_buffer import BufferField, new_binary_buffer


def new_typed_buffer(underlying_type: type) -> type:
    """
    Creates a new typed buffer with the given element
    """

    class TypedBuffer(BufferField):
        _is_binary_field = True
        element_type = underlying_type
        static_size = 0

        def __new__(self, *args):
            """
            Create a new binary buffer using the given iterable in *args
            """

            new_cls = type(f'TypedBuffer_{underlying_type.__name__}_{len(args)}',
                        (new_binary_buffer(underlying_type, len(args)), ),
                        {})

            return new_cls(*args)

        @classmethod
        def deserialize(cls, buf) -> type:
            num_of_elements = len(buf) // underlying_type.static_size

            new_cls = type(f'TypedBuffer_{underlying_type.__name__}_{num_of_elements}',
                        (new_binary_buffer(underlying_type, num_of_elements), ),
                        {})

            return new_cls.deserialize(buf)


    return TypedBuffer
