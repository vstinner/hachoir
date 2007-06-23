"""
Windows Shortcut (.lnk) parser.

Documents:
- The Windows Shortcut File Format (document version 1.0)
  Reverse-engineered by Jesse Hager
  http://www.i2s-lab.com/Papers/The_Windows_Shortcut_File_Format.pdf
- Wine source code:
  http://source.winehq.org/source/include/shlobj.h (SHELL_LINK_DATA_FLAGS enum)
  http://source.winehq.org/source/dlls/shell32/pidl.h

Author: Robert Xiao, Victor Stinner

Changes:
  2007-06-13 - Robert Xiao
     * XXX
  2007-03-15 - Victor Stinner
    * Creation of the parser
"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, GenericString,
    SeekableFieldSet, CString, PascalString16,
    UInt32, UInt16, UInt8, String, TimestampWin64, Bit,
    NullBytes, PaddingBits, PaddingBytes, Enum, RawBytes, DateTimeMSDOS32)
from hachoir_core.endian import LITTLE_ENDIAN
from hachoir_core.text_handler import textHandler, hexadecimal
from hachoir_parser.common.win32 import GUID
from hachoir_parser.common.msdos import MSDOSFileAttr16, MSDOSFileAttr32
from hachoir_core.text_handler import filesizeHandler

from hachoir_core.tools import paddingSize

class ItemId(FieldSet):
    ITEM_TYPE = {
        0x1F: "GUID",
        0x23: "Drive",
        0x25: "Drive",
        0x29: "Drive",
        0x2E: "GUID",
        0x2F: "Drive",
        0x30: "Dir/File",
        0x31: "Directory",
        0x32: "File",
        0x34: "File [Unicode Name]",
        0x41: "Workgroup",
        0x42: "Computer",
        0x46: "Net Provider",
        0x47: "Whole Network",
        0x61: "MSITStore",
        0x70: "Printer/RAS Connection",
        0xB1: "History/Favorite",
        0xC3: "Network Share",
    }

    def createFields(self):
        yield UInt16(self, "length", "Length of Item ID Entry")
        if not self["length"].value:
            return

        yield Enum(UInt8(self, "type"),self.ITEM_TYPE)
        entrytype=self["type"].value
        if entrytype in (0x1F, 0x2E, 0x70):
            # GUID
            yield RawBytes(self, "dummy", 1, "should be 0x50")
            yield GUID(self, "guid")

        elif entrytype in (0x23, 0x25, 0x29, 0x2F):
            # Drive
            yield String(self, "drive", self["length"].value-3, strip="\0")

        elif entrytype in (0x30, 0x31, 0x32):
            yield RawBytes(self, "dummy", 1, "should be 0x00")
            yield UInt32(self, "size", "size of file; 0 for folders")
            yield DateTimeMSDOS32(self, "date_time", "File/folder date and time")
            yield MSDOSFileAttr16(self, "attribs", "File/folder attributes")
            yield CString(self, "name", "File/folder name")
            if self.root.hasUnicodeNames():
                # Align to 2-bytes
                n = paddingSize(self.current_size//8, 2)
                if n:
                    yield PaddingBytes(self, "pad", n)

                yield UInt16(self, "length_w", "Length of wide struct member")
                yield RawBytes(self, "unknown[]", 6)
                yield DateTimeMSDOS32(self, "creation_date_time", "File/folder creation date and time")
                yield DateTimeMSDOS32(self, "access_date_time", "File/folder last access date and time")
                yield RawBytes(self, "unknown[]", 4)
                yield CString(self, "unicode_name", "File/folder name", charset="UTF-16-LE")
                yield RawBytes(self, "unknown[]", 2)
            else:
                yield CString(self, "name_short", "File/folder short name")

        elif entrytype in (0x41, 0x42, 0x46):
            yield RawBytes(self, "unknown[]", 2)
            yield CString(self, "name")
            yield CString(self, "protocol")
            yield RawBytes(self, "unknown[]", 2)

        elif entrytype == 0x47:
            # Whole Network
            yield RawBytes(self, "unknown[]", 2)
            yield CString(self, "name")

        elif entrytype == 0xC3:
            # Network Share
            yield RawBytes(self, "unknown[]", 2)
            yield CString(self, "name")
            yield CString(self, "protocol")
            yield CString(self, "description")
            yield RawBytes(self, "unknown[]", 2)

        else:
            yield RawBytes(self, "raw", self["length"].value-3)

    def createValue(self):
        if self["length"].value:
            return self["type"].value
        else:
            return 0

    def createDisplay(self):
        if self["length"].value:
            return "Item ID Entry: "+self.ITEM_TYPE.get(self["type"].value,"Unknown")
        else:
            return "End of Item ID List"

class LnkFile(Parser):
    MAGIC = "\x4C\0\0\0\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x46"
    tags = {
        "id": "lnk",
        "category": "misc",
        "file_ext": ("lnk",),
        "mime": (u"application/x-ms-shortcut",),
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

    def hasUnicodeNames(self):
        return self["has_unicode_names"].value

    def createFields(self):
        yield UInt32(self, "signature", "Shortcut signature (0x0000004C)")
        yield GUID(self, "guid")

        yield Bit(self, "has_shell_id")
        yield Bit(self, "target_is_file", "Is a file or a directory?")
        yield Bit(self, "has_description")
        yield Bit(self, "has_rel_path")
        yield Bit(self, "has_working_dir")
        yield Bit(self, "has_cmd_line_args")
        yield Bit(self, "has_custom_icon")
        yield Bit(self, "has_unicode_names")
        yield Bit(self, "force_no_linkinfo")
        yield Bit(self, "has_exp_sz")
        yield Bit(self, "run_in_separate")
        yield Bit(self, "has_logo3id")
        yield Bit(self, "has_darwinid")
        yield Bit(self, "runas_user")
        yield Bit(self, "has_exp_icon_sz")
        yield Bit(self, "no_pidl_alias")
        yield Bit(self, "force_unc_name")
        yield Bit(self, "run_with_shim_layer")
        yield PaddingBits(self, "reserved[]", 14)

        yield MSDOSFileAttr32(self, "target_attr")

        yield TimestampWin64(self, "creation_time")
        yield TimestampWin64(self, "modification_time")
        yield TimestampWin64(self, "last_access_time")
        yield filesizeHandler(UInt32(self, "target_filesize"))
        yield UInt32(self, "icon_number")
        yield Enum(UInt32(self, "show_window"), self.SHOW_WINDOW_STATE)
        yield UInt32(self, "hot_key")
        yield NullBytes(self, "reserved[]", 8)

        if self["has_shell_id"].value:
            yield UInt16(self, "item_idlist_size", "size of item ID list")
            item=ItemId(self, "item_idlist[]")
            yield item
            while item["length"].value:
                item=ItemId(self, "item_idlist[]")
                yield item

        size = (self.size - self.current_size) // 8
        if size:
            yield RawBytes(self, "raw_end", size)

