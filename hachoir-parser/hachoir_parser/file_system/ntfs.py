"""
New Technology File System (NTFS) file system parser.

Sources:
- The NTFS documentation
  http://www.linux-ntfs.org/
- NTFS-3G driver
  http://www.ntfs-3g.org/

Creation date: 3rd january 2007
Author: Victor Stinner
"""

SECTOR_SIZE = 512

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, Enum,
    UInt8, UInt16, UInt32, UInt64, TimestampWin64,
    String, Bytes, Bit,
    NullBits, NullBytes, PaddingBytes, RawBytes)
from hachoir_core.endian import LITTLE_ENDIAN
from hachoir_core.text_handler import hexadecimal, humanFilesize
from hachoir_core.tools import humanFilesize as doHumanFilesize, createDict
from hachoir_parser.common.msdos import MSDOSFileAttr

class BiosParameterBlock(FieldSet):
    """
    BIOS parameter block (bpb) structure
    """
    static_size = 25 * 8
    MEDIA_TYPE = {0xf8: "Hard disk"}

    def createFields(self):
        yield UInt16(self, "bytes_per_sector", "Size of a sector in bytes")
	yield UInt8(self, "sectors_per_cluster", "Size of a cluster in sectors")
	yield NullBytes(self, "reserved_sectors", 2)
	yield NullBytes(self, "fats", 1)
	yield NullBytes(self, "root_entries", 2)
	yield NullBytes(self, "sectors", 2)
	yield Enum(UInt8(self, "media_type"), self.MEDIA_TYPE)
	yield NullBytes(self, "sectors_per_fat", 2)
	yield UInt16(self, "sectors_per_track")
	yield UInt16(self, "heads")
	yield UInt32(self, "hidden_sectors")
	yield NullBytes(self, "large_sectors", 4)

    def validate(self):
        if self["bytes_per_sector"].value not in (256, 512, 1024, 2048, 4096):
            return "Invalid sector size (%u bytes)" % \
                self["bytes_per_sector"].value
        if self["sectors_per_cluster"].value not in (1, 2, 4, 8, 16, 32, 64, 128):
            return "Invalid cluster size (%u sectors)" % \
                self["sectors_per_cluster"].value
        return ""

class MasterBootRecord(FieldSet):
    static_size = 512*8
    def createFields(self):
        yield Bytes(self, "jump", 3, "Intel x86 jump instruction")
        yield String(self, "name", 8)
        yield BiosParameterBlock(self, "bios", "BIOS parameters")

        yield UInt8(self, "physical_drive", "(0x80)", text_handler=hexadecimal)
        yield NullBytes(self, "current_head", 1)
        yield UInt8(self, "ext_boot_sig", "Extended boot signature (0x80)", text_handler=hexadecimal)
        yield NullBytes(self, "unused", 1)

        yield UInt64(self, "nb_sectors")
        yield UInt64(self, "mft_cluster", "Cluster location of MFT data")
        yield UInt64(self, "mftmirr_cluster", "Cluster location of copy of MFT")
        yield UInt8(self, "cluster_per_mft", "MFT record size in clusters")
        yield NullBytes(self, "reserved[]", 3)
        yield UInt8(self, "cluster_per_index", "Index block size in clusters")
        yield NullBytes(self, "reserved[]", 3)
        yield UInt64(self, "serial_number", text_handler=hexadecimal)
        yield UInt32(self, "checksum", "Boot sector checksum", text_handler=hexadecimal)
        yield Bytes(self, "boot_code", 426)
        yield Bytes(self, "mbr_magic", 2, r"Master boot record magic number (\x55\xAA)")

    def createDescription(self):
        size = self["nb_sectors"].value * self["bios/bytes_per_sector"].value
        return "NTFS Master Boot Record (%s)" % doHumanFilesize(size)

class MFT_Flags(FieldSet):
    static_size = 16
    def createFields(self):
        yield Bit(self, "in_use")
        yield Bit(self, "is_directory")
        yield NullBits(self, "padding", 14)

class Attribute(FieldSet):
    # --- Common code ---
    def __init__(self, *args):
        FieldSet.__init__(self, *args)
        self._size = self["size"].value * 8
        type = self["type"].value
        if type in self.ATTR_INFO:
            self._parser = self.ATTR_INFO[type][1]

    def createFields(self):
        yield Enum(UInt32(self, "type", text_handler=hexadecimal), self.ATTR_NAME)
        yield UInt32(self, "size")
        yield UInt8(self, "non_resident", "Non-resident flag")
        yield UInt8(self, "name_length", "Name length in bytes")
        yield UInt16(self, "name_offset", "Name offset")
        yield UInt16(self, "flags")
        yield UInt16(self, "attribute_id", text_handler=hexadecimal)
        yield UInt32(self, "length_attr", "Length of the Attribute")
        yield UInt16(self, "offset_attr", "Offset of the Attribute")
        yield UInt8(self, "indexed_flag")
        yield NullBytes(self, "padding", 1)
        size = self["length_attr"].value
        if size:
            if self._parser:
                for field in self._parser(self):
                    yield field
            else:
                yield RawBytes(self, "data", size)
        size = (self.size - self.current_size) // 8
        if size:
            yield PaddingBytes(self, "end_padding", size)

    def createDescription(self):
        return "Attribute %s" % self["type"].display
    FILENAME_NAMESPACE = {
        0: "POSIX",
        1: "Win32",
        2: "DOS",
        3: "Win32 & DOS",
    }

    # --- Parser specific to a type ---
    def parseStandardInfo(self):
        yield TimestampWin64(self, "ctime", "File Creation")
        yield TimestampWin64(self, "atime", "File Altered")
        yield TimestampWin64(self, "mtime", "MFT Changed")
        yield TimestampWin64(self, "rtime", "File Read")
        yield MSDOSFileAttr(self, "file_attr", "DOS File Permissions")
        yield UInt32(self, "max_version", "Maximum Number of Versions")
        yield UInt32(self, "version", "Version Number")
        yield UInt32(self, "class_id")
        yield UInt32(self, "owner_id")
        yield UInt32(self, "security_id")
        yield UInt64(self, "quota_charged", "Quota Charged", text_handler=humanFilesize)
        yield UInt64(self, "usn", "Update Sequence Number (USN)")

    def parseFilename(self):
        yield UInt64(self, "ref", "File reference to the parent directory")
        yield TimestampWin64(self, "ctime", "File Creation")
        yield TimestampWin64(self, "atime", "File Altered")
        yield TimestampWin64(self, "mtime", "MFT Changed")
        yield TimestampWin64(self, "rtime", "File Read")
        yield UInt64(self, "alloc_size", "Allocated size of the file", text_handler=humanFilesize)
        yield UInt64(self, "real_size", "Real size of the file", text_handler=humanFilesize)
        yield UInt32(self, "file_flags")
        yield UInt32(self, "file_flags2", "Used by EAs and Reparse")
        yield UInt8(self, "filename_length", "Filename length in characters")
        yield Enum(UInt8(self, "filename_namespace"), self.FILENAME_NAMESPACE)
        size = self["filename_length"].value * 2
        if size:
            yield String(self, "filename", size, charset="UTF-16-LE")

    # --- Type information ---
    ATTR_INFO = {
         0x10: ('STANDARD_INFORMATION ', parseStandardInfo),
         0x20: ('ATTRIBUTE_LIST ', None),
         0x30: ('FILE_NAME ', parseFilename),
         0x40: ('VOLUME_VERSION', None),
         0x40: ('OBJECT_ID ', None),
         0x50: ('SECURITY_DESCRIPTOR ', None),
         0x60: ('VOLUME_NAME ', None),
         0x70: ('VOLUME_INFORMATION ', None),
         0x80: ('DATA ', None),
         0x90: ('INDEX_ROOT ', None),
         0xA0: ('INDEX_ALLOCATION ', None),
         0xB0: ('BITMAP ', None),
         0xC0: ('SYMBOLIC_LINK', None),
         0xC0: ('REPARSE_POINT ', None),
         0xD0: ('EA_INFORMATION ', None),
         0xE0: ('EA ', None),
         0xF0: ('PROPERTY_SET', None),
        0x100: ('LOGGED_UTILITY_STREAM', None),
    }
    ATTR_NAME = createDict(ATTR_INFO, 0)

class MFT(FieldSet):
#    static_size = 48*8
    def createFields(self):
        yield Bytes(self, "signature", 4, "Usually the magic is 'FILE'")
        yield UInt16(self, "usa_ofs", "Update Sequence Array offset")
        yield UInt16(self, "usa_count", "Update Sequence Array count")
        yield UInt64(self, "lsn", "$LogFile sequence number for this record")
        yield UInt16(self, "sequence_number", "Number of times this mft record has been reused")
        yield UInt16(self, "link_count", "Number of hard links")
        yield UInt16(self, "attrs_offset", "Byte offset to the first attribute")
        yield MFT_Flags(self, "flags")
        yield UInt32(self, "bytes_in_use", "Number of bytes used in this record")
        yield UInt32(self, "bytes_allocated", "Number of bytes allocated for this record")
        yield UInt64(self, "base_mft_record")
        yield UInt16(self, "next_attr_instance")

        # The below fields are specific to NTFS 3.1+ (Windows XP and above)
        yield NullBytes(self, "reserved", 2)
        yield UInt32(self, "mft_record_number", "Number of this mft record")

        padding = self.seekByte(self["attrs_offset"].value, relative=True)
        if padding:
            yield padding
        for index in xrange(4):
            yield Attribute(self, "attr[]")

class NTFS(Parser):
    MAGIC = "\xEB\x52\x90NTFS    "
    tags = {
        "id": "ntfs",
        "category": "file_system",
        "description": "NTFS file system",
        "min_size": 1024*8,
        "magic": ((MAGIC, 0),),
    }
    endian = LITTLE_ENDIAN
    _cluster_size = None

    def validate(self):
        if self.stream.readBytes(0, len(self.MAGIC)) != self.MAGIC:
            return "Invalid magic string"
        err = self["mbr/bios"].validate()
        if err:
            return err
        return True

    def createFields(self):
        yield MasterBootRecord(self, "mbr")

        bios = self["mbr/bios"]
        cluster_size = bios["sectors_per_cluster"].value * bios["bytes_per_sector"].value
        offset = self["mbr/mft_cluster"].value * cluster_size
        padding = self.seekByte(offset, relative=False)
        if padding:
            yield padding
        yield MFT(self, "mft")

        size = (self.size - self.current_size) // 8
        if size:
            yield RawBytes(self, "end", size)

