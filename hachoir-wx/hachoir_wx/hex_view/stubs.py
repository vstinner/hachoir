# -*- coding: utf-8 -*-

from hachoir_core.tools import alignValue
from math import floor
from hachoir_core.error import warning

def byte_addr(bit):
    return bit / 8

def bit_addr(byte):
    return byte * 8

def get_file_size(file):
    pos = file.tell()
    file.seek(0, 2)
    size = file.tell()
    file.seek(pos)

    return size

def to_hex(data, width=None):
    hex_data = ''
    for i in xrange(len(data)):
        hex_data += "%02x" % ord(data[i])
        if width and (i+1)%width==0:
            hex_data += '\n'
        else:
            hex_data += ' '

    return hex_data.rstrip(' ')

def calc_char_range(start, end):
    aligned_start = byte_addr(start)
    aligned_end = byte_addr(alignValue(end, 8))

    char_start = calc_char_pos(aligned_start)
    char_end = calc_char_pos(aligned_end)

    return char_start, char_end

def calc_char_pos(byte_pos):
    return byte_pos * 3

def clamp_range(what, begin, end):
    what = max(what, begin)
    what = min(what, end)
    return what

def safe_seek(file, where):
    try:
        where = max(0, where)
        file.seek(where)
    except IOError, err:
        warning("Cannot seek to %s: %s" % (where, unicode(err)))
        return False

    return True

def get_page_num(offset, page_width):
    return int(floor(offset / float(page_width)))

def get_page_offset(offset, page_width):
    return get_page_num(offset, page_width) * page_width

def calc_field_mark(offset, field):
    start = field._getAbsoluteAddress() - bit_addr(offset)
    size = field._getSize()
    return (start, size)
