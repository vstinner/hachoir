"""
ACE parser

From wotsit.org and the SDK header (bitflags)

Partial study of a new block type (5) I've called "new_recovery", as its
syntax is very close to the former one (of type 2).

Status: can only read totally file and header blocks.
Author: Christophe Gisquet <christophe.gisquet@free.fr>
"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    Bit, Bits, Enum,
    UInt8, UInt16, UInt32, UInt64,
    String,
    RawBytes)
from hachoir_core.text_handler import humanFilesize, hexadecimal, timestampMSDOS
from hachoir_core.endian import LITTLE_ENDIAN
from hachoir_parser.archive.rar import MSDOSFileAttr
from hachoir_core.error import info
#import hachoir_core.config as config

MAX_CHUNK_SIZE = 500 * 1024 # Maximum chunk size (500 KB)
MAGIC = "**ACE**"
HOST_OS = {
    0: "MS-DOS",
    1: "OS/2",
    2: "Win32",
    3: "Unix",
    4: "MAC-OS",
    5: "Win NT",
    6: "Primos",
    7: "APPLE GS",
    8: "ATARI",
    9: "VAX VMS",
    10: "AMIGA",
    11: "NEXT",
    12: "Unknown"
}
COMPRESSION_TYPE = {
    0: "store",
    1: "Lempel-Ziv 77",
    2: "ACE v2.0"
}

COMPRESSION_MODE = {
    0: "fastest",
    1: "fast",
    2: "normal",
    3: "good",
    4: "best"
}

def markerValidate(self):
    # Computing the CRC16 would also prove useful
    return not self["extend"].value and self["signature"].value == MAGIC and \
           self["host_os"].value<12
def markerFlags(self):
    #info("Marker parseFlags()")
    class marker_flags(FieldSet):
        static_size = 16
        def createFields(self):
            yield Bit(self, "extend", "Whether the header is extended")
            yield Bit(self, "has_comment", "Whether the archive has a comment")
            yield Bits(self, "unused", 7, "Reserved bits", text_handler=hexadecimal)
            yield Bit(self, "sfx", "SFX")
            yield Bit(self, "limited_dict", "Junior SFX with 256K dictionary")
            yield Bit(self, "multi_volume", "Part of a set of ACE archives")
            yield Bit(self, "has_av_string", "This header holds an AV-string")
            yield Bit(self, "recovery_record", "Recovery record preset")
            yield Bit(self, "locked", "Archive is locked")
            yield Bit(self, "solid", "Archive uses solid compression")
    yield marker_flags(self, "flags", "Marker flags")
def markerHeader(self):
    #info("Marker parseHeader()")
    yield String(self, "signature", 7, "Signature")
    yield UInt8(self, "ver_extract", "Version needed to extract archive")
    yield UInt8(self, "ver_created", "Version used to create archive")
    yield Enum(UInt8(self, "host_os", "OS where the files were compressed"), HOST_OS)
    yield UInt8(self, "vol_num", "Volume number")
    yield UInt32(self, "time", "Date and time (MS DOS format)", text_handler=timestampMSDOS)
    yield UInt64(self, "reserved", "Reserved size for future extensions", text_handler=hexadecimal)
    if self.flags["has_av_string"].value:
        size = UInt8(self, "av_size", "Size of the AV string")
        yield size
        if size.value>0: yield String(self, "av_string", size.value, "AV string")
    if self.flags["has_comment"].value:
        size = UInt16(self, "comment_size", "Size of the comment string")
        yield size
        if size.value>0: yield RawBytes(self, "comment", size.value, "Comment compressed data")

def fileFlags(self):
    #info("File parseFlags()")
    class file_flags(FieldSet):
        static_size = 16
        def createFields(self):
            yield Bit(self, "extend", "Whether the header is extended")
            yield Bit(self, "has_comment", "Presence of file comment")
            yield Bits(self, "unused", 10, "Unused bit flags")
            yield Bit(self, "encrypted", "File encrypted with password")
            yield Bit(self, "previous", "File continued from previous volume")
            yield Bit(self, "next", "File continues on the next volume")
            yield Bit(self, "solid", "File compressed using previously archived files")
    yield file_flags(self, "flags", "File flags")
def fileHeader(self):
    #info("File parseHeader()")
    yield UInt32(self, "compressed_size", "Size of the compressed file", text_handler=humanFilesize)
    yield UInt32(self, "uncompressed_size", "Uncompressed file size", text_handler=humanFilesize)
    yield UInt32(self, "ftime", "Date and time (MS DOS format)", text_handler=timestampMSDOS)
    marker = self._parent["header"]
    if marker["host_os"].value in (0, 2):
        yield MSDOSFileAttr(self, "file_attr", "File attributes")
    else:
        yield UInt32(self, "attr", "File attributes", text_handler=hexadecimal)
    yield UInt32(self, "file_crc32", "CRC32 checksum over the compressed file)", text_handler=hexadecimal)
    yield Enum(UInt8(self, "compression_type", "Type of compression"), COMPRESSION_TYPE)
    yield Enum(UInt8(self, "compression_mode", "Quality of compression"), COMPRESSION_MODE)
    yield UInt16(self, "parameters", "Compression paramters", text_handler=hexadecimal)
    yield UInt16(self, "reserved", "Reserved data", text_handler=hexadecimal)
    # Filename
    size = UInt16(self, "filename_size", "Size of the filename", text_handler=humanFilesize)
    yield size
    if size.value>0:
        value = String(self, "filename", size.value, "Filename")
        yield value
        self._name = value.value.replace(' ', '\x80').replace('/','\\')
    # Comment
    if self.flags["has_comment"].value:
        size = UInt16(self, "comment_size", "Size of the compressed comment", text_handler=humanFilesize)
        yield size
        if size.value>0: yield RawBytes(self, "comment_data", size.value, "Comment data")
def fileBody(self):
    #info("File parseBody()")
    size = self["compressed_size"].value
    if size>0: yield RawBytes(self, "compressed_data", size, "Compressed data")
def fileDesc(self):
    return "File entry: %s (%s)" % (self["filename"].value, self["compressed_size"].display)

def recoveryHeader(self):
    size = UInt32(self, "rec_blk_size", "Size of recovery data", text_handler=humanFilesize)
    yield size
    self.body_size = size.value
    yield String(self, "signature", 7, "Signature, normally '**ACE**'")
    yield UInt32(self, "relative_start", "Relative start (to this block) of the data this block is mode of", text_handler=hexadecimal)
    yield UInt32(self, "num_blocks", "Number of blocks the data is splitten in")
    yield UInt32(self, "size_blocks", "Size of these blocks")
    yield UInt16(self, "crc16_blocks", "CRC16 over recovery data")
    # size_blocks blocks of size size_blocks follow
    # The ultimate data is the xor data of all those blocks
    num = self["num_blocks"].value
    size = self["size_blocks"].value
    while num:
        yield RawBytes(self, "data[]", size, "Recovery block %i" % num)
        num -= 1
    yield RawBytes(self, "xor_data", size, "The XOR value of the above data blocks")
def recoveryDesc(self):
    return "Recovery block, size=%u" % humanFilesize(self["body_size"].value)

def newrecoveryHeader(self):
    """
    This header is described nowhere
    """
    #info("NewRecovery parseHeaders()")
    self.body_size = 0
    flags = self["flags"]
    if flags["extend"].value:
        yield UInt32(self, "body_size", "Size of the unknown body following")
        self.body_size = self["body_size"].value
    yield UInt32(self, "unknown[]", "Unknown field, probably 0", text_handler=hexadecimal)
    yield String(self, "signature", 7, "Signature, normally '**ACE**'")
    yield UInt32(self, "relative_start", "Offset (=crc16's) of this block in the file", text_handler=hexadecimal)
    yield UInt32(self, "unknown[]", "Unknown field, probably 0", text_handler=hexadecimal)

def parseFlags(self):
    #info("Base parseFlags()")
    class base_flags(FieldSet):
        static_size = 16
        def createFields(self):
            yield Bit(self, "extend", "Whether the header is extended")
            yield Bits(self, "unused", 15, "Unused bit flags")
    yield base_flags(self, "flags", "Unknown flags")
def parseHeader(self):
    #info("Base parseHeaders()")
    self.body_size = 0
    flags = self["flags"]
    if flags["extend"].value:
        yield UInt32(self, "body_size", "Size of the unknown body following")
        self.body_size = self["body_size"].value
def parseBody(self):
    #info("Base parseBody()")
    if self.body_size>0:
        yield RawBytes(self, "body_data", self.body_size, "Body data, unhandled")
def createDescription(self):
    if self.desc_func: return self.desc_func(self)
    else:              return "Chunk: %s" % self["type"].display

class Block(FieldSet):
    tag_info = {
        0: ("header", "Archiver header", markerFlags, markerHeader, None),
        1: ("file[]", fileDesc, fileFlags, fileHeader, fileBody),
        2: ("recovery[]", recoveryDesc, recoveryHeader, None, None),
        5: ("new_recovery[]", None, None, newrecoveryHeader, None)
    }

    def __init__(self, parent, name, description=None):
        FieldSet.__init__(self, parent, name, description)
        #info("Members from type...")
        self.body_size = 0
        type = self["block_type"].value
        self.parseFlags = parseFlags
        self.parseHeader = parseHeader
        self.parseBody = parseBody
        self.createDescription = createDescription
        if type in self.tag_info:
            self._name, desc, self.parseFlags, self.parseHeader, self.parseBody = self.tag_info[type]
            if desc:
                if isinstance(desc, str): self._description = desc
                else:                     self.createDescription = desc
        else: print "Processing as unknown block block of type %u" % type
        if not self.parseFlags: self.parseFlags = parseFlags
        if not self.parseHeader: self.parseHeader = parseHeader
        if not self.parseBody: self.parseBody = parseBody
        if not self.createDescription: self.createDescription = createDescription

    def createFields(self):
        yield UInt16(self, "crc16", "Archive CRC16 (from byte 4 on)", text_handler=hexadecimal)
        yield UInt16(self, "head_size", "Block size (from byte 4 on)", text_handler=humanFilesize)
        yield UInt8(self, "block_type", "Block type")

        # Flags
        for flag in self.parseFlags(self): yield flag
        #info("Flags: %s" % self["flags"])
        self.flags = self["flags"]
        # Rest of the header
        for field in self.parseHeader(self): yield field
        size = self["head_size"].value - (self.current_size//8) + (2+2)
        if size>0:
            yield RawBytes(self, "extra_data", size, "Extra header data, unhandled")
        # Body in itself
        for field in self.parseBody(self): yield field

class AceFile(Parser):
    endian = LITTLE_ENDIAN
    tags = {
        "id": "ace",
        "category": "archive",
        "file_ext": ("ace",),
        "mime": ["application/x-ace-compressed"],
        "min_size": 50*8,
        "description": "ACE archive"
    }

    def validate(self):
        if self.stream.readBytes(7*8, len(MAGIC)) != MAGIC:
            return "Invalid magic"
        return True

    def createFields(self):
        while not self.eof:
            yield Block(self, "block[]")
