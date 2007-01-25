# -*- coding: utf-8 -*-

from hachoir_core import field as field_module
from hachoir_wx.field_view.stubs import has_static_size, convert_size

def split_field(field, split_pos, split_name, split_t, size_func):
    split_name += '[]'

    subfields = [
        split_t(field._parent, split_name, split_pos),
        split_t(field._parent, split_name, size_func(field) - split_pos)
        ]

    field._parent.replaceField(field._getName(), subfields)

def convert_field(field, new_type_name):
    field_set = field._parent
    new_type = getattr(field_module, new_type_name)

    if has_static_size(new_type):
        new_field = new_type(field_set, field._getName(), field._getDescription())
    else:
        new_field = new_type(field_set, field._getName(), convert_size(field, new_type), field._getDescription())

    field_set.replaceField(field._getName(), [new_field])
