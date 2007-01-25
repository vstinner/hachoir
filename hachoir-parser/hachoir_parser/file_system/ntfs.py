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
    UInt8, UInt16, UInt32, UInt64,
    String, Bytes, NullBytes, RawBytes)
from hachoir_core.endian import LITTLE_ENDIAN
from hachoir_core.text_handler import hexadecimal
from hachoir_core.tools import humanFilesize

class Header(FieldSet):
    def createFields(self):
        yield UInt16(self, "name_len", "Name length in character (size=length*2 bytes)")
        yield String(self, "name", self["name_len"].value*2, charset="UTF-16-LE")


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
        return "NTFS Master Boot Record (%s)" % humanFilesize(size)

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

    def validate(self):
        if self.stream.readBytes(0, len(self.MAGIC)) != self.MAGIC:
            return "Invalid magic string"
        err = self["mbr/bios"].validate()
        if err:
            return err
        return True

    def createFields(self):
        yield MasterBootRecord(self, "mbr")
        size = (self.size - self.current_size) // 8
        if size:
            yield RawBytes(self, "end", size)

