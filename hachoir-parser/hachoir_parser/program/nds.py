"""
Nintendo DS .nds game file parser

File format references:
- http://www.bottledlight.com/ds/index.php/FileFormats/NDSFormat
- http://imrannazar.com/The-Smallest-NDS-File
- http://darkfader.net/ds/files/ndstool.cpp
"""

from hachoir_parser import Parser
from hachoir_core.field import (ParserError,
    UInt8, UInt16, UInt32, UInt64, String, RawBytes, SubFile, FieldSet, NullBits, Bit, Bits,
    SeekableFieldSet, RootSeekableFieldSet)
from hachoir_core.text_handler import textHandler, hexadecimal
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN

class FileNameDirTable(FieldSet):
    def createFields(self):
        yield UInt32(self, "entry_start")
        yield UInt16(self, "entry_file_id")
        yield UInt16(self, "parent_id")
        if self["entry_start"].value < self.parent.firstEntryOffset:
            self.parent.firstEntryOffset = self["entry_start"].value

    def createDescription(self):
        return "first file id: %d; parent directory id: %d (%d)" % (self["entry_file_id"].value, self["parent_id"].value, self["parent_id"].value & 0xFFF)

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
        num_entries = self.parent["header"]["fat_size"].value / 8
        for i in range(0, num_entries):
            yield FATFileEntry(self, "entry[]")



class NdsColor(FieldSet):
    def createFields(self):
        yield Bits(self, "red", 5)
        yield Bits(self, "green", 5)
        yield Bits(self, "blue", 5)
        yield NullBits(self, "pad", 1)

    def createDescription(self):
        return "#%02x%02x%02x" % (self["red"].value << 3, self["green"].value << 3, self["blue"].value << 3)

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


class DeviceSize(UInt8):
    def createDescription(self):
        return "%d Mbit" % ((2**(20+self.value)) / (1024*1024))

class Header(FieldSet):
    def createFields(self):
        yield String(self, "game_title", 12, truncate="\0")
        yield String(self, "game_code", 4)
        yield String(self, "maker_code", 2)
        yield UInt8(self, "unit_code")
        yield UInt8(self, "device_code")

        yield DeviceSize(self, "card_size")
        yield String(self, "card_info", 9)
        yield UInt8(self, "rom_version")
        yield Bits(self, "unknown_flags[]", 2)
        yield Bit(self, "autostart_flag")
        yield Bits(self, "unknown_flags[]", 5)

        yield UInt32(self, "arm9_source", "ARM9 ROM offset")
        yield textHandler(UInt32(self, "arm9_execute_addr", "ARM9 entry address"), hexadecimal)
        yield textHandler(UInt32(self, "arm9_copy_to_addr", "ARM9 RAM address"), hexadecimal)
        yield UInt32(self, "arm9_bin_size", "ARM9 code size")

        yield UInt32(self, "arm7_source", "ARM7 ROM offset")
        yield textHandler(UInt32(self, "arm7_execute_addr", "ARM7 entry address"), hexadecimal)
        yield textHandler(UInt32(self, "arm7_copy_to_addr", "ARM7 RAM address"), hexadecimal)
        yield UInt32(self, "arm7_bin_size", "ARM7 code size")

        yield UInt32(self, "filename_table_offset")
        yield UInt32(self, "filename_table_size")
        yield UInt32(self, "fat_offset")
        yield UInt32(self, "fat_size")

        yield UInt32(self, "arm9_overlay_src")
        yield UInt32(self, "arm9_overlay_size")
        yield UInt32(self, "arm7_overlay_src")
        yield UInt32(self, "arm7_overlay_size")

        yield textHandler(UInt32(self, "ctl_read_flags"), hexadecimal)
        yield textHandler(UInt32(self, "ctl_init_flags"), hexadecimal)
        yield UInt32(self, "banner_offset")
        yield UInt16(self, "secure_crc16")
        yield UInt16(self, "rom_timeout")

        yield UInt32(self, "arm9_unk_addr")
        yield UInt32(self, "arm7_unk_addr")
        yield UInt64(self, "unenc_mode_magic")

        yield UInt32(self, "rom_size")
        yield UInt32(self, "header_size")

        yield RawBytes(self, "unknown[]", 36)
        yield String(self, "passme_autoboot_detect", 4)
        yield RawBytes(self, "unknown[]", 16)

        yield RawBytes(self, "gba_logo", 156)
        yield UInt16(self, "logo_crc16")
        yield UInt16(self, "header_crc16")


class NdsFile(Parser, RootSeekableFieldSet):
    PARSER_TAGS = {
        "id": "nds_file",
        "category": "program",
        "file_ext": ("nds",),
        "mime": (u"application/octet-stream",),
        "min_size": 352 * 8, # just a minimal header
        "description": "Nintendo DS game file",
    }

    endian = LITTLE_ENDIAN

    def validate(self):
        return (self.stream.readBytes(0, 1) != "\0"
            and ((self["header"]["device_code"].value & 7) == 0)
            and self["header"]["header_size"].value >= 352
            and self["header"]["arm9_bin_size"].value > 0
            and self["header"]["arm7_bin_size"].value > 0
            and self["header"]["arm9_source"].value + self["header"]["arm9_bin_size"].value < self._size
            and self["header"]["arm7_source"].value + self["header"]["arm7_bin_size"].value < self._size
            )

    def createFields(self):
        # Header
        yield Header(self, "header")

        # ARM9 binary
        self.seekByte(self["header"]["arm9_source"].value, relative=False)
        yield RawBytes(self, "arm9_bin", self["header"]["arm9_bin_size"].value)

        # ARM7 binary
        self.seekByte(self["header"]["arm7_source"].value, relative=False)
        yield RawBytes(self, "arm7_bin", self["header"]["arm7_bin_size"].value)

        # File Name Table
        if self["header"]["filename_table_size"].value > 0:
            self.seekByte(self["header"]["filename_table_offset"].value, relative=False)
            yield FileNameTable(self, "filename_table", size=self["header"]["filename_table_size"].value*8)

        # FAT
        if self["header"]["fat_size"].value > 0:
            self.seekByte(self["header"]["fat_offset"].value, relative=False)
            yield FATContent(self, "fat_content", size=self["header"]["fat_size"].value*8)

        # banner
        if self["header"]["banner_offset"].value > 0:
            self.seekByte(self["header"]["banner_offset"].value, relative=False)
            yield Banner(self, "banner")

        # files
        if self["header"]["fat_size"].value > 0:
            for field in self["fat_content"]:
                if field["end"].value > field["start"].value:
                    self.seekByte(field["start"].value, relative=False)
                    yield SubFile(self, "file[]", field["end"].value - field["start"].value)
