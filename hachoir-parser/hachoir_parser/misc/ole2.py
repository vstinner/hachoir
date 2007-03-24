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
    Bit, Bits, NullBits,
    UInt8, UInt16, UInt32, UInt64, TimestampWin64, Enum,
    Bytes, RawBytes, NullBytes, String,
    Int8, Int16, Int32, Float32, Float64, PascalString32)
from hachoir_core.text_handler import textHandler, hexadecimal
from hachoir_core.tools import humanFilesize, createDict
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN
from hachoir_parser.common.win32 import GUID

# Number of items in DIFAT
NB_DIFAT = 109

# FIXME: Remove this hack
HACK_FOR_SUMMARY = False

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
    TYPE_ROOT = 5
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
        yield NullBytes(self, "flags", 4, "User flags")
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
        yield NullBytes(self, "transaction", 4, "Signature used for transactions (must be zero)")
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

class PropertyIndex(FieldSet):
    COMMON_PROPERTY = {
        0: "Dictionary",
        1: "CodePage",
        0x80000000: "LOCALE_SYSTEM_DEFAULT",
        0x80000003: "CASE_SENSITIVE",
    }

    DOCUMENT_PROPERTY = {
         2: "Category",
         3: "PresentationFormat",
         4: "NumBytes",
         5: "NumLines",
         6: "NumParagraphs",
         7: "NumSlides",
         8: "NumNotes",
         9: "NumHiddenSlides",
        10: "NumMMClips",
        11: "Scale",
        12: "HeadingPairs",
        13: "DocumentParts",
        14: "Manager",
        15: "Company",
        16: "LinksDirty",
        17: "DocSumInfo_17",
        18: "DocSumInfo_18",
        19: "DocSumInfo_19",
        20: "DocSumInfo_20",
        21: "DocSumInfo_21",
        22: "DocSumInfo_22",
        23: "DocSumInfo_23",
    }
    DOCUMENT_PROPERTY.update(COMMON_PROPERTY)

    COMPONENT_PROPERTY = {
         2: "Title",
         3: "Subject",
         4: "Author",
         5: "Keywords",
         6: "Comments",
         7: "Template",
         8: "LastSavedBy",
         9: "RevisionNumber",
        10: "TotalEditingTime",
        11: "LastPrinted",
        12: "CreateTime",
        13: "LastSavedTime",
        14: "NumPages",
        15: "NumWords",
        16: "NumCharacters",
        17: "Thumbnail",
        18: "AppName",
        19: "Security",
    }
    COMPONENT_PROPERTY.update(COMMON_PROPERTY)

    def createFields(self):
        if self["../.."].name.startswith("doc_summary"):
            enum = self.DOCUMENT_PROPERTY
        else:
            enum = self.COMPONENT_PROPERTY
        yield Enum(UInt32(self, "id"), enum)
        yield UInt32(self, "offset")

    def createDescription(self):
        return "Propery: %s" % self["id"].display

class Bool(Int8):
    def createValue(self):
        value = Int8.createValue(self)
        return (value == -1)

class Thumbnail(FieldSet):
    """
    Thumbnail.

    Documents:
    - See Jakarta POI
      http://jakarta.apache.org/poi/hpsf/thumbnails.html
      http://www.penguin-soft.com/penguin/developer/poi/
          org/apache/poi/hpsf/Thumbnail.html#CF_BITMAP
    - How To Extract Thumbnail Images
      http://sparks.discreet.com/knowledgebase/public/
          solutions/ExtractThumbnailImg.htm
    """
    FORMAT_NAME = {
        -1: "Windows clipboard",
        -2: "Macintosh clipboard",
        -3: "GUID that contains format identifier",
         0: "No data",
         2: "Bitmap",
         3: "Windows metafile format",
         8: "Device Independent Bitmap",
        14: "Enhanced Windows metafile",
    }
    def __init__(self, *args):
        FieldSet.__init__(self, *args)
        self._size = self["size"].value * 8

    def createFields(self):
        yield textHandler(UInt32(self, "size"), humanFilesize)
        yield Enum(Int32(self, "format"), self.FORMAT_NAME)
        size = (self.size - self.current_size) // 8
        if size:
            yield RawBytes(self, "data", size)

class PropertyContent(FieldSet):
    TYPE_INFO = {
        0: ("EMPTY", None),
        1: ("NULL", None),
        2: ("Int16", Int16),
        3: ("Int32", Int32),
        4: ("Float32", Float32),
        5: ("Float64", Float64),
        6: ("CY", None),
        7: ("DATE", None),
        8: ("BSTR", None),
        9: ("DISPATCH", None),
        10: ("ERROR", None),
        11: ("BOOL", Bool),
        12: ("VARIANT", None),
        13: ("UNKNOWN", None),
        14: ("DECIMAL", None),
        16: ("I1", None),
        17: ("UI1", None),
        18: ("UI2", None),
        19: ("UI4", None),
        20: ("I8", None),
        21: ("UI8", None),
        22: ("INT", None),
        23: ("UINT", None),
        24: ("VOID", None),
        25: ("HRESULT", None),
        26: ("PTR", None),
        27: ("SAFEARRAY", None),
        28: ("CARRAY", None),
        29: ("USERDEFINED", None),
        30: ("LPSTR", PascalString32),
        31: ("LPWSTR", None),
        64: ("FILETIME", TimestampWin64),
        65: ("BLOB", None),
        66: ("STREAM", None),
        67: ("STORAGE", None),
        68: ("STREAMED_OBJECT", None),
        69: ("STORED_OBJECT", None),
        70: ("BLOB_OBJECT", None),
        71: ("THUMBNAIL", Thumbnail),
        72: ("CLSID", None),
        0x1000: ("Vector", None),
    }
    TYPE_NAME = createDict(TYPE_INFO, 0)

    def createFields(self):
        if True:
            yield Enum(Bits(self, "type", 12), self.TYPE_NAME)
            yield Bit(self, "is_vector")
            yield NullBits(self, "padding", 32-12-1)
        else:
            yield Enum(Bits(self, "type", 32), self.TYPE_NAME)
        try:
            handler = self.TYPE_INFO[ self["type"].value ][1]
        except LookupError:
            handler = None
        if not handler:
            raise ParserError("OLE2: Unable to parse property of type %s" \
                % self["type"].display)
        if self["is_vector"].value:
            yield UInt32(self, "count")
            for index in xrange(self["count"].value):
                yield handler(self, "item[]")
        else:
            yield handler(self, "value")
            self.createValue = lambda: self["value"].value
PropertyContent.TYPE_INFO[12] = ("VARIANT", PropertyContent)

class SummarySection(SeekableFieldSet):
    def __init__(self, *args):
        SeekableFieldSet.__init__(self, *args)
        self._size = self["size"].value * 8

    def createFields(self):
        yield UInt32(self, "size")
        yield UInt32(self, "property_count")
        for index in xrange(self["property_count"].value):
            yield PropertyIndex(self, "property_index[]")
        for index in xrange(self["property_count"].value):
            findex = self["property_index[%u]" % index]
            self.seekByte(findex["offset"].value)
            yield PropertyContent(self, "property[]", findex["id"].display)

class SummaryIndex(FieldSet):
    def createFields(self):
        yield String(self, "name", 16)
        yield UInt32(self, "offset")

class Summary(FieldSet):
    OS_NAME = {
        0: "Windows 16-bit",
        1: "Mac",
        2: "Windows 32-bit",
    }

    def __init__(self, *args, **kw):
        FieldSet.__init__(self, *args, **kw)
        if self["endian"].value == "\xFF\xFE":
            self.endian = BIG_ENDIAN

    def createFields(self):
        yield Bytes(self, "endian", 2, "Endian (0xFF 0xFE for Intel)")
        yield UInt16(self, "format", "Format (0)")
        yield textHandler(UInt16(self, "os_version"), hexadecimal)
        yield Enum(UInt16(self, "os"), self.OS_NAME)
        yield GUID(self, "format_id")
        yield UInt32(self, "section_count")

        section_indexes = []
        for index in xrange(self["section_count"].value):
            section_index = SummaryIndex(self, "section_index[]")
            yield section_index
            section_indexes.append(section_index)

        for section_index in section_indexes:
            self.seekByte(section_index["offset"].value)
            yield SummarySection(self, "section[]")

        size = (self.size - self.current_size) // 8
        if size:
            yield NullBytes(self, "end_padding", size)

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
        self.items_per_bbfat = (8 << header["bb_shift"].value) / SECT.static_size
        self.ss_size = (8 << header["sb_shift"].value)

        # Read DIFAT (one level of indirection)
        yield SectFat(self, "difat", 0, NB_DIFAT, "Double Indirection FAT")

        # Read FAT (one level of indirection)
        for field in self.readBFAT():
            yield field

        # Read SFAT
        for field in self.readSFAT():
            yield field

        # Read properties
        chain = self.getChain(self["header/bb_start"].value)
        prop_per_sector = self.sector_size // Property.static_size
        properties = []
        for block in chain:
            self.seekBlock(block)
            for index in xrange(prop_per_sector):
                property = Property(self, "property[]")
                yield property
                properties.append(property)

        # Parse first property
        if HACK_FOR_SUMMARY:
            for field in self.parseProperty(self["property[0]"], "root"):
                yield field
            for field in self.parseProperty(self["property[4]"], "summary"):
                yield field
            for field in self.parseProperty(self["property[5]"], "doc_summary"):
                yield field
        else:
            for index, property in enumerate(properties):
                if index == 0:
                    name = "root"
                else:
                    name = property.name+"content"
                for field in self.parseProperty(property, name):
                    yield field

    def parseProperty(self, property, name_prefix):
        if not property["size"].value:
            return
        name = "%s[]" % name_prefix
        first = None
        previous = None
        size = 0
        start = property["start"].value
        if HACK_FOR_SUMMARY or property["type"].value == Property.TYPE_ROOT:
            chain = self.getChain(start)
            blocksize = self.sector_size
            seek = self.seekBlock
            desc_format = "Big blocks %s..%s (%s)" + " of %s bytes" % (blocksize//8)
        else:
            chain = self.getChain(start, self.ss_fat)
            blocksize = self.ss_size
            seek = self.seekSBlock
            desc_format = "Small blocks %s..%s (%s)"
        while True:
            try:
                block = chain.next()
                contigious = False
                if not first:
                    first = block
                    contigious = True
                if previous and block == (previous+1):
                    contigious = True
                if contigious:
                    #self.warning("Root block: %s" % block)
                    previous = block
                    size += blocksize
                    continue
            except StopIteration:
                block = None
            seek(first)
            desc = desc_format % (first, previous, previous-first+1)
            if name_prefix in ("summary", "doc_summary"):
                yield Summary(self, name, desc, size=size)
            else:
                yield RawBytes(self, name, size//8, desc)
            if block is None:
                break
            first = block
            previous = block
            size = self.sector_size

    def getChain(self, start, fat=None):
        if not fat:
            fat = self.bb_fat
        block = start
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
        chain = self.getChain(self["header/sb_start"].value)
        start = 0
        self.ss_fat = []
        count = self.items_per_bbfat
        for index, block in enumerate(chain):
            self.seekBlock(block)
            field = SectFat(self, "sfat[]", \
                start, count, \
                "SFAT %u/%u at block %u" % \
                (1+index, self["header/sb_count"].value, block))
            yield field
            self.ss_fat.append(field)
            start += count

    def seekBlock(self, block):
        self.seekBit(HEADER_SIZE + block * self.sector_size)

    def seekSBlock(self, block):
        # FIXME: Fix the offset
        self.seekBit((1024 - 64)*8 + block * self.ss_size)

