# -*- coding: utf-8 -*-

def format_addr_dec(addr):
    return "%08d.%01d" % divmod(addr, 8)

def format_addr_hex(addr):
    return "%08x.%01d" % divmod(addr, 8)

def format_size(size):
    return "%08u.%01d" % divmod(size, 8)

def format_data(field):
    data = ''

    if field.hasValue():
        data = field.display

    return data

def format_name(field):
    name = field._getName()
    if field.is_field_set:
        name += '/'

    return name

def format_desc(field):
    if field.description:
        return unicode(field.description)
    return u''

