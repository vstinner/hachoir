"""
Zip splitter.

Status: can read most important headers
Author: Victor Stinner
"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    Bit, Bits, Enum,
    UInt8, UInt16, UInt32,
    String, PascalString16,
    NullBits, RawBytes)
from hachoir_core.text_handler import humanFilesize, hexadecimal, timestampMSDOS
from hachoir_core.endian import LITTLE_ENDIAN
from hachoir_core.error import info

def ZipRevision(field):
    return "%u.%u" % divmod(field.value, 10)

# TODO: Merge ZipCentralDirectory and FileEntry (looks very similar)
class ZipVersion(FieldSet):
    static_size = 16
    HOST_OS = {
        0: "FAT file system (DOS, OS/2, NT)",
        1: "Amiga",
        2: "VMS (VAX or Alpha AXP)",
        3: "Unix",
        4: "VM/CMS",
        5: "Atari",
        6: "HPFS file system (OS/2, NT 3.x)",
        7: "Macintosh",
        8: "Z-System",
        9: "CP/M",
        10: "TOPS-20",
        11: "NTFS file system (NT)",
        12: "SMS/QDOS",
        13: "Acorn RISC OS",
        14: "VFAT file system (Win95, NT)",
        15: "MVS",
        16: "BeOS (BeBox or PowerMac)",
        17: "Tandem",
        18: "unused",
    }
    def createFields(self):
        yield UInt8(self, "zip_version", "ZIP version", text_handler=ZipRevision)
        yield Enum(UInt8(self, "host_os", "ZIP Host OS"), self.HOST_OS)

class ZipGeneralFlags(FieldSet):
    static_size = 16
    def createFields(self):
        yield Bits(self, "unused[]", 8, "Unused")
        yield Bits(self, "reserved", 2, "Reserved for internal state")
        yield Bit(self, "is_patched", "File is compressed with patched data?")
        yield Bit(self, "unused[]", "Unused")
        yield Bit(self, "has_descriptor",
                  "Compressed data followed by descriptor?")
        # Need the compression info from the parent, and that is the byte following
        yield Bits(self, "compression_info", 2, "Depends on method",
                   text_handler=hexadecimal)
        yield Bit(self, "is_encrypted", "File is encrypted?")

class ExtraField(FieldSet):
    EXTRA_FIELD_ID = {
        0x0007: "AV Info",
        0x0009: "OS/2 extended attributes      (also Info-ZIP)",
        0x000a: "PKWARE Win95/WinNT FileTimes  [undocumented!]",
        0x000c: "PKWARE VAX/VMS                (also Info-ZIP)",
        0x000d: "PKWARE Unix",
        0x000f: "Patch Descriptor",
        0x07c8: "Info-ZIP Macintosh (old, J. Lee)",
        0x2605: "ZipIt Macintosh (first version)",
        0x2705: "ZipIt Macintosh v 1.3.5 and newer (w/o full filename)",
        0x334d: "Info-ZIP Macintosh (new, D. Haase Mac3 field)",
        0x4341: "Acorn/SparkFS (David Pilling)",
        0x4453: "Windows NT security descriptor (binary ACL)",
        0x4704: "VM/CMS",
        0x470f: "MVS",
        0x4b46: "FWKCS MD5 (third party, see below)",
        0x4c41: "OS/2 access control list (text ACL)",
        0x4d49: "Info-ZIP VMS (VAX or Alpha)",
        0x5356: "AOS/VS (binary ACL)",
        0x5455: "extended timestamp",
        0x5855: "Info-ZIP Unix (original; also OS/2, NT, etc.)",
        0x6542: "BeOS (BeBox, PowerMac, etc.)",
        0x756e: "ASi Unix",
        0x7855: "Info-ZIP Unix (new)",
        0xfb4a: "SMS/QDOS"
    }
    def createFields(self):
        yield Enum(UInt16(self, "field_id", "Extra field ID"),
                   self.EXTRA_FIELD_ID)
        size = UInt16(self, "field_data_size", "Extra field data size")
        yield size
        if size.value > 0:
            yield RawBytes(self, "field_data", size, "Unknown field data")

def ZipStartCommonFields(self):
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
    yield ZipVersion(self, "version_needed", "Version needed")
    yield ZipGeneralFlags(self, "flags", "General purpose flag")
    yield Enum(UInt16(self, "compression", "Compression method"),
               compression_name)
    yield UInt32(self, "last_mod", "Last moditication file time",
                 text_handler=timestampMSDOS)
    yield UInt32(self, "crc32", "CRC-32", text_handler=hexadecimal)
    yield UInt32(self, "compressed_size", "Compressed size")
    yield UInt32(self, "uncompressed_size", "Uncompressed size")
    yield UInt16(self, "filename_length", "Filename length")
    yield UInt16(self, "extra_length", "Extra fields length")

class ZipCentralDirectory(FieldSet):
    HEADER = 0x02014b50
    def createFields(self):
        yield ZipVersion(self, "version_made_by", "Version made by")
        for field in ZipStartCommonFields(self):
            yield field
        yield UInt16(self, "comment_length", "Comment length")
        yield UInt16(self, "disk_number_start", "Disk number start")
        yield UInt16(self, "internal_attr", "Internal file attributes")
        yield UInt32(self, "external_attr", "External file attributes")
        yield UInt32(self, "offset_header", "Relative offset of local header")
        yield String(self, "filename", self["filename_length"].value,
                     "Filename") # TODO: charset?
        if 0 < self["extra_length"].value:
            yield RawBytes(self, "extra", self["extra_length"].value,
                           "Extra fields")
        if 0 < self["comment_length"].value:
            yield String(self, "comment", self["comment_length"].value,
                         "Comment") # TODO: charset?

    def createDescription(self):
        return "Central directory: %s" % self["filename"].value

class Zip64EndCentralDirectory(FieldSet):
    HEADER = 0x06064b50
    def createFields(self):
        yield UInt64(self, "zip64_end_size",
                     "Size of zip64 end of central directory record")
        yield ZipVersion(self, "version_made_by", "Version made by")
        yield ZipVersion(self, "version_needed", "Version needed to extract")
        yield UInt32(self, "number_disk", "Number of this disk")
        yield UInt32(self, "number_disk2",
                     "Number of the disk with the start of the central directory")
        yield UInt64(self, "number_entries",
                     "Total number of entries in the central directory on this disk")
        yield UInt64(self, "number_entrie2",
                     "Total number of entries in the central directory")
        yield UInt64(self, "size", "Size of the central directory")
        yield UInt64(self, "offset", "Offset of start of central directory")
        if 0 < self["zip64_end_size"].value:
            yield RawBytes(self, "data_sector", self["zip64_end_size"].value,
                           "zip64 extensible data sector")

class ZipEndCentralDirectory(FieldSet):
    HEADER = 0x06054b50
    def createFields(self):
        yield UInt16(self, "number_disk", "Number of this disk")
        yield UInt16(self, "number_disk2", "Number in the central dir")
        yield UInt16(self, "total_number_disk",
                     "Total number of entries in this disk")
        yield UInt16(self, "total_number_disk2",
                     "Total number of entries in the central dir")
        yield UInt32(self, "size", "Size of the central directory")
        yield UInt32(self, "offset", "Offset of start of central directory")
        yield PascalString16(self, "comment", "ZIP comment")

class ZipDataDescriptor(FieldSet):
    HEADER_STRING = "\x50\x4B\x07\x08"
    HEADER = 0x08074B50
    static_size = 96
    def createFields(self):
        yield UInt32(self, "file_crc32", "Checksum (CRC32)",
                     text_handler=hexadecimal)
        yield UInt32(self, "file_compressed_size", "Compressed size (bytes)",
                     text_handler=humanFilesize)
        yield UInt32(self, "file_uncompressed_size",
                     "Uncompressed size (bytes)", text_handler=humanFilesize)

class FileEntry(FieldSet):
    HEADER = 0x04034B50
    def Resynch(self):
        info("Trying to resynch...")
        # Non-seekable output, search the next data descriptor
        len = self.stream.searchBytesLength(ZipDataDescriptor.HEADER_STRING, False,
                                            self.absolute_address+self.current_size)
        if len > 0:
            yield RawBytes(self, "compressed_data", len, "Compressed data")
            yield UInt32(self, "header[]", "Header", text_handler=hexadecimal)
            data_desc = ZipDataDescriptor(self, "data_desc", "Data descriptor")
            if data_desc["file_compressed_size"].value == len:
                info("Resynched!")
                yield data_desc
                return
            raise ParserError("Bad resynch: %i != %i" % \
                              (len, data_desc["file_compressed_size"].value))
        raise ParserError("Couldn't resynch to %s" %
                          ZipDataDescriptor.HEADER_STRING)
    def createFields(self):
        for field in ZipStartCommonFields(self):
            yield field
        if self["filename_length"].value:
            yield String(self, "filename", self["filename_length"].value,
                         "Filename") # TODO: charset?
        if self["extra_length"].value:
            yield RawBytes(self, "extra", self["extra_length"].value, "Extra")
        if self["compressed_size"].value:
            # TODO: Use SubFile field type with deflate stream
            if self["compression"].value == 0:
                yield String(self, "data", self["compressed_size"].value,
                             "Uncompressed data")
            else:
                yield RawBytes(self, "compressed_data",
                               self["compressed_size"].value, "Compressed data")
        elif not self["crc32"].value:
            for field in self.Resynch():
                yield field
        if self["flags/has_descriptor"].value:
            yield ZipDataDescriptor(self, "data_desc", "Data descriptor")

    def createDescription(self):
        return "File entry: %s (%s)" % \
            (self["filename"].value, self["compressed_size"].display)

class ZipSignature(FieldSet):
    HEADER = 0x05054B50
    def createFields(self):
        yield PascalString16(self, "signature", "Signature")

class Zip64EndCentralDirectoryLocator(FieldSet):
    HEADER = 0x07064b50
    def createFields(self):
        yield UInt32(self, "disk_number", \
                     "Number of the disk with the start of the zip64 end of central directory")
        yield UInt64(self, "relative_offset", \
                     "Relative offset of the zip64 end of central directory record")
        yield UInt32(self, "disk_total_number", "Total number of disks")


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
        if self["header[0]"].value != FileEntry.HEADER:
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
            if header == FileEntry.HEADER:
                yield FileEntry(self, "file[]")
            elif header == ZipDataDescriptor.HEADER:
                yield ZipDataDescriptor(self, "spanning[]")
            elif header == 0x30304b50:
                yield ZipDataDescriptor(self, "temporary_spanning[]")
            elif header == ZipCentralDirectory.HEADER:
                yield ZipCentralDirectory(self, "central_directory[]")
            elif header == ZipEndCentralDirectory.HEADER:
                yield ZipEndCentralDirectory(self, "end_central_directory", "End of central directory")
            elif header == Zip64EndCentralDirectory.HEADER:
                yield Zip64EndCentralDirectory(self, "end64_central_directory", "ZIP64 end of central directory")
            elif header == ZipSignature.HEADER:
                yield ZipSignature(self, "signature", "Signature")
            elif header == Zip64EndCentralDirectoryLocator.HEADER:
                yield Zip64EndCentralDirectoryLocator(self, "end_locator", "ZIP64 Enf of central directory locator")
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

