"""
7zip file parser

Informations:
- File 7zformat.txt of 7-zip SDK:
  http://www.7-zip.org/sdk.html

Author: Olivier SCHWAB
Creation date: 6 december 2006
"""

from hachoir_parser import Parser
from hachoir_core.field import (Field, FieldSet,
    GenericVector,
    Enum, UInt8, UInt32, UInt64,
    Bytes, RawBytes, String)
from hachoir_core.endian import LITTLE_ENDIAN
from hachoir_core.text_handler import hexadecimal, humanFilesize

class SZUInt64(Field):
    """
    Variable length UInt64, where the first byte gives both the number of bytes
    needed and the upper byte value.
    """
    def __init__(self, parent, name, max_size=None, description=None):
        Field.__init__(self, parent, name, size=8, description=description)
        value = 0
        addr = self.absolute_address
        mask = 0x80
        firstByte = parent.stream.readBits(addr, 8, LITTLE_ENDIAN)
        for i in xrange(8):
            if not (firstByte & mask):
                value += ((firstByte & (mask-1)) << (8*i))
                break
            value |= parent.stream.readBits(addr, 8, LITTLE_ENDIAN) << (8*i)
            mask >>= 1
            self._size += 8
            addr += 8
        self.createValue = lambda: value

ID_END, ID_HEADER, ID_ARCHIVE_PROPS, ID_ADD_STREAM_INFO, ID_MAIN_STREAM_INFO, \
ID_FILES_INFO, ID_PACK_INFO, ID_UNPACK_INFO, ID_SUBSTREAMS_INFO, ID_SIZE, \
ID_CRC, ID_FOLDER, ID_CODERS_UNPACK_SIZE, ID_NUM_UNPACK_STREAMS, \
ID_EMPTY_STREAM, ID_EMPTY_FILE, ID_ANTI, ID_NAME, ID_CREATION_TIME, \
ID_LAST_ACCESS_TIME, ID_LAST_WRITE_TIME, ID_WIN_ATTR, ID_COMMENT, \
ID_ENCODED_HEADER = xrange(24)

ID_INFO = {
    ID_END               : "End",
    ID_HEADER            : "Header embedding another one",
    ID_ARCHIVE_PROPS     : "Archive Properties",
    ID_ADD_STREAM_INFO   : "Additional Streams Info",
    ID_MAIN_STREAM_INFO  : "Main Streams Info",
    ID_FILES_INFO        : "Files Info",
    ID_PACK_INFO         : "Pack Info",
    ID_UNPACK_INFO       : "Unpack Info",
    ID_SUBSTREAMS_INFO   : "Substreams Info",
    ID_SIZE              : "Size",
    ID_CRC               : "CRC",
    ID_FOLDER            : "Folder",
    ID_CODERS_UNPACK_SIZE: "Coders Unpacked size",
    ID_NUM_UNPACK_STREAMS: "Number of Unpacked Streams",
    ID_EMPTY_STREAM      : "Empty Stream",
    ID_EMPTY_FILE        : "Empty File",
    ID_ANTI              : "Anti",
    ID_NAME              : "Name",
    ID_CREATION_TIME     : "Creation Time",
    ID_LAST_ACCESS_TIME  : "Last Access Time",
    ID_LAST_WRITE_TIME   : "Last Write Time",
    ID_WIN_ATTR          : "Win Attributes",
    ID_COMMENT           : "Comment",
    ID_ENCODED_HEADER    : "Header holding encoded data info",
}

class SkippedData(FieldSet):
    def createFields(self):
        yield Enum(UInt8(self, "id[]"), ID_INFO)
        size = SZUInt64(self, "size")
        yield size
        if size.value > 0:
            yield RawBytes(self, "data", size.value)

def waitForID(self, wait_id, wait_name="waited_id[]"):
    while not self.eof:
        addr = self.absolute_address+self.current_size
        id = self.stream.readBits(addr, 8, LITTLE_ENDIAN)
        if id == wait_id:
            yield Enum(UInt8(self, wait_name), ID_INFO)
            self.info("Found ID %s (%u)" % (ID_INFO[id], id))
            return
        self.info("Skipping ID %u!=%u" % (id, wait_id))
        yield SkippedData(self, "skipped_id[]", "%u != %u" % (id, wait_id))

class HashDigest(FieldSet):
    def __init__(self, parent, name, num_digests, desc=None):
        FieldSet.__init__(self, parent, name, desc)
        self.num_digests = num_digests
    def createFields(self):
        yield Enum(UInt8(self, "id"), ID_INFO)
        bytes = self.stream.readBytes(self.absolute_address, self.num_digests)
        if self.num_digests > 0:
            yield GenericVector(self, "defined[]", self.num_digests, UInt8, "bool")
            for index in xrange(self.num_digests):
                if bytes[index]:
                    yield UInt32(self, "hash[]", "Hash for digest %u" % index, \
                                 text_handler=hexadecimal)

class PackInfo(FieldSet):
    def createFields(self):
        yield Enum(UInt8(self, "id"), ID_INFO)
        yield SZUInt64(self, "pack_pos", "Positions of the packs")
        num = SZUInt64(self, "num_pack_streams")
        yield num
        num = num.value

        for field in waitForID(self, ID_SIZE, "size_marker"):
            yield field

        for size in xrange(num):
            yield SZUInt64(self, "pack_size[]")

        while not self.eof:
            addr = self.absolute_address+self.current_size
            id = self.stream.readBits(addr, 8, LITTLE_ENDIAN)
            if id == ID_END:
                yield Enum(UInt8(self, "end_marker"), ID_INFO)
                break
            elif id == ID_CRC:
                yield HashDigest(self, "hash_digest", size)
            else:
                yield SkippedData(self)

def lzmaParams(value):
    param = value.value
    remainder = param / 9
    # Literal coder context bits
    lc = param % 9
    # Position state bits
    pb = remainder / 5
    # Literal coder position bits
    lp = remainder % 5
    return "lc=%u pb=%u lp=%u" % (lc, lp, pb)

class CoderID(FieldSet):
    CODECS = {
        # Only 2 methods ... and what about PPMD ?
        "\0"     : "Copy",
        "\3\1\1" : "LZMA",
    }
    def createFields(self):
        byte = UInt8(self, "id_size")
        yield byte
        byte = byte.value
        self.info("ID=%u" % byte)
        size = byte & 0xF
        if size > 0:
            name = self.stream.readBytes(self.absolute_address+self.current_size, size)
            if name in self.CODECS:
                name = self.CODECS[name]
                self.info("Codec is %s" % name)
            else:
                self.info("Undetermined codec %s" % name)
                name = None
            yield RawBytes(self, "id", size, name)
        if byte & 0x10:
            yield SZUInt64(self, "num_stream_in")
            yield SZUInt64(self, "num_stream_out")
            self.info("Streams: IN=%u    OUT=%u" % \
                      (self["num_stream_in"].value, self["num_stream_out"].value))
        if byte & 0x20:
            size = SZUInt64(self, "properties_size[]")
            yield size
            if size.value == 5:
                #LzmaDecodeProperties@LZMAStateDecode.c
                yield UInt8(self, "parameters", text_handler=lzmaParams)
                yield UInt32(self, "dictionary_size", text_handler=humanFilesize)
            elif size.value > 0:
                yield RawBytes(self, "properties[]", size.value)

class CoderInfo(FieldSet):
    def __init__(self, parent, name, desc=None):
        FieldSet.__init__(self, parent, name, desc)
        self.in_streams = 1
        self.out_streams = 1
    def createFields(self):
        # The real ID
        addr = self.absolute_address + self.current_size
        b = self.parent.stream.readBits(addr, 8, LITTLE_ENDIAN)
        cid = CoderID(self, "coder_id")
        yield cid
        if b&0x10: # Work repeated, ...
            self.in_streams = cid["num_stream_in"].value
            self.out_streams = cid["num_stream_out"].value

        # Skip other IDs
        while b&0x80:
            addr = self.absolute_address + self.current_size
            b = self.parent.stream.readBits(addr, 8, LITTLE_ENDIAN)
            yield CoderID(self, "unused_codec_id[]")

class BindPairInfo(FieldSet):
    def createFields(self):
        # 64 bits values then cast to 32 in fact
        yield SZUInt64(self, "in_index")
        yield SZUInt64(self, "out_index")
        self.info("Indexes: IN=%u   OUT=%u" % \
                  (self["in_index"].value, self["out_index"].value))

class FolderItem(FieldSet):
    def __init__(self, parent, name, desc=None):
        FieldSet.__init__(self, parent, name, desc)
        self.in_streams = 0
        self.out_streams = 0
    def createFields(self):
        yield SZUInt64(self, "num_coders")
        num = self["num_coders"].value
        self.info("Folder: %u codecs" % num)

        # Coders info
        for index in xrange(num):
            ci = CoderInfo(self, "coder_info[]")
            yield ci
            self.in_streams += ci.in_streams
            self.out_streams += ci.out_streams

        # Bin pairs
        self.info("out streams: %u" % self.out_streams)
        for index in xrange(self.out_streams-1):
            yield BindPairInfo(self, "bind_pair[]")

        # Packed streams
        # @todo: Actually find mapping
        packed_streams = self.in_streams - self.out_streams + 1
        if packed_streams == 1:
            pass
        else:
            for index in xrange(packed_streams):
                yield SZUInt64(self, "pack_stream[]")


class UnpackInfo(FieldSet):
    def createFields(self):
        yield Enum(UInt8(self, "id"), ID_INFO)
        # Wait for synch
        for field in waitForID(self, ID_FOLDER, "folder_marker"):
            yield field
        yield SZUInt64(self, "num_folders")

        # Get generic info
        num = self["num_folders"].value
        self.info("%u folders" % num)
        yield UInt8(self, "is_external")

        # Read folder items
        for folder_index in xrange(num):
            yield FolderItem(self, "folder_item[]")

        # Get unpack sizes for each coder of each folder
        for field in waitForID(self, ID_CODERS_UNPACK_SIZE, "coders_unpsize_marker"):
            yield field
        for folder_index in xrange(num):
            folder_item = self["folder_item[%u]" % folder_index]
            for index in xrange(folder_item.out_streams):
                #yield UInt8(self, "unpack_size[]")
                yield SZUInt64(self, "unpack_size[]")
        
        # Extract digests
        while not self.eof:
            addr = self.absolute_address+self.current_size
            id = self.stream.readBits(addr, 8, LITTLE_ENDIAN)
            if id == ID_END:
                yield Enum(UInt8(self, "end_marker"), ID_INFO)
                break
            elif id == ID_CRC:
                yield HashDigest(self, "hash_digest", num)
            else:
                yield SkippedData(self, "skip_data")

class SubStreamInfo(FieldSet):
    def createFields(self):
        yield Enum(UInt8(self, "id"), ID_INFO)
        ParserError("SubStreamInfo not implemented yet")

class EncodedHeader(FieldSet):
    def createFields(self):
        yield Enum(UInt8(self, "id"), ID_INFO)
        while not self.eof:
            addr = self.absolute_address+self.current_size
            id = self.stream.readBits(addr, 8, LITTLE_ENDIAN)
            if id == ID_END:
                yield Enum(UInt8(self, "end_marker"), ID_INFO)
                break
            elif id == ID_PACK_INFO:
                yield PackInfo(self, "pack_info", ID_INFO[ID_PACK_INFO])
            elif id == ID_UNPACK_INFO:
                yield UnpackInfo(self, "unpack_info", ID_INFO[ID_UNPACK_INFO])
            elif id == ID_SUBSTREAMS_INFO:
                yield SubStreamInfo(self, "substreams_info", ID_INFO[ID_SUBSTREAMS_INFO])
            else:
                self.info("Unexpected ID (%i)" % id)
                break

class IDHeader(FieldSet):
    def createFields(self):
        yield Enum(UInt8(self, "id"), ID_INFO)
        ParserError("IDHeader not implemented")

class NextHeader(FieldSet):
    def __init__(self, parent, name, hdr_size):
        FieldSet.__init__(self, parent, name, "Next header")
        self.hdr_size = hdr_size
    # Less work, as much interpretable information as the other
    # version... what an obnoxious format
    def createFields2(self):
        yield Enum(UInt8(self, "header_type"), ID_INFO)
        yield RawBytes(self, "header_data", self.hdr_size-1)
    def createFields(self):
        id = self.stream.readBits(self.absolute_address, 8, LITTLE_ENDIAN)
        if id == ID_HEADER:
            yield IDHeader(self, "header", ID_INFO[ID_HEADER])
        elif id == ID_ENCODED_HEADER:
            yield EncodedHeader(self, "encoded_hdr", ID_INFO[ID_ENCODED_HEADER])
        else:
            ParserError("Unexpected ID %u" % id)
        size = self.hdr_size - (self.current_size//8)
        if size > 0:
            yield RawBytes(self, "next_hdr_data", size, "Next header's data")

class StartHeader(FieldSet):
    #static_size = 20
    def createFields(self):
        yield UInt64(self, "next_hdr_offset", "NextHeaderOffset")
        yield UInt64(self, "next_hdr_size", "NextHeaderSize")
        yield UInt32(self, "next_hdr_crc", "Next header CRC",
                     text_handler=hexadecimal)

class SignatureHeader(FieldSet):
    #static_size = 32
    def createFields(self):
        yield Bytes(self, "signature", 6, "Signature Header")
        yield UInt8(self, "major_ver", "Archive major version")
        yield UInt8(self, "minor_ver", "Archive minor version")
        yield UInt32(self, "start_hdr_crc", "Start header CRC",
                     text_handler=hexadecimal)
        yield StartHeader(self, "start_hdr", "Start header")

class SevenZipParser(Parser):
    tags = {
        "id": "7zip",
        "category": "archive",
        "file_ext": ("7z",),
        "mime": ("application/x-7z-compressed",),
        "min_size": 32*8,
        "magic": (("7z\xbc\xaf\x27\x1c", 0),),
        "description": "Compressed archive in 7z format"
    }
    endian = LITTLE_ENDIAN

    def createFields(self):
        yield SignatureHeader(self, "signature", "Signature Header")
        size = self["/signature/start_hdr/next_hdr_offset"].value
        if size > 0:
            yield RawBytes(self, "data", size, "Compressed data")
            yield NextHeader(self, "next_hdr",
                             self["/signature/start_hdr/next_hdr_size"].value)

    def validate(self):
        if self.stream.readBytes(0,6) != "7z\xbc\xaf'\x1c":
            return "Invalid signature"
        return True

    def createContentSize(self):
        size = self["/signature/start_hdr/next_hdr_offset"].value
        size += self["/signature/start_hdr/next_hdr_size"].value
        size += 12 # Signature size
        size += 20 # Start header size
        return size*8
