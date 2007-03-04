"""
Microsoft's HTML Help (.chm) format

Author: Victor Stinner
Creation date: 2007-03-04
"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet,
    Enum, String, Int32, UInt32, UInt64, DateTimeMSDOS32)
from hachoir_core.endian import LITTLE_ENDIAN
from hachoir_parser.common.win32 import GUID
from hachoir_parser.common.win32_lang_id import LANGUAGE_ID
from hachoir_core.text_handler import hexadecimal, humanFilesize

class SectionTable(FieldSet):
    static_size = 128
    def createFields(self):
        yield UInt64(self, "offset")
        yield UInt64(self, "size", text_handler=humanFilesize)

class HeaderSection0(FieldSet):
    static_size = 24*8
    def createFields(self):
        yield UInt32(self, "unknown[]", "0x01FE", text_handler=hexadecimal)
        yield UInt32(self, "unknown[]", "0x0", text_handler=hexadecimal)
        yield UInt64(self, "file_size", text_handler=humanFilesize)
        yield UInt32(self, "unknown[]", "0x0", text_handler=hexadecimal)
        yield UInt32(self, "unknown[]", "0x0", text_handler=hexadecimal)

class HeaderSection1(FieldSet):
    def __init__(self, *args):
        FieldSet.__init__(self, *args)
        self._size = self["size"].value * 8

    def createFields(self):
        yield String(self, "magic", 4, "ITSP", charset="ASCII")
        yield UInt32(self, "version", "Version (=1)")
        yield UInt32(self, "size", "Length (in bytes) of the directory header (84)", text_handler=humanFilesize)
        yield UInt32(self, "unknown[]", "0x0a")
        yield UInt32(self, "chunk_size", "Directory chunk size", text_handler=humanFilesize)
        yield UInt32(self, "density", "Density of quickref section, usually 2")
        yield UInt32(self, "depth", "Depth of the index tree")
        yield UInt32(self, "chunk_nb", "Chunk number of root index chunk")
        yield UInt32(self, "first_pmgl", "Chunk number of first PMGL (listing) chunk")
        yield UInt32(self, "last_pmgl", "Chunk number of last PMGL (listing) chunk")
        yield Int32(self, "unknown[]", "-1")
        yield UInt32(self, "nb_dir_chunk", "Number of directory chunks (total)")
        yield Enum(UInt32(self, "lang_id", "Windows language ID"), LANGUAGE_ID)
        yield GUID(self, "guid", "{5D02926A-212E-11D0-9DF9-00A0C922E6EC}")
        yield UInt32(self, "size2", "Same value than size", text_handler=humanFilesize)
        yield Int32(self, "unknown[]", "-1")
        yield Int32(self, "unknown[]", "-1")
        yield Int32(self, "unknown[]", "-1")

class ListingChunk(FieldSet):
    def createFields(self):
        yield String(self, "magic", 4, "PMGL", charset="ASCII")
        yield UInt32(self, "free_space", "Length of free space and/or quickref area at end of directory chunk", text_handler=humanFilesize)
        yield UInt32(self, "zero", "Always 0")
        yield Int32(self, "previous", "Chunk number of previous listing chunk")
        yield Int32(self, "next", "Chunk number of previous listing chunk")


class ChmFile(Parser):
    tags = {
        "id": "chm",
        "category": "misc",
        "file_ext": ("chm",),
        "min_size": 4*8,
        "magic": (("ITSF\3\0\0\0", 0),),
        "description": "Microsoft's HTML Help (.chm)",
    }
    endian = LITTLE_ENDIAN

    def validate(self):
        if self.stream.readBytes(0, 4) != "ITSF":
            return "Invalid magic"
        if self["version"].value != 3:
            return "Invalid version"
        return True

    def createFields(self):
        yield String(self, "magic", 4, charset="ASCII")
        yield UInt32(self, "version")
        yield UInt32(self, "header_size", "Total header length (in bytes)")
        yield UInt32(self, "one")
        yield DateTimeMSDOS32(self, "timestamp")
        yield Enum(UInt32(self, "lang_id", "Windows Language ID"), LANGUAGE_ID)
        yield GUID(self, "guid1", "{7C01FD10-7BAA-11D0-9E0C-00A0-C922-E6EC}")
        yield GUID(self, "guid2", "{7C01FD11-7BAA-11D0-9E0C-00A0-C922-E6EC}")

        # Read section table
        for index in xrange(2):
            yield SectionTable(self, "section_table[]")

        # Read section #0
        padding = self.seekByte(self["section_table[0]/offset"].value)
        if padding:
            yield padding
        yield HeaderSection0(self, "section0")

        # Read section #1
        padding = self.seekByte(self["section_table[1]/offset"].value)
        if padding:
            yield padding
        yield HeaderSection1(self, "section1")

        yield ListingChunk(self, "listing_chunk")

    def createContentSize(self):
        return self["section0/file_size"].value * 8

