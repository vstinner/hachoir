"""
Microsoft Office documents parser.

Informations:
* wordole.c of AntiWord program (v0.35)
  Copyright (C) 1998-2003 A.J. van Os
  Released under GNU GPL
  http://www.winfield.demon.nl/
* File gsf-infile-msole.c of libgsf library (v1.14.0)
  Copyright (C) 2002-2004 Jody Goldberg (jody@gnome.org)
  Released under GNU LGPL 2.1
  http://freshmeat.net/projects/libgsf/
* PDF from AAF Association
  Copyright (C) 2004 AAF Association
  Copyright (C) 1991-2003 Microsoft Corporation
  http://www.aafassociation.org/html/specs/aafcontainerspec-v1.0.1.pdf

Author: Victor Stinner
Creation: 8 january 2005
"""

from hachoir_parser import HachoirParser
from hachoir_core.field import (FieldSet, ParserError,
    RootSeekableFieldSet, SeekableFieldSet,
    UInt8, UInt16, UInt32, UInt64, TimestampWin64, Enum,
    Bytes, RawBytes, NullBytes,
    String)
from hachoir_core.text_handler import hexadecimal
from hachoir_core.tools import humanFilesize
from hachoir_core.endian import LITTLE_ENDIAN
from hachoir_parser.common.win32 import GUID

# Number of items in DIFAT
NB_DIFAT = 109

class SECT(UInt32):
    END_OF_CHAIN = 0xFFFFFFFE
    UNUSED = 0xFFFFFFFF

    special_value_name = {
        0xFFFFFFFC: "DIFAT sector (in a FAT)",
        0xFFFFFFFD: "FAT sector (in a FAT)",
        END_OF_CHAIN: "end of a chain",
        UNUSED: "none"
    }

    def __init__(self, parent, name, description=None):
        UInt32.__init__(self, parent, name, \
            text_handler=self._processDisplay, description=description)

    def _processDisplay(self, field):
        val = field.value
        return SECT.special_value_name.get(val, str(val))

class Property(FieldSet):
    TYPE_NAME = {
        1: "storage",
        2: "stream",
        3: "ILockBytes",
        4: "IPropertyStorage",
        5: "root"
    }
    DECORATOR_NAME = {
        0: "red",
        1: "black",
    }
    static_size = 128 * 8

    def createFields(self):
        yield String(self, "name", 64, charset="UTF-16-LE", strip="\0")
        yield UInt16(self, "namelen", "Length of the name")
        yield Enum(UInt8(self, "type", "Property type"), self.TYPE_NAME)
        yield Enum(UInt8(self, "decorator", "Decorator"), self.DECORATOR_NAME)
        yield SECT(self, "left")
        yield SECT(self, "right")
        yield SECT(self, "child")
        yield GUID(self, "clsid", "CLSID of this storage")
        yield RawBytes(self, "flags", 4, "User flags")
        yield TimestampWin64(self, "creation", "Creation timestamp")
        yield TimestampWin64(self, "lastmod", "Modify timestamp")
        yield SECT(self, "start", "Starting SECT of the stream")
        yield UInt64(self, "size", "Size in bytes")

    def createDescription(self):
        name = self["name"].display
        size = self["size"].value
        size = humanFilesize(size)
        return "Property: %s (%s)" % (name, size)

class Header(FieldSet):
    static_size = 68 * 8
    def createFields(self):
        yield GUID(self, "clsid", "16 bytes GUID used by some apps")
        yield UInt16(self, "ver_min", "Minor version")
        yield UInt16(self, "ver_maj", "Minor version")
        if self["ver_maj"].value not in (3, 4):
            raise ParserError("Unknown Header version!")
        yield UInt16(self, "endian", "Endian (0xFFFE for Intel)", text_handler=hexadecimal)
        yield UInt16(self, "bb_shift", "Log, base 2, of the big block size")
        if not(6 <= self["bb_shift"].value < 31):
            raise ParserError("Invalid (log 2 of) big block size")
        yield UInt16(self, "sb_shift", "Log, base 2, of the small block size")
        if self["bb_shift"].value < self["sb_shift"].value:
            raise ParserError("Small block size is bigger than big block size!")
        yield NullBytes(self, "reserverd[]", 6, "(reserved)")
        yield UInt32(self, "csectdir", "Number of SECTs in directory chain for 4 KB sectors (version 4)")
        yield UInt32(self, "bb_count", "Number of Big Block Depot blocks")
        yield SECT(self, "bb_start", "Root start block")
        yield RawBytes(self, "transaction", 4, "Signature used for transactions (must be zero)")
        yield UInt32(self, "threshold", "Maximum size for a mini stream (typically 4096 bytes)")
        yield SECT(self, "sb_start", "Small Block Depot start block")
        yield UInt32(self, "sb_count")
        yield SECT(self, "db_start", "First block of DIFAT")
        yield UInt32(self, "db_count", "Number of SECTs in DIFAT")

# Header (ole_id, header, difat) size in bytes
HEADER_SIZE = 64 + Header.static_size + NB_DIFAT * SECT.static_size

class SectFat(FieldSet):
    def __init__(self, parent, name, start, count, description=None):
        FieldSet.__init__(self, parent, name, description, size=count*32)
        self.count = count
        self.start = start

    def createFields(self):
        for i in xrange(self.start, self.start + self.count):
            yield SECT(self, "index[%u]" % i)

class OLE2_File(HachoirParser, RootSeekableFieldSet):
    tags = {
        "id": "ole2",
        "category": "misc",
        "file_ext": (
            "doc", "dot",                # Microsoft Word
            "ppt", "ppz", "pps", "pot",  # Microsoft Powerpoint
            "xls", "xla"),               # Microsoft Excel
        "mime": (
            "application/msword",
            "application/msexcel",
            "application/mspowerpoint"),
        "min_size": 512*8,
        "description": "Microsoft Office document",
        "magic": (("\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1", 0),),
    }
    endian = LITTLE_ENDIAN

    def __init__(self, stream, **args):
        RootSeekableFieldSet.__init__(self, None, "root", stream, None, stream.askSize(self))
        HachoirParser.__init__(self, stream, **args)

    def validate(self):
        if self["ole_id"].value != "\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1":
            return "Invalid magic"
        return True

    def createFields(self):
        # Signature
        yield Bytes(self, "ole_id", 8, "OLE object signature")

        header = Header(self, "header")
        yield header

        # Configure values
        if header["ver_maj"].value == 3:
            self.sector_size = 512*8
        else: # major version is 4
            self.sector_size = 4096*8
        self.fat_count = header["bb_count"].value
        sector = (SECT.static_size // 8)
        self.items_per_bbfat = (1 << header["bb_shift"].value) / sector

        # Read DIFAT (one level of indirection)
        yield SectFat(self, "difat", 0, NB_DIFAT, "Double Indirection FAT")

        # Read FAT (one level of indirection)
        for field in self.readBFAT():
            yield field

        # Read SFAT
        for field in self.readSFAT():
            yield field

        # Read properties
        chain = self.getFatChain(self.bb_fat, self["header/bb_start"].value)
        prop_per_sector = self.sector_size // Property.static_size
        for block in chain:
            self.seekBlock(block)
            for index in xrange(prop_per_sector):
                yield Property(self, "property[]")

    def getFatChain(self, fat, block):
        while block != SECT.END_OF_CHAIN:
            yield block
            index = block // self.items_per_bbfat
            block = fat[index]["index[%u]" % block].value

    def readBFAT(self):
        self.bb_fat = []
        start = 0
        count = self.items_per_bbfat
        for index, block in enumerate(self.array("difat/index")):
            block = block.value
            if block == SECT.UNUSED:
                break

            desc = "FAT %u/%u at block %u" % \
                (1+index, self["header/bb_count"].value, block)

            self.seekBlock(block)
            field = SectFat(self, "bbfat[]", start, count, desc)
            yield field
            self.bb_fat.append(field)

            start += count

    def readSFAT(self):
        chain = self.getFatChain(self.bb_fat, self["header/sb_start"].value)
        start = 0
        self.ss_fat = []
        count = self.items_per_bbfat
        for index, block in enumerate(chain):
            self.seekBlock(block)
            field = SectFat(self, "sfat[]", \
                start, count, \
                "SFAT %u/%u at block %u" % \
                (1+index, self["header/bb_count"].value, block))
            yield field
            self.ss_fat.append(field)
            start += count

    def seekBlock(self, block):
        self.seekBit(HEADER_SIZE + block * self.sector_size)

