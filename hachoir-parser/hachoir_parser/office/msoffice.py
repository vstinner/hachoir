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

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    UInt8, UInt16, UInt32, UInt64, Enum,
    Bytes, RawBytes, NullBytes,
    String, PascalString32)
from hachoir_core.text_handler import hexadecimal, timestampWin64
from hachoir_core.tools import humanFilesize
from hachoir_core.endian import LITTLE_ENDIAN
from hachoir_parser.common.win32 import GUID

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
    type_name = {
        1: "storage",
        2: "stream",
        3: "ILockBytes",
        4: "IPropertyStorage",
        5: "root"
    }
    decorator_name = {
        0: "red",
        1: "black",
    }
    static_size = 128 * 8

    def createDescription(self):
        name = self["name"].display
        size = self["size_hi"].value * (1 << 32) + self["size_lo"].value
        size = humanFilesize(size)
        return "Property: %s (%s)" % (name, size)

    def createFields(self):
        yield String(self, "name", 64, charset="UTF-16-LE", strip="\0")
        yield UInt16(self, "namelen", "Length of the name")
        yield Enum(UInt8(self, "type", "Property type"), self.type_name)
        yield Enum(UInt8(self, "decorator", "Decorator"), self.decorator_name)
        yield SECT(self, "left")
        yield SECT(self, "right")
        yield SECT(self, "child")
        yield GUID(self, "clsid", "CLSID of this storage")
        yield RawBytes(self, "flags", 4, "User flags")
        # Timestamp format: Number of nanosecond since January 1, 1601
        yield UInt64(self, "creation", "Creation timestamp", text_handler=timestampWin64)
        yield UInt64(self, "lastmod", "Modify timestamp", text_handler=timestampWin64)
        yield SECT(self, "start", "Starting SECT of the stream")
#        block = self["start"].value
#        if block != SECT.UNUSED and block != 0:
#            chain = self["/"].getFatChain(block)
        yield UInt32(self, "size_lo", "Size in bytes (low part)")
        yield UInt32(self, "size_hi", "Size in bytes (high part)")

class Header(FieldSet):
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

class SectFat(FieldSet):
    def __init__(self, parent, name, start, count, description=None):
        FieldSet.__init__(self, parent, name, description, size=count*32)
        self.count = count
        self.start = start

    def createFields(self):
        for i in xrange(self.start, self.start + self.count):
            yield SECT(self, "index[%u]" % i)

class OLE_Document(Parser):
    BIG_BLOCK_SIZE = 512

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
            self.sector_size = 512 # bytes
        else: # major version is 4
            self.sector_size = 4096 # bytes
        self.bb_size = (1 << header["bb_shift"].value)
        self.sb_size = (1 << header["sb_shift"].value)
        self.fat_count = header["bb_count"].value
        self.items_per_bbfat = self.bb_size / (SECT.static_size/8)
        self.items_per_sfat = self.bb_size / (SECT.static_size/8)

        # Read DIFAT (one level of indirection)
        yield SectFat(self, "difat", 0, 109, "Double Indirection FAT")

        # Read FAT (one level of indirection)
        for field in self.readBFAT():
            yield field

        chain = self.getFatChain(self["header/bb_start"].value)
        count = 512 / (Property.static_size/8)
        for block in chain:
            fields = [ Property(self, "property[]") for i in range(count) ]
            for field in self.write(block, fields):
                yield field

        chain = self.getFatChain(self["header/sb_start"].value)
        index = 0
        start = 0
        for block in chain:
            fat = SectFat(self, "sfat[]", \
                start, self.items_per_sfat, \
                "SFAT %u/%u at block %u" % \
                (1+index, self["header/sb_count"].value, block))
            start += len(fat)
            index += 1

            for field in self.write(block, (fat,)):
                yield field

        # Read SFAT and big block depot (root directory)
        if False:
            block_bb = self["/header/bb_start"].value
            block_sb = self["/header/sb_start"].value
            if block_bb < block_sb:
                gen_list = (self.readRoot(), self.readSFAT())
            else:
                gen_list = (self.readSFAT(), self.readRoot())

            for gen in gen_list:
                for field in gen:
                    yield field
        if self.current_size < self._size:
            yield self.seekBit(self._size, "end")

    def write(self, block, fields):
        address = self.blockAddress(block)
        existing = self.getFieldByAddress(address, False)
        if existing is None:
            pad = self.seekBlock(block)
            if pad is not None:
                yield pad
            for field in fields:
                yield field
        else:
            self.writeFieldsIn(existing, address, fields)

    def getFatSECT(self, block):
        index = block / self.items_per_bbfat
        return self.bb_fat[index]["index[%u]" % block].value

    def getFatChain(self, block):
        chain = [ ]
        while block != SECT.END_OF_CHAIN:
            chain.append(block)
            block = self.getFatSECT(block)
        return chain

    def readBFAT(self):
        self.bb_fat = []
        start = 0
        for index, block in enumerate(self.array("difat/index")):
            block = block.value
            if block == SECT.UNUSED:
                break

            fat = SectFat(self, "bbfat[]", \
                start, self.items_per_bbfat, \
                "FAT %u/%u at block %u" % \
                (1+index, self["header/bb_count"].value, block))
            start += len(fat)
            self.bb_fat.append(fat)

            for field in self.write(block, (fat,)):
                yield field

    def readSFAT(self):
        chain = self.getFatChain(self["header/sb_start"].value)
        start = 0
        for index, block in enumerate(chain):
            block = block.value
            pad = self.seekBlock(block)
            if pad is not None:
                yield pad
            field = SectFat(self, "sfat[]", \
                start, self.items_per_sfat, \
                "SFAT %u/%u at block %u" % \
                (1+index, self["header/bb_count"].value, block))
            start += len(field)
            yield field

    def blockAddress(self, block):
        """ Address in bits of a block """

        # 512 is header size (in bytes)
        return (512 + block * self.sector_size) * 8

    def seekBlock(self, block):
        address = self.blockAddress(block)
        return self.seekBit(address)

    def readRoot(self):
        chain = self.getFatChain(self["header/bb_start"].value)
        for block in chain:
            pad = self.seekBlock(block)
            if pad is not None:
                yield pad
            count = 512 / (Property.static_size/8)
            for i in range(0, count):
                yield Property(self, "property[]")

