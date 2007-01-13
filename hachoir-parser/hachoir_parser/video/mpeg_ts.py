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
        yield UInt8(self, "sync", 8, text_handler=hexadecimal)
        if self["sync"].value != 0x47:
            raise ParserError("MPEG-2 TS: Invalid synchronization byte")
        yield Bit(self, "has_error")
        yield Bit(self, "payload_unit_start")
        yield Bit(self, "priority")
        yield Bits(self, "pid", 13, text_handler=hexadecimal)
        yield Bits(self, "scrambling_control", 2)

        yield Bit(self, "has_adaptation")
        yield Bit(self, "has_payload")

        yield Bits(self, "counter", 4)
        yield RawBytes(self, "payload", 184)
        if self["has_error"].value:
            yield RawBytes(self, "error_correction", 16)

    def createDescription(self):
        text = "Packet: PID %s" % self["pid"].display
        if self["payload_unit_start"].value:
            text += ", start of payload"
        return text

    def isValid(self):
        if not self["has_payload"].value and not self["has_adaptation"].value:
            return u"No payload and no adaptation"
        return ""

class MPEG_TS(Parser):
    tags = {
        "file_ext": ("ts",),
        "min_size": 188*8,
        "description": u"MPEG-2 Transport Stream"
    }
    endian = BIG_ENDIAN

    def validate(self):
        sync = self.stream.searchBytes("\x47", 0, 204*8)
        if sync is None:
            return "Unable to find synchronization byte"
        err = self["packet[0]"].isValid()
        if err:
            return "Packet #0 is invalid: %s" % err
        return True

    def createFields(self):
        sync = self.stream.searchBytes("\x47", 0, 204*8)
        if sync is None:
            raise ParserError("Unable to find synchronization byte")
        elif sync:
            yield RawBytes(self, "incomplete_packet", sync//8)
        while not self.eof:
            yield Packet(self, "packet[]")

