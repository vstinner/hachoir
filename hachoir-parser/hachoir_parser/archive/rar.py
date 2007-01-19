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

def formatRARVersion(field):
    """
    Decodes the RAR version stored on 1 byte
    """
    version = field.value
    return "%u.%u" % divmod(version, 10)

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

class BaseBlock(FieldSet):
    """
    Base class made for common functions collection, don't use directly
    """

    block_name = {
        0x72: "Marker",
        0x73: "Archive",
        0x74: "File",
        0x75: "Comment",
        0x76: "Extra info",
        0x77: "Subblock",
        0x78: "Recovery record",
        0x79: "Archive authenticity",
        0x7A: "New-format subblock",
        0x7B: "Archive end"
    }

    compression_name = {
        0x30: "Storing",
        0x31: "Fastest compression",
        0x32: "Fast compression",
        0x33: "Normal compression",
        0x34: "Good compression",
        0x35: "Best compression"
    }

    def parseHeader(self):
        yield UInt16(self, "crc16", "Block CRC16", text_handler=hexadecimal)
        yield UInt8(self, "type", "Block type", DefaultBlock.block_name)

    def getBaseSize(self):
        if self["has_extended_size"].value==0:
            return self["head_size"].value
        else:
            return self["head_size"].value + self["added_size"].value
    def parseCommonFlags(self):
        yield Bit(self, "has_extended_size", "Additional field indicating additional size")
        yield Bit(self, "is_ignorable", "Old versions of RAR should ignore this block when copying data")
    def parseBaseFlags(self):
        yield Bits(self, "flags_bits1", 8, "Unused flag bits", text_handler=hexadecimal)
        self.parseCommonFlags()
        yield Bits(self, "flags_bits2", 6, "Unused flag bits", text_handler=hexadecimal)
    def parseBaseSize(self):
        yield UInt16(self, "head_size", "Block size", text_handler=humanFilesize)
        if self["has_extended_size"].value==1:
             yield UInt32(self, "added_size", "Supplementary block size", text_handler=humanFilesize)
    def parseBaseBody(self, name, size=None, comment="Unknow data"):
        if size == None: size = self.getBaseSize()-7
        if size>0:
            yield RawBytes(self, name, size, comment)

class DefaultBlock(BaseBlock):
    def createFields(self):
        #self.parseBaseFlags()
        yield Bits(self, "flags_bits1", 8, "Unused flag bits", text_handler=hexadecimal)
        yield Bit(self, "has_extended_size", "Additional field indicating additional size")
        yield Bit(self, "is_ignorable", "Old versions of RAR should ignore this block when copying data")
        yield Bits(self, "flags_bits2", 6, "Unused flag bits", text_handler=hexadecimal)
        #self.parseBaseSize()
        size = UInt16(self, "head_size", "Block size", text_handler=humanFilesize)
        yield size
        size = size.value
        if self["has_extended_size"].value:
             yield UInt32(self, "added_size", "Supplementary block size", text_handler=humanFilesize)
             size += self["added_size"].value
        #self.parseBaseBody("unknown")
        if size>0:
            yield RawBytes(self, "unknown", size, "Unknow data")

class MarkerBlock(BaseBlock):
    """
    The marker block is actually considered as a fixed byte
    sequence: 0x52 0x61 0x72 0x21 0x1a 0x07 0x00
    """

    magic = "Rar!\x1A\x07\x00"

    def createFields(self):
        yield Bits(self, "flags_bits1", 8, "Unused flag bits", text_handler=hexadecimal)
        yield Bit(self, "has_extended_size", "Additional field indicating additional size")
        yield Bit(self, "is_ignorable", "Old versions of RAR should ignore this block when copying data")
        yield Bits(self, "flags_bits2", 6, "Unused flag bits", text_handler=hexadecimal)
        yield UInt16(self, "head_size", "Block size", text_handler=humanFilesize)
    #def validate(self):
    #    if self.stream.readBytes(0,7) != magic:
    #        return "Invalid signature"
    #    return True

class EndBlock(BaseBlock):
    def createFields(self):
        yield Bits(self, "flags_bits1", 8, "Unused flag bits", text_handler=hexadecimal)
        yield Bit(self, "has_extended_size", "Additional field indicating additional size")
        yield Bit(self, "is_ignorable", "Old versions of RAR should ignore this block when copying data")
        yield Bits(self, "flags_bits2", 6, "Unused flag bits", text_handler=hexadecimal)
        yield UInt16(self, "head_size", "Block size", text_handler=humanFilesize)

class CommentBlock(BaseBlock):
    def createFields(self):
        #self.parseBaseFlags()
        yield Bits(self, "flags_bits1", 8, "Unused flag bits", text_handler=hexadecimal)
        yield Bit(self, "has_extended_size", "Additional field indicating additional size")
        yield Bit(self, "is_ignorable", "Old versions of RAR should ignore this block when copying data")
        yield Bits(self, "flags_bits2", 6, "Unused flag bits", text_handler=hexadecimal)

        size = UInt16(self, "total_size", "Comment header size + comment size", text_handler=humanFilesize)
        yield size
        size = size.value
        yield UInt16(self, "uncompressed_size", "Uncompressed comment size", text_handler=humanFilesize)
        yield Byte(self, "required_version", "RAR version needed to extract comment")
        yield Byte(self, "packing_method", "Comment packing method")
        yield UInt16(self, "comment_crc16", "Comment CRC")
        #self.parseBaseBody("comment_data", size-13, "Compressed comment data")
        if size-13>0:
            yield RawBytes(self, "comment_data", size-13, "Compressed comment data")

class ExtraInfoBlock(BaseBlock):
    def createFields(self):
        #self.parseBaseFlags()
        yield Bits(self, "flags_bits1", 8, "Unused flag bits", text_handler=hexadecimal)
        yield Bit(self, "has_extended_size", "Additional field indicating body size")
        yield Bit(self, "is_ignorable", "Old versions of RAR should ignore this block when copying data")
        yield Bits(self, "flags_bits2", 6, "Unused flag bits", text_handler=hexadecimal)

        size = UInt16(self, "total_size", "Total block size", text_handler=humanFilesize)
        yield size

        #self.parseBaseBody(size.value-7)
        if size-7>0:
            yield RawBytes(self, "info_data", size-7, "Other info")

class ArchiveBlock(BaseBlock):
    def createFields(self):
        yield Bit(self, "vol", "Archive volume")
        yield Bit(self, "has_comment", "Whether there is a comment")
        yield Bit(self, "is_locked", "Archive volume")
        yield Bit(self, "is_solid", "Whether files can be extracted separately")
        yield Bit(self, "unused", "Unused bit")
        yield Bit(self, "has_authenticity_information", "The integrity/authenticity of the archive can be checked")
        yield NullBits(self, "internal", 10, "Reserved for 'internal use'")
        yield UInt16(self, "head_size", "Block size", text_handler=humanFilesize)
        yield NullBytes(self, "reserved[]", 2, "Reserved word")
        yield NullBytes(self, "reserved[]", 4, "Reserved dword")
        if self["has_comment"].value==1:
            yield CommentBlock(self, "comment", "Archive compressed comment")

class FileBlock(BaseBlock):
    DICTIONARY_SIZE = {
        0: "Dictionary size 64 Kb",
        1: "Dictionary size 128 Kb",
        2: "Dictionary size 256 Kb",
        3: "Dictionary size 512 Kb",
        4: "Dictionary size 1024 Kb",
        7: "File is a directory",
    }

    OS_NAME = {
        0: "MS DOS",
        1: "OS/2",
        2: "Win32",
        3: "Unix",
    }

    def createFields(self):
        yield Bit(self, "continued_from", "File continued from previous volume")
        yield Bit(self, "continued_in", "File continued in next volume")
        yield Bit(self, "encrypted", "File encrypted with password")
        yield Bit(self, "has_comment", "File comment present")
        yield Bit(self, "is_solid", "Information from previous files is used (solid flag)")
        yield Enum(Bits(self, "dictionary_size", 3, "Dictionary size"), self.DICTIONARY_SIZE)
        yield Bit(self, "has_extended_size", "Additional field indicating body size")
        yield Bit(self, "is_ignorable", "Old versions of RAR should ignore this block when copying data")
        yield Bit(self, "is_large", "file64 operations needed")
        yield Bit(self, "is_unicode", "Filename also encoded using Unicode")
        yield Bit(self, "has_salt", "Has salt for encryption")
        yield Bit(self, "uses_file_version", "File versioning is used")
        yield Bit(self, "bexttime", "Extra time ??")
        yield Bit(self, "bextflag", "Extra flag ??")
        yield UInt16(self, "head_size", "File header full size including file name and comments", text_handler=humanFilesize)
        yield UInt32(self, "compressed_size", "Compressed size (bytes)", text_handler=humanFilesize)
        yield UInt32(self, "uncompressed_size", "Uncompressed size (bytes)", text_handler=humanFilesize)
        yield Enum(UInt8(self, "host_os", "Operating system used for archiving"), self.OS_NAME)
        yield UInt32(self, "file_crc", "File CRC32", text_handler=hexadecimal)
        yield UInt32(self, "ftime", "Date and time (MS DOS format)", text_handler=timestampMSDOS)
        yield UInt8(self, "version", "RAR version needed to extract file", text_handler=formatRARVersion)
        yield Enum(UInt8(self, "method", "Packing method"), BaseBlock.compression_name)
        yield UInt16(self, "filename_length", "File name size", text_handler=humanFilesize)
        if self["host_os"].value in (0, 2):
            yield MSDOSFileAttr(self, "file_attr", "File attributes")
        else:
            yield UInt32(self, "file_attr", "File attributes", text_handler=hexadecimal)

        if self["is_large"].value:
            yield UInt64(self, "large_size", "Extended 64bits filesize", text_handler=humanFilesize)
        if self["is_unicode"].value: ParserError("Can't handle unicode filenames.")
        if self["has_salt"].value:
            yield UInt8(self, "salt", "Encryption salt value")
        if self["bexttime"].value:
            yield UInt16(self, "time_flags", "Flags for extended time", text_handler=hexadecimal)
            # Needs to be decoded more

        size = self["filename_length"].value
        if size:
            yield String(self, "filename", size, "Filename", charset="ISO-8859-15", truncate="\0")

        # Raw unused data = difference between header_size and what was parsed
        size = self["head_size"].value - (self.current_size//8 + 3)
        if 0 < size:
            yield RawBytes(self, "extra_data", size, "Extra header data")

        # File compressed data
        size = self["compressed_size"].value
        yield RawBytes(self, "compressed_data", size, "File compressed data")
        if self["has_comment"].value:
            yield CommentBlock(self, "comment", "File compressed comment")

    def createDescription(self):
        return "File entry: %s (%s)" % \
            (self["filename"].display, self["compressed_size"].display)


class BlockHead(FieldSet):
    def createFields(self):
      yield UInt16(self, "crc16", "Block CRC16", text_handler=hexadecimal)
      yield Enum(UInt8(self, "type", "Block type"), DefaultBlock.block_name)
      type = self["type"].value

      # Parse now block
      if type == 0x72:
          yield MarkerBlock(self, "marker", "Archive header")
      elif type == 0x73:
          yield ArchiveBlock(self, "archive", "Archive info")
      elif type == 0x74:
          yield FileBlock(self, "file[]")
      elif type == 0x75:
          yield CommentBlock(self, "comment", "Comment associated to a previous block")
      elif type == 0x76:
          yield ExtraInfoBlock(self, "extra_info", "Extra information")
      elif type == 0x77:
          #raise ParserError("Error, stray sub-block.")
          yield SubBlock(self, "subblock", "Subblock associated to a previous block")
      elif type == 0x78:
          yield DefaultBlock(self, "recovery", "Recovery block")
      elif type == 0x79:
          yield DefaultBlock(self, "recovery", "Signature block")
      elif type == 0x80:
          yield DefaultBlock(self, "recovery", "New-format subblock")
      elif type == 0x7B:
          yield EndBlock(self, "end", "End of archive block")
      else:
          yield DefaultBlock(self, "unknown", "Unknown block")

    def createDescription(self):
        return "Block entry: %s" % self["type"].display

class RarFile(Parser):
    MAGIC = MarkerBlock.magic
    tags = {
        "id": "rar",
        "category": "archive",
        "file_ext": ("rar",),
        "mime": ("application/x-rar-compressed", ),
        "min_size": 11*8,
        "magic": ((MAGIC, 0),),
        "description": "Compressed archive in RAR (Roshal ARchive) format"
    }
    endian = LITTLE_ENDIAN

    def validate(self):
        magic = self.MAGIC
        if self.stream.readBytes(0, len(magic)) != magic:
            return "Invalid magic"
        return True

    def createFields(self):
        while not self.eof:
            yield BlockHead(self, "block[]")

