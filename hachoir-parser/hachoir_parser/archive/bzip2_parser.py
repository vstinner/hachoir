"""
BZIP2 archive file

Author: Victor Stinner
"""

from hachoir_parser import Parser
from hachoir_core.field import (ParserError, String,
    Character, UInt8, UInt32, SubFile, CompressedField)
from hachoir_core.endian import LITTLE_ENDIAN
from hachoir_core.text_handler import hexadecimal

try:
    from bz2 import BZ2Decompressor

    class Bunzip2:
        def __init__(self, stream):
            self.bzip2 = BZ2Decompressor()

        def __call__(self, size, data=''):
            return self.bzip2.decompress(data)

    has_deflate = True
except ImportError:
    has_deflate = False

class Bzip2Parser(Parser):
    tags = {
        "id": "bzip2",
        "category": "archive",
        "file_ext": ("bz2",),
        "mime": ["application/x-bzip2"],
        "min_size": 10*8,
        "magic": (('BZh', 0),),
        "description": "bzip2 archive"
    }
    endian = LITTLE_ENDIAN

    def validate(self):
        if self.stream.readBytes(0, 3) != 'BZh':
            return "Wrong file signature"
        if not("1" <= self["blocksize"].value <= "9"):
            return "Wrong blocksize"
        return True

    def createFields(self):
        yield String(self, "id", 3, "Identifier (BZh)", charset="ASCII")
        yield Character(self, "blocksize", "Block size (KB of memory needed to uncompress)")

        yield UInt8(self, "blockheader", "Block header")
        if self["blockheader"].value == 0x17:
            yield String(self, "id2", 4, "Identifier2 (re8P)", charset="ASCII")
            yield UInt8(self, "id3", "Identifier3 (0x90)")
        elif self["blockheader"].value == 0x31:
            yield String(self, "id2", 5, "Identifier 2 (AY&SY)", charset="ASCII")
            if self["id2"].value != "AY&SY":
                raise ParserError("Invalid identifier 2 (AY&SY)!")
        else:
            raise ParserError("Invalid block header!")
        yield UInt32(self, "crc32", "CRC32", text_handler=hexadecimal)

        if self._size is None: # TODO: is it possible to handle piped input?
            raise NotImplementedError

        size = (self._size - self.current_size)/8
        if size:
            try:
                filename = self.stream.filename
                if filename and filename.endswith(".bz2"):
                    filename = filename[:-4]
                else:
                    filename = None
            except AttributeError:
                filename = None
            data = SubFile(self, "file", size, filename=filename)
            if has_deflate:
                CompressedField(self, Bunzip2)
                data._createInputStream = lambda: self._createInputStream()
            yield data

