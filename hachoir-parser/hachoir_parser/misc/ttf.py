"""
TrueType Font parser.

Author: Victor Stinner
Creation date: 2007-02-08
"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet,
    UInt16, UInt32, String, RawBytes)
from hachoir_core.endian import BIG_ENDIAN
from hachoir_core.text_handler import hexadecimal, humanFilesize

class TableEntry(FieldSet):
    def createFields(self):
        yield String(self, "tag", 4)
        yield UInt32(self, "checksum", text_handler=hexadecimal)
        yield UInt32(self, "offset")
        yield UInt32(self, "size", text_handler=humanFilesize)

    def createDescription(self):
         return "Table entry: %s (%s)" % (self["tag"].display, self["size"].display)

class Table(FieldSet):
    def __init__(self, parent, name, table, **kw):
        FieldSet.__init__(self, parent, name, **kw)
        self.table = table

    def createFields(self):
        yield RawBytes(self, name, self.size//8)

    def createDescription(self):
        return "Table (%s)" % self.table.path

class TrueTypeFontFile(Parser):
    endian = BIG_ENDIAN
    tags = {
        "id": "ttf",
        "category": "misc",
        "file_ext": ("ttf",),
        "min_size": 10*8, # FIXME
        "description": "TrueType font",
    }

    def validate(self):
        return True

    def createFields(self):
        yield UInt16(self, "maj_ver", "Major version")
        yield UInt16(self, "min_ver", "Minor version")
        yield UInt16(self, "nb_table")
        yield UInt16(self, "search_range")
        yield UInt16(self, "entry_selector")
        yield UInt16(self, "range_shift")
        tables = []
        for index in xrange(self["nb_table"].value):
            table = TableEntry(self, "table_entry[]")
            yield table
            tables.append(table)
        tables.sort(key=lambda field: field["offset"].value)
        for table in tables:
            padding = self.seekByte(table["offset"].value, null=True)
            if padding:
                yield padding
            size = table["size"].value
            if size:
                name = table["tag"].value.replace("/", "_").lower().strip(" ")
                yield Table(self, name, table, size=size*8)
        padding = self.seekBit(self.size, null=True)
        if padding:
            yield padding

