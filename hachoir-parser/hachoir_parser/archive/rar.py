"""
RAR parser

Status: can only read higher-level attructures
Author: Christophe Gisquet
"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    Bit, Bits, Enum,
    UInt8, UInt16, UInt32, UInt64,
    String,
    NullBytes, NullBits, RawBytes)
from hachoir_core.text_handler import humanFilesize, hexadecimal, timestampMSDOS
from hachoir_core.endian import LITTLE_ENDIAN

BLOCK_NAME = {
    0x72: "Marker",
    0x73: "Archive",
    0x74: "File",
    0x75: "Comment",
    0x76: "Extra info",
    0x77: "Subblock",
    0x78: "Recovery record",
    0x79: "Archive authenticity",
    0x7A: "New-format subblock",
    0x7B: "Archive end",
}

COMPRESSION_NAME = {
    0x30: "Storing",
    0x31: "Fastest compression",
    0x32: "Fast compression",
    0x33: "Normal compression",
    0x34: "Good compression",
    0x35: "Best compression"
}

OS_MSDOS = 0
OS_WIN32 = 2
OS_NAME = {
    0: "MS DOS",
    1: "OS/2",
    2: "Win32",
    3: "Unix",
}

def formatRARVersion(field):
    """
    Decodes the RAR version stored on 1 byte
    """
    return "%u.%u" % divmod(field.value, 10)

class MSDOSFileAttr(FieldSet):
    """
    Decodes the MSDOS file attribute, as specified by the winddk.h header
    and its FILE_ATTR_ defines:
    http://www.cs.colorado.edu/~main/cs1300/include/ddk/winddk.h
    """
    static_size = 32
    def createFields(self):
        yield Bit(self, "read_only")
        yield Bit(self, "hidden")
        yield Bit(self, "system")
        yield NullBits(self, "reserved[]", 1)
        yield Bit(self, "directory")
        yield Bit(self, "archive")
        yield Bit(self, "device")
        yield Bit(self, "normal")
        yield Bit(self, "temporary")
        yield Bit(self, "sparse_file")
        yield Bit(self, "reparse_file")
        yield Bit(self, "compressed")
        yield Bit(self, "offline")
        yield Bit(self, "dont_index_content")
        yield Bit(self, "encrypted")
        yield NullBits(self, "reserved[]", 1+16)

def commonFlags(self):
    yield Bit(self, "has_added_size", "Additional field indicating additional size")
    yield Bit(self, "is_ignorable", "Old versions of RAR should ignore this block when copying data")

def archiveFlags(self):
    class archive_flags(FieldSet):
        static_size = 16
        def createFields(self):
            yield Bit(self, "vol", "Archive volume")
            yield Bit(self, "has_comment", "Whether there is a comment")
            yield Bit(self, "is_locked", "Archive volume")
            yield Bit(self, "is_solid", "Whether files can be extracted separately")
            yield Bit(self, "new_numbering", "New numbering, or compressed comment") # From unrar
            yield Bit(self, "has_authenticity_information", "The integrity/authenticity of the archive can be checked")
            yield Bit(self, "is_protected", "The integrity/authenticity of the archive can be checked")
            yield Bit(self, "is_passworded", "Needs a password to be decrypted")
            yield Bit(self, "is_first_vol", "Whether it is the first volume")
            yield Bit(self, "is_encrypted", "Whether the encryption version is present")
            yield NullBits(self, "internal", 6, "Reserved for 'internal use'")
    yield archive_flags(self, "flags", "Archiver block flags")

def archiveHeader(self):
    yield NullBytes(self, "reserved[]", 2, "Reserved word")
    yield NullBytes(self, "reserved[]", 4, "Reserved dword")

def archiveSubBlocks(self):
    count = 0
    flags = self["flags"]
    if flags["has_comment"].value:
        count += 1
    if flags["is_protected"].value or flags["is_encrypted"].value:
        count += 1
    return count

def commentHeader(self):
    yield UInt16(self, "total_size", "Comment header size + comment size", text_handler=humanFilesize)
    yield UInt16(self, "uncompressed_size", "Uncompressed comment size", text_handler=humanFilesize)
    yield UInt8(self, "required_version", "RAR version needed to extract comment")
    yield UInt8(self, "packing_method", "Comment packing method")
    yield UInt16(self, "comment_crc16", "Comment CRC")

def commentBody(self):
    size = self["total_size"].value - self.current_size
    if size > 0:
        yield RawBytes(self, "comment_data", size, "Compressed comment data")

def signatureHeader(self):
    yield UInt32(self, "creation_time", text_handler=timestampMSDOS)
    yield UInt16(self, "arc_name_size", text_handler=humanFilesize)
    yield UInt16(self, "user_name_size", text_handler=humanFilesize)

def recoveryHeader(self):
    yield UInt32(self, "total_size", text_handler=humanFilesize)
    yield UInt8(self, "version", text_handler=hexadecimal)
    yield UInt16(self, "rec_sectors")
    yield UInt32(self, "total_blocks")
    yield RawBytes(self, "mark", 8)

def avInfoHeader(self):
    yield UInt16(self, "total_size", "Total block size", text_handler=humanFilesize)
    yield UInt8(self, "version", "Version needed to decompress", handler=hexadecimal)
    yield UInt8(self, "method", "Compression method", handler=hexadecimal)
    yield UInt8(self, "av_version", "Version for AV", handler=hexadecimal)
    yield UInt32(self, "av_crc", "AV info CRC32", handler=hexadecimal)

def avInfoBody(self):
    size = self["total_size"].value - self.current_size
    if size > 0:
        yield RawBytes(self, "av_info_data", size, "AV info")

def fileFlags(self):
    class file_flags(FieldSet):
        DICTIONARY_SIZE = {
            0: "Dictionary size 64 Kb",
            1: "Dictionary size 128 Kb",
            2: "Dictionary size 256 Kb",
            3: "Dictionary size 512 Kb",
            4: "Dictionary size 1024 Kb",
            7: "File is a directory",
        }
        static_size = 16
        def createFields(self):
            yield Bit(self, "continued_from", "File continued from previous volume")
            yield Bit(self, "continued_in", "File continued in next volume")
            yield Bit(self, "is_encrypted", "File encrypted with password")
            yield Bit(self, "has_comment", "File comment present")
            yield Bit(self, "is_solid", "Information from previous files is used (solid flag)")
            yield Enum(Bits(self, "dictionary_size", 3, "Dictionary size"), self.DICTIONARY_SIZE)
            for bit in commonFlags(self): yield bit
            yield Bit(self, "is_large", "file64 operations needed")
            yield Bit(self, "is_unicode", "Filename also encoded using Unicode")
            yield Bit(self, "has_salt", "Has salt for encryption")
            yield Bit(self, "uses_file_version", "File versioning is used")
            yield Bit(self, "has_ext_time", "Extra time ??")
            yield Bit(self, "has_ext_flags", "Extra flag ??")
    yield file_flags(self, "flags", "File block flags")

class ExtTime(FieldSet):
    def createFields(self):
        yield UInt16(self, "time_flags", "Flags for extended time", text_handler=hexadecimal)
        flags = self["time_flags"].value
        for index in xrange(4):
            rmode = flags >> ((3-index)*4)
            if rmode & 8:
                if index:
                    yield UInt32(self, "dos_time[]", "DOS Time", text_handler=timestampMSDOS)
                if rmode & 3:
                    yield RawBytes(self, "remainder[]", rmode & 3, "Time remainder")

def specialHeader(self, is_file):
    yield UInt32(self, "compressed_size", "Compressed size (bytes)", text_handler=humanFilesize)
    yield UInt32(self, "uncompressed_size", "Uncompressed size (bytes)", text_handler=humanFilesize)
    yield Enum(UInt8(self, "host_os", "Operating system used for archiving"), OS_NAME)
    yield UInt32(self, "crc32", "File CRC32", text_handler=hexadecimal)
    yield UInt32(self, "ftime", "Date and time (MS DOS format)", text_handler=timestampMSDOS)
    yield UInt8(self, "version", "RAR version needed to extract file", text_handler=formatRARVersion)
    yield Enum(UInt8(self, "method", "Packing method"), COMPRESSION_NAME)
    yield UInt16(self, "filename_length", "File name size", text_handler=humanFilesize)
    if self["host_os"].value in (OS_MSDOS, OS_WIN32):
        yield MSDOSFileAttr(self, "file_attr", "File attributes")
    else:
        yield UInt32(self, "file_attr", "File attributes", text_handler=hexadecimal)

    # Start additional field from unrar
    flags = self["flags"]
    if flags["is_large"].value:
        val = UInt64(self, "large_size", "Extended 64bits filesize", text_handler=humanFilesize)

    # End additional field
    size = self["filename_length"].value
    if size > 0:
        if flags["is_unicode"].value:
            charset = "UTF-8"
        else:
            charset = "ISO-8859-15"
        yield String(self, "filename", size, "Filename", charset=charset)
    # Start additional fields from unrar - file only
    if is_file:
        if flags["has_salt"].value:
            yield UInt8(self, "salt", "Salt", text_handler=hexadecimal)
        if flags["has_ext_time"].value:
            yield ExtTime(self, "extra_time", "Extra time info")

def fileHeader(self):
    return specialHeader(self, True)

def fileBody(self):
    # File compressed data
    size = self["compressed_size"].value
    flags = self["flags"]
    if flags["is_large"].value:
        size += self["large_size"].value
    if size > 0:
        yield RawBytes(self, "compressed_data", size, "File compressed data")

def fileSubBlocks(self):
    count = 0
    f1, f2 = self["flags"], self["/archive_start/flags"]
    if f1["has_comment"].value:  count += 1
    if f1["is_encrypted"].value: count += 1
    if f2["is_protected"].value: count += 1
    return count

def fileDescription(self):
    return "File entry: %s (%s)" % \
           (self["filename"].display, self["compressed_size"].display)

def newSubHeader(self):
    return specialHeader(self, False)

class EndFlags(FieldSet):
    static_size = 16
    def createFields(self):
        yield Bit(self, "has_next_vol", "Whether there is another next volume")
        yield Bit(self, "has_data_crc", "Whether a CRC value is present")
        yield Bit(self, "rev_space")
        yield Bit(self, "has_vol_number", "Whether the volume number is present")
        yield Bits(self, "unused[]", 4)
        for bit in commonFlags(self):
            yield bit

def endFlags(self):
    yield EndFlags(self, "flags", "End block flags")

class BlockFlags(FieldSet):
    static_size = 16
    def createFields(self):
        yield Bits(self, "unused[]", 8, "Unused flag bits", text_handler=hexadecimal)
        for bit in commonFlags(self):
            yield bit

class Block(FieldSet):
    BLOCK_INFO = {
        # None means 'use default function'
        0x72: ("marker", "Archive header", None, None, None, None),
        0x73: ("archive_start", "Archive info", archiveFlags, archiveHeader,
               None, archiveSubBlocks),
        0x74: ("file[]", fileDescription, fileFlags, fileHeader, fileBody,
               fileSubBlocks),
        0x75: ("comment[]", "Stray comment", None, commentHeader, commentBody, None),
        0x76: ("av_info[]", "Extra information", None, avInfoHeader, avInfoBody, None),
        0x77: ("sub_block[]", "Stray subblock", None, newSubHeader, fileBody, None),
        0x78: ("recovery[]", "Recovery block", None, recoveryHeader, None, None),
        0x79: ("signature", "Signature block", None, signatureHeader, None, None),
        0x7A: ("new_sub_block[]", "Stray new-format subblock", fileFlags,
               newSubHeader, fileBody, None),
        0x7B: ("archive_end", "Archive end block", endFlags, None, None, None),
    }

    def __init__(self, parent, name):
        FieldSet.__init__(self, parent, name)
        type = self["block_type"].value
        if type in self.BLOCK_INFO:
            self._name, desc, parseFlags, parseHeader, parseBody, countSubBlocks = self.BLOCK_INFO[type]
            if callable(desc):
                self.createDescription = lambda: desc(self)
            elif desc:
                self._description = desc
            if parseFlags    : self.parseFlags     = lambda: parseFlags(self)
            if parseHeader   : self.parseHeader    = lambda: parseHeader(self)
            if parseBody     : self.parseBody      = lambda: parseBody(self)
            if countSubBlocks: self.countSubBlocks = lambda: countSubBlocks(self)
        else:
            self.info("Processing as unknown block block of type %u" % type)

    def createFields(self):
        yield UInt16(self, "crc16", "Block CRC16", text_handler=hexadecimal)
        yield UInt8(self, "block_type", "Block type", text_handler=hexadecimal)

        # Parse flags
        for field in self.parseFlags():
            yield field

        # Get block size
        yield UInt16(self, "block_size", "Block size", text_handler=humanFilesize)

        # Parse remaining header
        for field in self.parseHeader():
            yield field

        # Finish header with stuff of unknow size
        size = self["block_size"].value - (self.current_size//8)
        if size > 0:
            yield RawBytes(self, "unknown", size, "Unknow data (UInt32 probably)")

        # Parse body
        for field in self.parseBody():
            yield field

        # Get sub blocks, if any
        count = self.countSubBlocks()
        for i in xrange(count):
            yield Block(self, "sub_block[]")

    def createDescription(self):
        return "Block entry: %s" % self["type"].display

    def parseFlags(self):
        yield BlockFlags(self, "flags", "Block header flags")

    def parseHeader(self):
        flags = self["flags"]
        if "has_added_size" in flags and flags["has_added_size"].value:
            yield UInt32(self, "added_size", "Supplementary block size", text_handler=humanFilesize)

    def parseBody(self):
        """
        Parse what is left of the block
        """
        size = self["block_size"].value - (self.current_size//8)
        flags = self["flags"]
        if "has_added_size" in flags and flags["has_added_size"].value:
            size += self["added_size"].value
        if size > 0:
            yield RawBytes(self, "body", size, "Body data")

    def countSubBlocks(self):
        return 0

class RarFile(Parser):
    MAGIC = "Rar!\x1A\x07\x00"
    tags = {
        "id": "rar",
        "category": "archive",
        "file_ext": ("rar",),
        "mime": ("application/x-rar-compressed", ),
        "min_size": 7*8,
        "magic": ((MAGIC, 0),),
        "description": "Roshal archive (RAR)",
    }
    endian = LITTLE_ENDIAN

    def validate(self):
        magic = self.MAGIC
        if self.stream.readBytes(0, len(magic)) != magic:
            return "Invalid magic"
        return True

    def createFields(self):
        while not self.eof:
            yield Block(self, "block[]")

    def createContentSize(self):
        end = self.stream.searchBytes("\xC4\x3D\x7B\x00\x40\x07\x00", 0)
        if end is not None:
            return end + 7*8
        return None

