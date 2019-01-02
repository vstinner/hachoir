from hachoir import field as field_module
from hachoir.wx.field_view.stubs import has_static_size, convert_size


def split_field(field, split_pos, split_name, split_t, size_func):
    split_name += '[]'

    subfields = [
        split_t(field._parent, split_name, split_pos),
        split_t(field._parent, split_name, size_func(field) - split_pos)]

    field._parent.replaceField(field.name, subfields)


def convert_field(field, new_type_name):
    field_set = field._parent
    new_type = getattr(field_module, new_type_name)

    if has_static_size(new_type):
        new_field = new_type(field_set, field.name, field._getDescription())
    else:
        new_field = new_type(field_set, field.name, convert_size(field, new_type), field._getDescription())

    field_set.replaceField(field.name, [new_field])
