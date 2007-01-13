"""
MPEG-2 Transport Stream parser.

Author: Victor Stinner
Creation date: 13 january 2007
"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    UInt8, Bit, Bits, RawBytes)
from hachoir_core.endian import BIG_ENDIAN
from hachoir_core.text_handler import hexadecimal

class Packet(FieldSet):
    def __init__(self, *args):
        FieldSet.__init__(self, *args)
        if self["has_error"].value:
            self._size = 204*8
        else:
            self._size = 188*8

    def createFields(self):
        yield Bits(self, "sync", 8)
        if self["sync"].value != 0x47:
            raise ParserError("MPEG-2 TS: Invalid synchronization byte")
        yield Bit(self, "has_error")
        yield Bit(self, "payload_unistart")
        yield Bit(self, "priority")
        yield Bits(self, "pid", 13)
        yield Bits(self, "scrambling_control", 2)
        yield Bits(self, "adaptation_field_control", 2)
        yield Bits(self, "counter", 4)
        yield RawBytes(self, "payload", 184)
        if self["has_error"].value:
            yield RawBytes(self, "error_correction", 16)

class MPEG_TS(Parser):
    tags = {
        "file_ext": ("ts",),
        "min_size": 188*8,
        "description": u"MPEG-2 Transport Stream"
    }
    endian = BIG_ENDIAN

    def validate(self):
        return True

    def createFields(self):
        while not self.eof:
            yield Packet(self, "packet[]")

