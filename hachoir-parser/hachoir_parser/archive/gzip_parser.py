"""
GZIP archive parser.

Author: Victor Stinner
"""

from hachoir_parser import Parser
from hachoir_core.field import (
    UInt8, UInt16, UInt32, Enum,
    Bit, CString, SubFile, CompressedField,
    NullBits, Bytes, RawBytes)
from hachoir_core.text_handler import hexadecimal, humanFilesize, timestampUNIX
from hachoir_core.endian import LITTLE_ENDIAN
from hachoir_core.tools import makeUnicode

try:
    from zlib import decompressobj, MAX_WBITS

    class Gunzip:
        def __init__(self, stream):
            self.gzip = decompressobj(-MAX_WBITS)

        def __call__(self, size, data=None):
            if data is None:
                data = self.gzip.unconsumed_tail
            return self.gzip.decompress(data, size)

    has_deflate = True
except ImportError:
    has_deflate = False

class GzipParser(Parser):
    endian = LITTLE_ENDIAN
    tags = {
        "id": "gzip",
        "category": "archive",
        "file_ext": ("gz",),
        "mime": ["application/x-gzip"],
        "min_size": 18*8,
        "magic": (
            # (magic, compression=deflate)
            ('\x1F\x8B\x08', 0),
        ),
        "description": u"gzip archive"
    }
    os_name = {
        0: "FAT filesystem",
        1: "Amiga",
        2: "VMS (or OpenVMS)",
        3: "Unix",
        4: "VM/CMS",
        5: "Atari TOS",
        6: "HPFS filesystem (OS/2, NT)",
        7: "Macintosh",
        8: "Z-System",
        9: "CP/M",
        10: "TOPS-20",
        11: "NTFS filesystem (NT)",
        12: "QDOS",
        13: "Acorn RISCOS",
    }
    COMPRESSION_NAME = {
        8: "deflate",
    }

    def validate(self):
        if self["signature"].value != '\x1F\x8B':
            return "Invalid signature"
        if self["compression"].value not in self.COMPRESSION_NAME:
            return "Unkown compression method (%u)" % self["compression"].value
        if self["reserved[0]"].value != 0:
            return "Invalid reserved[0] value"
        if self["reserved[1]"].value != 0:
            return "Invalid reserved[1] value"
        if self["reserved[2]"].value != 0:
            return "Invalid reserved[2] value"
        return True

    def createFields(self):
        # Gzip header
        yield Bytes(self, "signature", 2, r"GZip file signature (\x1F\x8B)")
        yield Enum(UInt8(self, "compression", "Compression method"), self.COMPRESSION_NAME)

        # Flags
        yield Bit(self, "is_text", "File content is probably ASCII text")
        yield Bit(self, "has_crc16", "Header CRC16")
        yield Bit(self, "has_extra", "Extra informations (variable size)")
        yield Bit(self, "has_filename", "Contains filename?")
        yield Bit(self, "has_comment", "Contains comment?")
        yield NullBits(self, "reserved[]", 3)
        yield UInt32(self, "mtime", "Modification time",
            text_handler=timestampUNIX)

        # Extra flags
        yield NullBits(self, "reserved[]", 1)
        yield Bit(self, "slowest", "Compressor used maximum compression (slowest)")
        yield Bit(self, "fastest", "Compressor used the fastest compression")
        yield NullBits(self, "reserved[]", 5)
        yield Enum(UInt8(self, "os", "Operating system"), self.os_name)

        # Optional fields
        if self["has_extra"].value:
            yield UInt16(self, "extra_length", "Extra length")
            yield RawBytes(self, "extra", self["extra_length"].value, "Extra")
        if self["has_filename"].value:
            yield CString(self, "filename", "Filename")
        if self["has_comment"].value:
            yield CString(self, "comment", "Comment")
        if self["has_crc16"].value:
            yield UInt16(self, "hdr_crc16", "CRC16 of the header",
                text_handler=hexadecimal)

        if self._size is None: # TODO: is it possible to handle piped input?
            raise NotImplementedError()

        # Read file
        size = (self._size - self.current_size) // 8 - 8  # -8: crc32+size
        if 0 < size:
            if self["has_filename"].value:
                filename = self["filename"].value
            else:
                for tag, filename in self.stream.tags:
                    if tag == "filename" and filename.endswith(".gz"):
                        filename = filename[:-3]
                        break
                else:
                    filename = None
            data = SubFile(self, "file", size, filename=filename)
            if has_deflate:
                CompressedField(data, Gunzip)
            yield data

        # Footer
        yield UInt32(self, "crc32", "Uncompressed data content CRC32",
            text_handler=hexadecimal)
        yield UInt32(self, "size", "Uncompressed size",
            text_handler=humanFilesize)

    def createDescription(self):
        desc = self.tags["description"]
        info = []
        if "filename" in self:
            filename = makeUnicode(self["filename"].value)
            info.append('filename "%s"' % filename)
        if "size" in self:
            info.append("was %s" % humanFilesize(self["size"]))
        if self["mtime"].value:
            info.append(self["mtime"].display)
        return "%s: %s" % (desc, ", ".join(info))

