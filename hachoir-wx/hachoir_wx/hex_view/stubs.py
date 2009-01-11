# -*- coding: utf-8 -*-

from hachoir_core.tools import alignValue
from hachoir_core.error import warning

def byte_addr(bit):
    return bit // 8

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

def to_ascii(data, width=None):
    ascii_data = ''
    for i in xrange(len(data)):
        if 32 <= ord(data[i]) <= 126:
            ascii_data += data[i]
        else:
            ascii_data += '.'
        if width and (i+1)%width==0:
            ascii_data += '\n'

    return ascii_data

def calc_byte_range(start, end):
    return byte_addr(start), byte_addr(alignValue(end, 8))

def calc_ascii_range(start, end, width=None):
    aligned_start, aligned_end = calc_byte_range(start, end)

    char_start = calc_ascii_pos(aligned_start, width)
    char_end = calc_ascii_pos(aligned_end, width)

    return char_start, char_end

def calc_ascii_pos(byte_pos, width=None):
    if width:
        line_offset = (byte_pos // width) * (width+1)
        return line_offset + (byte_pos % width)
    return byte_pos

def calc_char_range(start, end, width=None):
    aligned_start, aligned_end = calc_byte_range(start, end)

    char_start = calc_char_pos(aligned_start)
    char_end = calc_char_pos(aligned_end)-1

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
    return offset // page_width

def get_page_offset(offset, page_width):
    return get_page_num(offset, page_width) * page_width

def calc_field_mark(offset, field):
    start = field._getAbsoluteAddress() - bit_addr(offset)
    size = field._getSize()
    return (start, size)
