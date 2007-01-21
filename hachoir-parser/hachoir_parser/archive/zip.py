"""
Zip splitter.

Status: can read most important headers
Author: Victor Stinner
"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    Bit, Bits, Enum,
    UInt16, UInt32,
    String, PascalString16,
    NullBits, RawBytes)
from hachoir_core.text_handler import humanFilesize, hexadecimal, timestampMSDOS
from hachoir_core.endian import LITTLE_ENDIAN

# TODO: Merge ZipCentralDirectory and FileEntry (looks very similar)

class ZipCentralDirectory(FieldSet):
    def createFields(self):
        yield UInt16(self, "version_made_by", "Version made by")
        yield UInt16(self, "version_needed", "Version needed")
        yield UInt16(self, "flags", "General purpose flag")
        yield Enum(UInt16(self, "compression", "Compression method"), FileEntry.compression_name)
        yield UInt32(self, "last_mod", "Last moditication file time", text_handler=timestampMSDOS)
        yield UInt32(self, "crc32", "CRC-32", text_handler=hexadecimal)
        yield UInt32(self, "compressed_size", "Compressed size")
        yield UInt32(self, "uncompressed_size", "Uncompressed size")
        yield UInt16(self, "filename_length", "Filename length")
        yield UInt16(self, "extra_length", "Extra fields length")
        yield UInt16(self, "comment_length", "File comment length")
        yield UInt16(self, "disk_number_start", "Disk number start")
        yield UInt16(self, "internal_attr", "Internal file attributes")
        yield UInt32(self, "external_attr", "External file attributes")
        yield UInt32(self, "offset_header", "Relative offset of local header")
        yield String(self, "filename", self["filename_length"].value, "Filename") # TODO: charset?
        if 0 < self["extra_length"].value:
            yield RawBytes(self, "extra", self["extra_length"].value, "Extra fields")
        if 0 < self["comment_length"].value:
            yield String(self, "comment", self["comment_length"].value, "Comment") # TODO: charset?

    def createDescription(self):
        return "Central directory: %s" % self["filename"].value

class ZipEndCentralDirectory(FieldSet):
    def createFields(self):
        yield UInt16(self, "number_disk", "Number of this disk")
        yield UInt16(self, "number_disk2", "Number of this disk2")
        yield UInt16(self, "total_number_disk", "Total number of entries")
        yield UInt16(self, "total_number_disk2", "Total number of entries2")
        yield UInt32(self, "size", "Size of the central directory")
        yield UInt32(self, "offset", "Offset of start of central directory")
        yield PascalString16(self, "comment", "ZIP comment")

class FileEntry(FieldSet):
    compression_name = {
        0: "no compression",
        1: "Shrunk",
        2: "Reduced (factor 1)",
        3: "Reduced (factor 2)",
        4: "Reduced (factor 3)",
        5: "Reduced (factor 4)",
        6: "Imploded",
        7: "Tokenizing",
        8: "Deflate",
        9: "Deflate64",
        10: "PKWARE Imploding"
    }

    def createFields(self):
        yield UInt16(self, "version", "Version")
        yield Bit(self, "is_encrypted", "File is encrypted?")
        yield Bit(self, "use_8k_sliding", "Use 8K sliding dictionnary (instead of 4K)")
        yield Bit(self, "use_3shannon", "Use a 3 Shannon-Fano tree (instead of 2 Shannon-Fano)")
        yield Bit(self, "use_data_desc", "Use data descriptor?")
        yield NullBits(self, "reserved", 1, "Reserved")
        yield Bit(self, "is_patched", "File is compressed with patched data?")
        yield NullBits(self, "unused", 6, "Unused bits")
        yield Bits(self, "pkware", 4, "Reserved by PKWARE")

        yield Enum(UInt16(self, "compression", "Compression method"), self.compression_name)
        yield UInt32(self, "last_mod", "Last modification time", text_handler=timestampMSDOS)
        yield UInt32(self, "crc32", "Checksum (CRC32)", text_handler=hexadecimal)
        yield UInt32(self, "compressed_size", "Compressed size (bytes)", text_handler=humanFilesize)
        yield UInt32(self, "uncompressed_size", "Uncompressed size (bytes)", text_handler=humanFilesize)
        yield UInt16(self, "filename_length", "Filename length")
        yield UInt16(self, "extra_length", "Extra length")
        if self["filename_length"].value:
            yield String(self, "filename", self["filename_length"].value, "Filename") # TODO: charset?
        if self["extra_length"].value:
            yield RawBytes(self, "extra", self["extra_length"].value, "Extra")
        if self["compressed_size"].value:
            # TODO: Use SubFile field type with deflate stream
            yield RawBytes(self, "compressed_data", self["compressed_size"].value, "Compressed data")
        if self["use_data_desc"].value:
            yield UInt32(self, "file_crc32", "Checksum (CRC32)", text_handler=hexadecimal)
            yield UInt32(self, "file_compressed_size", "Compressed size (bytes)", text_handler=humanFilesize)
            yield UInt32(self, "file_uncompressed_size", "Uncompressed size (bytes)", text_handler=humanFilesize)

    def createDescription(self):
        return "File entry: %s (%s)" % \
            (self["filename"].value, self["compressed_size"].display)

class ZipFile(Parser):
    endian = LITTLE_ENDIAN
    MIME_TYPES = {
        # Default ZIP archive
        "application/zip": "zip",
        "application/x-zip": "zip",

        # Java archive (JAR)
        "application/x-jar": "jar",
        "application/java-archive": "jar",

        # OpenOffice 1.0
        "application/vnd.sun.xml.calc": "sxc",
        "application/vnd.sun.xml.draw": "sxd",
        "application/vnd.sun.xml.impress": "sxi",
        "application/vnd.sun.xml.writer": "sxw",
        "application/vnd.sun.xml.math": "sxm",

        # OpenOffice 1.0 (template)
        "application/vnd.sun.xml.calc.template": "stc",
        "application/vnd.sun.xml.draw.template": "std",
        "application/vnd.sun.xml.impress.template": "sti",
        "application/vnd.sun.xml.writer.template": "stw",
        "application/vnd.sun.xml.writer.global": "sxg",

        # OpenDocument
        "application/vnd.oasis.opendocument.chart": "odc",
        "application/vnd.oasis.opendocument.image": "odi",
        "application/vnd.oasis.opendocument.database": "odb",
        "application/vnd.oasis.opendocument.formula": "odf",
        "application/vnd.oasis.opendocument.graphics": "odg",
        "application/vnd.oasis.opendocument.presentation": "odp",
        "application/vnd.oasis.opendocument.spreadsheet": "ods",
        "application/vnd.oasis.opendocument.text": "odt",
        "application/vnd.oasis.opendocument.text-master": "odm",

        # OpenDocument (template)
        "application/vnd.oasis.opendocument.graphics-template": "otg",
        "application/vnd.oasis.opendocument.presentation-template": "otp",
        "application/vnd.oasis.opendocument.spreadsheet-template": "ots",
        "application/vnd.oasis.opendocument.text-template": "ott",
    }
    tags = {
        "id": "zip",
        "category": "archive",
        "file_ext": list(set(MIME_TYPES.values())),
        "mime": MIME_TYPES.keys(),
# FIXME: Re-enable magic
#        "magic": (("PK\3\4", 0),),
        "min_size": (4 + 26)*8, # header + file entry
        "description": "ZIP archive"
    }

    def validate(self):
        if self["header[0]"].value != 0x04034B50:
            return "Invalid magic"
        return True

    def createFields(self):
        # File data
        self.signature = None
        self.central_directory = []
        while not self.eof:
            header = UInt32(self, "header[]", "Header", text_handler=hexadecimal)
            yield header
            header = header.value
            if header == 0x04034B50:
                yield FileEntry(self, "file[]")
            elif header == 0x02014b50:
                yield ZipCentralDirectory(self, "central_directory[]")
            elif header == 0x06054b50:
                yield ZipEndCentralDirectory(self, "end_central_directory", "End of central directory")
            elif header == 0x05054b50:
                yield PascalString16(self, "signature", "Signature")
            else:
                raise ParserError("Error, unknown ZIP header (0x%08X)." % header)

    def createMimeType(self):
        if self["file[0]/filename"].value == "mimetype":
            return self["file[0]/compressed_data"].value
        else:
            return "application/zip"

    def createFilenameSuffix(self):
        if self["file[0]/filename"].value == "mimetype":
            mime = self["file[0]/compressed_data"].value
            if mime in self.MIME_TYPES:
                return "." + self.MIME_TYPES[mime]
        return ".zip"

    def createContentSize(self):
        end = self.stream.searchBytes("PK\5\6", 0)
        if end is not None:
            return end + 22*8
        return None

