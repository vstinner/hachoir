#
# some stubs that could be in hachoir-core.
#

from hachoir.stream.input import FileFromInputStream
from shutil import copyfileobj


def field_index(field_set, field):
    return field_set._fields.index(field.name)


def field_from_index(field_set, index):
    return field_set._fields.values[index]


def has_static_size(type):
    return isinstance(type.static_size, int)


def can_convert(from_field, to_type):
    if has_static_size(from_field) and has_static_size(to_type):
        return from_field.static_size == to_type.static_size
    elif has_static_size(to_type):
        return from_field.size == to_type.static_size
    else:
        return False


def field_type_name(field):
    return field.__class__.__name__


def convert_size(from_field, to_type):
    if not(('Byte' in field_type_name(from_field)) ^ ('Byte' in to_type.__name__)):
        return from_field.size
    elif 'Byte' in field_type_name(from_field):
        return from_field.size * 8
    else:
        return from_field.size // 8


def save_substream_to_disk(field, dest_path):
    dest_stream = open(dest_path, 'wb')
    f = FileFromInputStream(field.getSubIStream())
    copyfileobj(f, dest_stream)
    dest_stream.close()
