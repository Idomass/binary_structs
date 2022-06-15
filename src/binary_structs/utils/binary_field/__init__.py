from sys import byteorder as __byteorder

from binary_structs.utils.binary_field.base_fields import       \
    PrimitiveTypeField, Endianness,                             \
    be_int16_t, be_int32_t, be_int64_t,                         \
    be_uint16_t, be_uint32_t, be_uint64_t,                      \
    le_int8_t, le_int16_t, le_int32_t, le_int64_t,              \
    le_uint8_t, le_uint16_t, le_uint32_t, le_uint64_t


byte        = le_uint8_t
uint8_t     = le_uint8_t
be_uint8_t  = le_uint8_t
be_int8_t   = le_int8_t
int8_t      = le_int8_t


if __byteorder == 'little':
    from binary_structs.utils.binary_field.base_fields import le_int16_t   as int16_t
    from binary_structs.utils.binary_field.base_fields import le_uint16_t  as uint16_t
    from binary_structs.utils.binary_field.base_fields import le_int32_t   as int32_t
    from binary_structs.utils.binary_field.base_fields import le_uint32_t  as uint32_t
    from binary_structs.utils.binary_field.base_fields import le_int64_t   as int64_t
    from binary_structs.utils.binary_field.base_fields import le_uint64_t  as uint64_t

else:
    from binary_structs.utils.binary_field.base_fields import be_int16_t   as int16_t
    from binary_structs.utils.binary_field.base_fields import be_uint16_t  as uint16_t
    from binary_structs.utils.binary_field.base_fields import be_int32_t   as int32_t
    from binary_structs.utils.binary_field.base_fields import be_uint32_t  as uint32_t
    from binary_structs.utils.binary_field.base_fields import be_int64_t   as int64_t
    from binary_structs.utils.binary_field.base_fields import be_uint64_t  as uint64_t
