"""
Nintendo DS .nds game file parser
"""

from hachoir_parser import Parser
from hachoir_core.field import (ParserError,
    UInt8, UInt16, UInt32, UInt64, String, RawBytes, FieldSet, NullBits, Bit, Bits)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN

class FileNameDirTable(FieldSet):
    def createFields(self):
        yield UInt32(self, "entry_start")
        yield UInt16(self, "entry_file_id")
        yield UInt16(self, "parent_id")
        if self["entry_start"].value < self.parent.firstEntryOffset:
            self.parent.firstEntryOffset = self["entry_start"].value

class FileNameEntry(FieldSet):
    def createFields(self):
        yield Bits(self, "name_len", 7)
        yield Bit(self, "is_directory")
        yield String(self, "name", self["name_len"].value)
        if self["is_directory"].value:
            yield UInt16(self, "dir_id")

    def createDescription(self):
        s = ""
        if self["is_directory"].value:
            s = "[D] "
        return s + self["name"].value

class Directory(FieldSet):
    def createFields(self):
        while True:
            fne = FileNameEntry(self, "entry[]")
            if fne["name_len"].value == 0:
                yield UInt8(self, "end_marker")
                break
            yield fne


class FileNameTable(FieldSet):
    def createFields(self):
        self.start_offsets = []
        self.firstEntryOffset = 2**32

        # read all directory tables (until the first directory offset is reached):
        while True:
            dt = FileNameDirTable(self, "dir_table[]")
            self.start_offsets.append(dt["entry_start"].value)
            yield dt
            if (self.current_size / 8) >= self.firstEntryOffset:
                break

        # read content of all directories for which we found directory tables:
        for offset in self.start_offsets:
            # insert padding, if necessary:
            if (self.current_size / 8 < offset):
                padding = offset - self.current_size / 8
                yield RawBytes(self, "pad[]", padding)
            yield Directory(self, "directory[]")


class FATFileEntry(FieldSet):
    static_size = 2*4*8
    def createFields(self):
        yield UInt32(self, "start")
        yield UInt32(self, "end")

    def createDescription(self):
        return "start: %d; size: %d" % (self["start"].value, self["end"].value - self["start"].value)

class FATContent(FieldSet):
    def createFields(self):
        num_entries = self.parent["fat_size"].value / 8
        for i in range(0, num_entries):
            yield FATFileEntry(self, "entry[]")



class NdsColor(FieldSet):
    def createFields(self):
        yield Bits(self, "red", 5)
        yield Bits(self, "green", 5)
        yield Bits(self, "blue", 5)
        yield NullBits(self, "pad", 1)


class Banner(FieldSet):
    def createFields(self):
        yield UInt16(self, "version")
        yield UInt16(self, "crc")
        yield RawBytes(self, "reserved", 28)
        yield RawBytes(self, "tile_data", 512)
        for i in range(0, 16):
            yield NdsColor(self, "palette_color[]")
        yield String(self, "title_jp", 256, charset="UTF-16-LE", truncate="\0")
        yield String(self, "title_en", 256, charset="UTF-16-LE", truncate="\0")
        yield String(self, "title_fr", 256, charset="UTF-16-LE", truncate="\0")
        yield String(self, "title_de", 256, charset="UTF-16-LE", truncate="\0")
        yield String(self, "title_it", 256, charset="UTF-16-LE", truncate="\0")
        yield String(self, "title_es", 256, charset="UTF-16-LE", truncate="\0")


class NdsFile(Parser):
    PARSER_TAGS = {
        "id": "nds_file",
        "category": "program",
        "file_ext": ("nds",),
        "mime": (u"application/octet-stream",),
        "min_size": 12,
        "description": "Nintendo DS game file",
    }

    endian = LITTLE_ENDIAN

    def validate(self):
        return self.stream.readBytes(0, 1) != "\0" and ((self["device_code"].value & 7) == 0) and self.size >= 512 * 8

    def createFields(self):
        # Header
        yield String(self, "game_title", 12, truncate="\0")
        yield String(self, "game_code", 4)
        yield String(self, "maker_code", 2)
        yield UInt8(self, "unit_code")
        yield UInt8(self, "device_code")

        yield UInt8(self, "card_size")
        yield String(self, "card_info", 10)
        yield UInt8(self, "flags")

        yield UInt32(self, "arm9_source")
        yield UInt32(self, "arm9_execute_addr")
        yield UInt32(self, "arm9_copy_to_addr")
        yield UInt32(self, "arm9_bin_size")

        yield UInt32(self, "arm7_source")
        yield UInt32(self, "arm7_execute_addr")
        yield UInt32(self, "arm7_copy_to_addr")
        yield UInt32(self, "arm7_bin_size")

        yield UInt32(self, "filename_table_offset")
        yield UInt32(self, "filename_table_size")
        yield UInt32(self, "fat_offset")
        yield UInt32(self, "fat_size")

        yield UInt32(self, "arm9_overlay_src")
        yield UInt32(self, "arm9_overlay_size")
        yield UInt32(self, "arm7_overlay_src")
        yield UInt32(self, "arm7_overlay_size")

        yield UInt32(self, "ctl_read_flags")
        yield UInt32(self, "ctl_init_flags")
        yield UInt32(self, "banner_offset")
        yield UInt16(self, "secure_crc16")
        yield UInt16(self, "rom_timeout")

        yield UInt32(self, "arm9_unk_addr")
        yield UInt32(self, "arm7_unk_addr")
        yield UInt64(self, "unenc_mode_magic")

        yield UInt32(self, "rom_size")
        yield UInt32(self, "header_size")

        yield RawBytes(self, "unknown_5_1", 36)
        yield String(self, "passme_autoboot_detect", 4)
        yield RawBytes(self, "unknown_5_2", 16)

        yield RawBytes(self, "gba_logo", 156)
        yield UInt16(self, "logo_crc16")
        yield UInt16(self, "header_crc16")

        yield RawBytes(self, "reserved", 160)


        # ARM9 binary
        if self["arm9_source"].value - (self.current_size / 8) > 0:
            yield RawBytes(self, "pad[]", self["arm9_source"].value - (self.current_size / 8))
        yield RawBytes(self, "arm9_bin", self["arm9_bin_size"].value)

        # ARM7 binary
        if self["arm7_source"].value - (self.current_size / 8) > 0:
            yield RawBytes(self, "pad[]", self["arm7_source"].value - (self.current_size / 8))
        yield RawBytes(self, "arm7_bin", self["arm7_bin_size"].value)

        # File Name Table
        if self["filename_table_offset"].value - (self.current_size / 8) > 0:
            yield RawBytes(self, "pad[]", self["filename_table_offset"].value - (self.current_size / 8))
        yield FileNameTable(self, "filename_table")

        # FAT
        if self["fat_size"].value > 0:
            if self["fat_offset"].value - (self.current_size / 8) > 0:
                yield RawBytes(self, "pad[]", self["fat_offset"].value - (self.current_size / 8))
            yield FATContent(self, "fat_content")

        # banner
        if self["banner_offset"].value > 0:
            if self["banner_offset"].value - (self.current_size / 8) > 0:
                yield RawBytes(self, "pad[]", self["banner_offset"].value - (self.current_size / 8))
            yield Banner(self, "banner")

        # Read rest of the file (if any)
        if self.current_size < self._size:
            yield self.seekBit(self._size, "end")
