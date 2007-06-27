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
  2007-06-27 - Robert Xiao
    * Fixes to FileLocationInfo to correctly handle Unicode paths
  2007-06-13 - Robert Xiao
    * ItemID, FileLocationInfo and ExtraInfo structs, correct Unicode string handling
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

    def __init__(self, *args, **kw):
        FieldSet.__init__(self, *args, **kw)
        if self["length"].value:
            self._size = self["length"].value * 8
        else:
            self._size = 16

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

def formatVolumeSerial(field):
    val = field.value
    return '%04X-%04X'%(val>>16, val&0xFFFF)

class LocalVolumeTable(FieldSet):
    VOLUME_TYPE={
        1: "No root directory",
        2: "Removable (Floppy, Zip, etc.)",
        3: "Fixed (Hard disk)",
        4: "Remote (Network drive)",
        5: "CD-ROM",
        6: "Ram drive",
    }

    def createFields(self):
        yield UInt32(self, "length", "Length of this structure")
        yield Enum(UInt32(self, "volume_type", "Volume Type"),self.VOLUME_TYPE)
        yield textHandler(UInt32(self, "volume_serial", "Volume Serial Number"), formatVolumeSerial)

        yield UInt32(self, "label_offset", "Offset to volume label")
        padding = self.seekByte(self["label_offset"].value)
        if padding:
            yield padding
        yield CString(self, "drive")

    def createValue(self):
        return self["drive"].value

class NetworkVolumeTable(FieldSet):
    def createFields(self):
        yield UInt32(self, "length", "Length of this structure")
        yield UInt32(self, "unknown[]")
        yield UInt32(self, "share_name_offset", "Offset to share name")
        yield UInt32(self, "unknown[]")
        yield UInt32(self, "unknown[]")
        padding = self.seekByte(self["share_name_offset"].value)
        if padding:
            yield padding
        yield CString(self, "share_name")

    def createValue(self): return self["share_name"].value

class FileLocationInfo(FieldSet):
    def createFields(self):
        yield UInt32(self, "length", "Length of this structure")
        if not self["length"].value:
            return

        yield UInt32(self, "first_offset_pos", "Position of first offset")
        has_unicode_paths = (self["first_offset_pos"].value == 0x24)
        yield Bit(self, "on_local_volume")
        yield Bit(self, "on_network_volume")
        yield PaddingBits(self, "reserved[]", 30)
        yield UInt32(self, "local_info_offset", "Offset to local volume table; only meaningful if on_local_volume = 1")
        yield UInt32(self, "local_pathname_offset", "Offset to local base pathname; only meaningful if on_local_volume = 1")
        yield UInt32(self, "remote_info_offset", "Offset to network volume table; only meaningful if on_network_volume = 1")
        yield UInt32(self, "pathname_offset", "Offset of remaining pathname")
        if has_unicode_paths:
            yield UInt32(self, "local_pathname_unicode_offset", "Offset to Unicode version of local base pathname; only meaningful if on_local_volume = 1")
            yield UInt32(self, "pathname_unicode_offset", "Offset to Unicode version of remaining pathname")
        if self["on_local_volume"].value:
            padding = self.seekByte(self["local_info_offset"].value)
            if padding:
                yield padding
            yield LocalVolumeTable(self, "local_volume_table", "Local Volume Table")

            padding = self.seekByte(self["local_pathname_offset"].value)
            if padding:
                yield padding
            yield CString(self, "local_base_pathname", "Local Base Pathname")
            if has_unicode_paths:
                padding = self.seekByte(self["local_pathname_unicode_offset"].value)
                if padding:
                    yield padding
                yield CString(self, "local_base_pathname_unicode", "Local Base Pathname in Unicode", charset="UTF-16-LE")

        if self["on_network_volume"].value:
            padding = self.seekByte(self["remote_info_offset"].value)
            if padding:
                yield padding
            yield NetworkVolumeTable(self, "network_volume_table")

        padding = self.seekByte(self["pathname_offset"].value)
        if padding:
            yield padding
        yield CString(self, "final_pathname", "Final component of the pathname")

        if has_unicode_paths:
            padding = self.seekByte(self["pathname_unicode_offset"].value)
            if padding:
                yield padding
            yield CString(self, "final_pathname_unicode", "Final component of the pathname in Unicode", charset="UTF-16-LE")

        padding=self.seekByte(self["length"].value)
        if padding:
            yield padding

class LnkString(FieldSet):
    def createFields(self):
        yield UInt16(self, "length", "Length of this string")
        if self.root.hasUnicodeNames():
            yield String(self, "data", self["length"].value*2, charset="UTF-16-LE")
        else:
            yield String(self, "data", self["length"].value, charset="ASCII")

    def createValue(self):
        return self["data"].value

class ExtraInfo(FieldSet):
    INFO_TYPE={
        0xA0000003: "Hostname and Other Stuff",
        0xA0000005: "Special Folder Info",
        0xA0000007: "Custom Icon Details",
    }
    SPECIAL_FOLDER = {
         0: "DESKTOP",
         1: "INTERNET",
         2: "PROGRAMS",
         3: "CONTROLS",
         4: "PRINTERS",
         5: "PERSONAL",
         6: "FAVORITES",
         7: "STARTUP",
         8: "RECENT",
         9: "SENDTO",
        10: "BITBUCKET",
        11: "STARTMENU",
        16: "DESKTOPDIRECTORY",
        17: "DRIVES",
        18: "NETWORK",
        19: "NETHOOD",
        20: "FONTS",
        21: "TEMPLATES",
        22: "COMMON_STARTMENU",
        23: "COMMON_PROGRAMS",
        24: "COMMON_STARTUP",
        25: "COMMON_DESKTOPDIRECTORY",
        26: "APPDATA",
        27: "PRINTHOOD",
        28: "LOCAL_APPDATA",
        29: "ALTSTARTUP",
        30: "COMMON_ALTSTARTUP",
        31: "COMMON_FAVORITES",
        32: "INTERNET_CACHE",
        33: "COOKIES",
        34: "HISTORY",
        35: "COMMON_APPDATA",
        36: "WINDOWS",
        37: "SYSTEM",
        38: "PROGRAM_FILES",
        39: "MYPICTURES",
        40: "PROFILE",
        41: "SYSTEMX86",
        42: "PROGRAM_FILESX86",
        43: "PROGRAM_FILES_COMMON",
        44: "PROGRAM_FILES_COMMONX86",
        45: "COMMON_TEMPLATES",
        46: "COMMON_DOCUMENTS",
        47: "COMMON_ADMINTOOLS",
        48: "ADMINTOOLS",
        49: "CONNECTIONS",
        53: "COMMON_MUSIC",
        54: "COMMON_PICTURES",
        55: "COMMON_VIDEO",
        56: "RESOURCES",
        57: "RESOURCES_LOCALIZED",
        58: "COMMON_OEM_LINKS",
        59: "CDBURN_AREA",
        61: "COMPUTERSNEARME",
    }

    def __init__(self, *args, **kw):
        FieldSet.__init__(self, *args, **kw)
        if self["length"].value:
            self._size = self["length"].value * 8
        else:
            self._size = 32

    def createFields(self):
        yield UInt32(self, "length", "Length of this structure")
        if not self["length"].value:
            return

        yield Enum(textHandler(UInt32(self, "flags", "Flags determining the function of this structure"),hexadecimal),self.INFO_TYPE)
        if self["flags"].value == 0xA0000003:
            yield UInt32(self, "remaining_length")
            yield UInt32(self, "unknown[]")
            yield String(self, "hostname", 16, "Computer hostname on which shortcut was last modified")
            yield RawBytes(self, "unknown[]", 32)
            yield RawBytes(self, "unknown[]", 32)
        elif self["flags"].value == 0xA0000005:
            yield Enum(UInt32(self, "special_folder_id", "ID of the special folder"),self.SPECIAL_FOLDER)
            yield UInt32(self, "offset", "Some kind of offset (?)")
        elif self["flags"].value == 0xA0000007:
            yield CString(self, "file_path", "Path to icon")
            yield RawBytes(self, "raw", self["length"].value-self.current_size/8)
        else:
            yield RawBytes(self, "raw", self["length"].value-self.current_size/8)

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
        "min_size": len(MAGIC)*8,   # signature + guid = 20 bytes
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
            item = ItemId(self, "item_idlist[]")
            yield item
            while item["length"].value:
                item = ItemId(self, "item_idlist[]")
                yield item
        if self["target_is_file"].value:
            yield FileLocationInfo(self, "file_location_info", "File Location Info")
        if self["has_description"].value:
            yield LnkString(self, "description")
        if self["has_rel_path"].value:
            yield LnkString(self, "relative_path", "Relative path to target")
        if self["has_working_dir"].value:
            yield LnkString(self, "working_dir", "Working directory (dir to start target in)")
        if self["has_cmd_line_args"].value:
            yield LnkString(self, "cmd_line_args", "Command Line Arguments")
        if self["has_custom_icon"].value:
            yield LnkString(self, "custom_icon", "Custom Icon Path")

        while not self.eof:
            yield ExtraInfo(self, "extra_info[]")

