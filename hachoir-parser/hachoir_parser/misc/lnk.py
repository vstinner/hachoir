"""
Windows Shortcut (.lnk) parser.

Documents:
- The Windows Shortcut File Format (document version 1.0)
  Reverse-engineered by Jesse Hager
  http://www.i2s-lab.com/Papers/The_Windows_Shortcut_File_Format.pdf

Author: Victor Stinner
Creation date: 2007-03-15
"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet,
    UInt32, UInt16, TimestampWin64, Bit,
    NullBytes, PaddingBits, Enum)
from hachoir_core.endian import LITTLE_ENDIAN
from hachoir_parser.common.win32 import GUID
from hachoir_parser.common.msdos import MSDOSFileAttr32
from hachoir_core.text_handler import textHandler, humanFilesize

class ShellItem(FieldSet):
    def __init__(self, *args, **kw):
        FieldSet.__init__(self, *args, **kw)
        self._size = self["size"].value * 8

    def createFields(self):
        yield UInt16(self, "size")
        yield UInt16(self, "xxx", "???")
        yield textHandler(UInt32(self, "filesize"), humanFilesize)
        yield UInt32(self, "xxx", "???")

class ShellID(FieldSet):
    def __init__(self, *args, **kw):
        FieldSet.__init__(self, *args, **kw)
        self._size = self["size"].value * 8

    def createFields(self):
        yield UInt16(self, "size")
        yield ShellItem(self, "item[]")

class LnkFile(Parser):
    MAGIC = "\x4C\0\0\0\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x46"
    tags = {
        "id": "lnk",
        "category": "misc",
        "file_ext": ("lnk",),
        "mime": ("application/x-ms-shortcut",),
        "magic": ((MAGIC, 0),),
        "min_size": 32, # FIXME
        "description": "Windows Shortcut (.lnk)",
    }
    endian = LITTLE_ENDIAN

    SHOW_WINDOW_STATE = {
         0: "Hide",
         1: "Normal",
         2: "Show minimized",
         3: "Show maximized",
         4: "Show no activate",
         5: "Show",
         6: "Minimize",
         7: "Show min no active",
         8: "Show NA",
         9: "Restore",
        10: "Show default",
    }

    def validate(self):
        if self["signature"].value != 0x0000004C:
            return "Invalid signature"
        if self["guid"].value != "00021401-0000-0000-C000-000000000046":
            return "Invalid GUID"
        return True

    def createFields(self):
        yield UInt32(self, "signature", "Shortcut signature (0x0000004C)")
        yield GUID(self, "guid")

#        yield UInt32(self, "flags")
        yield Bit(self, "has_shell_id")
        yield Bit(self, "target_is_file")
        yield Bit(self, "has_description")
        yield Bit(self, "has_rel_path")
        yield Bit(self, "has_working_dir")
        yield Bit(self, "has_cmd_line_args")
        yield Bit(self, "has_custom_icon")
        yield PaddingBits(self, "reserved[]", 25)

        yield MSDOSFileAttr32(self, "target_attr")

        yield TimestampWin64(self, "creation_time")
        yield TimestampWin64(self, "modification_time")
        yield TimestampWin64(self, "last_access_time")
        yield textHandler(UInt32(self, "target_filesize"), humanFilesize)
        yield UInt32(self, "nb_icons")
        yield Enum(UInt32(self, "show_window"), self.SHOW_WINDOW_STATE)
        yield UInt32(self, "hot_key")
        yield NullBytes(self, "reserved[]", 8)

        if self["has_shell_id"].value:
            yield ShellID(self, "shell_id")

