"""
7zip file parser

Informations:
- File 7zformat.txt of 7-zip SDK:
  http://www.7-zip.org/sdk.html

Author: Olivier SCHWAB
Creation date: 6 december 2006
"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, StaticFieldSet,
    MatchError,
    Bit, UInt8,UInt16, UInt32,UInt64,
    Bytes, String, Enum,
    PaddingBytes)
from hachoir_core.endian import LITTLE_ENDIAN
from hachoir_core.text_handler import hexadecimal

class StartHeader(FieldSet):
    def createFields(self):
        yield UInt64(self, "next_hdr_offset","NextHeaderOffset")
        yield UInt64(self, "next_hdr_size","NextHeaderSize")
        yield UInt32(self, "next_hder_crc","Next header CRC", text_handler=hexadecimal)

class SignatureHeader(FieldSet):
    def createFields(self):
        yield Bytes(self, "signature", 6,"Signature Header")
        yield UInt8(self, "major_ver","Archive major version")
        yield UInt8(self, "minor_ver","Archive minor version")
        yield UInt32(self, "start_hdr_crc","Start header CRC", text_handler=hexadecimal)
        yield StartHeader(self,"start_hdr","Start header")

class SevenZipParser(Parser):
    tags = {
        "file_ext": ("7z",),
        "mime": ("application/x-7z-compressed",),
        "min_size": 6*8,
        "magic": (("7z\xbc\xaf\x27\x1c", 0),),
        "description": "Compressed archive in 7z format"
    }
    endian = LITTLE_ENDIAN

    def createFields(self):
        yield SignatureHeader(self, "signature", "Signature Header")

        size = (self.size - self.current_size) // 8
        if size:
            yield Bytes(self, "code", size)

    def validate(self):
        if self.stream.readBytes(0,6) != "7z\xbc\xaf'\x1c":
            return "Invalid signature"
        return True

