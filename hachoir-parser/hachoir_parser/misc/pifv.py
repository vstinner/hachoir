"""
EFI Platform Initialization Firmware Volume parser.

Author: Alexandre Boeglin
Creation date: 08 jul 2007
"""

from hachoir_parser import Parser
from hachoir_core.bits import str2hex
from hachoir_core.field import (FieldSet, ParserError,
    UInt8, UInt16, UInt24, UInt32, UInt64, Enum,
    CString, String, Bytes, PaddingBytes, RawBytes)
from hachoir_core.text_handler import textHandler, hexadecimal
from hachoir_core.endian import LITTLE_ENDIAN
from hachoir_core.tools import paddingSize

# defines
EFI_SECTION_COMPRESSION = "Encapsulation section where other sections are" \
    + " compressed"
EFI_SECTION_GUID_DEFINED = "Encapsulation section where other sections have" \
    + " format defined by a GUID"
EFI_SECTION_PE32 = "PE32+ Executable image"
EFI_SECTION_PIC = "Position-Independent Code"
EFI_SECTION_TE = "Terse Executable image"
EFI_SECTION_DXE_DEPEX = "DXE Dependency Expression"
EFI_SECTION_VERSION = "Version, Text and Numeric"
EFI_SECTION_USER_INTERFACE = "User-Friendly name of the driver"
EFI_SECTION_COMPATIBILITY16 = "DOS-style 16-bit EXE"
EFI_SECTION_FIRMWARE_VOLUME_IMAGE = "PI Firmware Volume image"
EFI_SECTION_FREEFORM_SUBTYPE_GUID = "Raw data with GUID in header to define" \
    + " format"
EFI_SECTION_RAW = "Raw data"
EFI_SECTION_PEI_DEPEX = "PEI Dependency Expression"
EFI_SECTION_UNKNOWN = "Unknown Section Type"

EFI_SECTION_TYPE = {
    0x1: EFI_SECTION_COMPRESSION,
    0x2: EFI_SECTION_GUID_DEFINED,
    0x10: EFI_SECTION_PE32,
    0x11: EFI_SECTION_PIC,
    0x12: EFI_SECTION_TE,
    0x13: EFI_SECTION_DXE_DEPEX,
    0x14: EFI_SECTION_VERSION,
    0x15: EFI_SECTION_USER_INTERFACE,
    0x16: EFI_SECTION_COMPATIBILITY16,
    0x17: EFI_SECTION_FIRMWARE_VOLUME_IMAGE,
    0x18: EFI_SECTION_FREEFORM_SUBTYPE_GUID,
    0x19: EFI_SECTION_RAW,
    0x1b: EFI_SECTION_PEI_DEPEX,
}

EFI_FV_FILETYPE_RAW = "Binary data"
EFI_FV_FILETYPE_FREEFORM = "Sectioned data"
EFI_FV_FILETYPE_SECURITY_CORE = "Platform core code used during the SEC phase"
EFI_FV_FILETYPE_PEI_CORE = "PEI Foundation"
EFI_FV_FILETYPE_DXE_CORE = "DXE Foundation"
EFI_FV_FILETYPE_PEIM = "PEI module (PEIM)"
EFI_FV_FILETYPE_DRIVER = "DXE driver"
EFI_FV_FILETYPE_COMBINED_PEIM_DRIVER = "Combined PEIM/DXE driver"
EFI_FV_FILETYPE_APPLICATION = "Application"
EFI_FV_FILETYPE_FIRMWARE_VOLUME_IMAGE = "Firmware volume image"
EFI_FV_FILETYPE_FFS_PAD = "Pad File For FFS"
EFI_FV_FILETYPE_OEM = "OEM File"
EFI_FV_FILETYPE_DEBUG = "Debug/Test File"
EFI_FV_FILETYPE_FFS = "Firmware File System Specific File"
EFI_FV_FILETYPE_UNKNOWN = "Unknown File Type"

EFI_FV_FILETYPE = {
    0x1: EFI_FV_FILETYPE_RAW,
    0x2: EFI_FV_FILETYPE_FREEFORM,
    0x3: EFI_FV_FILETYPE_SECURITY_CORE,
    0x4: EFI_FV_FILETYPE_PEI_CORE,
    0x5: EFI_FV_FILETYPE_DXE_CORE,
    0x6: EFI_FV_FILETYPE_PEIM,
    0x7: EFI_FV_FILETYPE_DRIVER,
    0x8: EFI_FV_FILETYPE_COMBINED_PEIM_DRIVER,
    0x9: EFI_FV_FILETYPE_APPLICATION,
    0xb: EFI_FV_FILETYPE_FIRMWARE_VOLUME_IMAGE,
    0xf0: EFI_FV_FILETYPE_FFS_PAD,
}
for x in xrange(0xc0, 0xe0):
    EFI_FV_FILETYPE[x] = EFI_FV_FILETYPE_OEM
for x in xrange(0xe0, 0xf0):
    EFI_FV_FILETYPE[x] = EFI_FV_FILETYPE_DEBUG
for x in xrange(0xf1, 0x100):
    EFI_FV_FILETYPE[x] = EFI_FV_FILETYPE_FFS

class EfiGuid(FieldSet):
    static_size = 16*8
    def createFields(self):
        yield UInt32(self, "data1")
        yield UInt16(self, "data2")
        yield UInt16(self, "data3")
        yield Bytes(self, "data4", 8)

    def createValue(self):
        return "%08X-%04X-%04X-%s-%s" % (
            self["data1"].value, self["data2"].value, self["data3"].value,
            str2hex(self["data4"].value[:2]),
            str2hex(self["data4"].value[2:]))

class BlockMap(FieldSet):
    static_size = 8*8
    def createFields(self):
        yield UInt32(self, "num_blocks")
        yield UInt32(self, "len")

    def createDescription(self):
        return "%d blocks of %d bytes" % (self["num_blocks"].value,
            self["len"].value)

class FileSectionHeader(FieldSet):
    def createFields(self):
        yield UInt24(self, "size")
        yield Enum(UInt8(self, "type"), EFI_SECTION_TYPE)
        section_type = self["type"].value
        section_type_label = EFI_SECTION_TYPE.get(section_type,
            EFI_SECTION_UNKNOWN)

        if section_type_label == EFI_SECTION_COMPRESSION:
            yield UInt32(self, "uncomp_len")
            yield UInt8(self, "comp_type")
        elif section_type_label == EFI_SECTION_FREEFORM_SUBTYPE_GUID:
            yield EfiGuid(self, "sub_type_guid")
        elif section_type_label == EFI_SECTION_GUID_DEFINED:
            yield EfiGuid(self, "section_definition_guid")
            yield UInt16(self, "data_offset")
            yield UInt16(self, "attributes")
        elif section_type_label == EFI_SECTION_USER_INTERFACE:
            yield CString(self, "file_name", charset="UTF-16-LE")
        elif section_type_label == EFI_SECTION_VERSION:
            yield UInt16(self, "build_number")
            yield CString(self, "version", charset="UTF-16-LE")

class FileSection(FieldSet):
    def __init__(self, *args, **kw):
        FieldSet.__init__(self, *args, **kw)
        if not self._size:
            self._size = self["section_header/size"].value * 8

    def createFields(self):
        yield FileSectionHeader(self, "section_header")
        section_type = self["section_header/type"].value
        section_type_label = EFI_SECTION_TYPE.get(section_type,
            EFI_SECTION_UNKNOWN)
        content_size = (self.size - self.current_size) // 8
        if content_size == 0:
            return

        if section_type_label == EFI_SECTION_FIRMWARE_VOLUME_IMAGE:
            yield FirmwareVolume(self, "firmware_volume")
        else:
            yield RawBytes(self, "content", content_size,
                section_type_label)

    def createDescription(self):
        return EFI_SECTION_TYPE.get(self["section_header/type"].value,
            EFI_SECTION_UNKNOWN)

class FileHeader(FieldSet):
    static_size = 24*8
    def createFields(self):
        yield EfiGuid(self, "name")
        yield UInt16(self, "integrity_check")
        yield Enum(UInt8(self, "type"), EFI_FV_FILETYPE)
        yield UInt8(self, "attributes")
        yield UInt24(self, "size")
        yield UInt8(self, "state")

class File(FieldSet):
    def __init__(self, *args, **kw):
        FieldSet.__init__(self, *args, **kw)
        if not self._size:
            self._size = self["file_header/size"].value * 8

    def createFields(self):
        yield FileHeader(self, "file_header")

        while self.current_size < self.size:
            yield FileSection(self, "section[]")

    def createDescription(self):
        file_type = EFI_FV_FILETYPE.get(self["file_header/type"].value,
            EFI_FV_FILETYPE_UNKNOWN)
        return "%s: %s containing %d section(s)" % (
            self["file_header/name"].value, file_type,
            len(self.array("section")))

class FirmwareVolumeHeader(FieldSet):
    def __init__(self, *args, **kw):
        FieldSet.__init__(self, *args, **kw)
        if not self._size:
            self._size = self["header_len"].value * 8

    def createFields(self):
        yield Bytes(self, "zero_vector", 16)
        yield EfiGuid(self, "fs_guid")
        yield UInt64(self, "volume_len")
        yield String(self, "signature", 4)
        yield UInt32(self, "attributes")
        yield UInt16(self, "header_len")
        yield UInt16(self, "checksum")
        yield UInt16(self, "ext_header_offset")
        yield UInt8(self, "reserved")
        yield UInt8(self, "revision")
        while True:
            bm = BlockMap(self, "block_map[]")
            yield bm
            if bm['num_blocks'].value == 0 and bm['len'].value == 0:
                break
        # TODO must handle extended firmware

class FirmwareVolume(FieldSet):
    def __init__(self, *args, **kw):
        FieldSet.__init__(self, *args, **kw)
        if not self._size:
            self._size = self["volume_header/volume_len"].value * 8

    def createFields(self):
        yield FirmwareVolumeHeader(self, "volume_header")

        while self.current_size < self.size:
            padding = paddingSize(self.current_size // 8, 8)
            if padding:
                yield PaddingBytes(self, "padding[]", padding)
            yield File(self, "file[]")

    def createDescription(self):
        return "Firmware Volume containing %d file(s)" % \
            len(self.array("file"))

class PIFVFile(Parser):
    endian = LITTLE_ENDIAN
    MAGIC = '\x00' * 16
    PARSER_TAGS = {
        "id": "pifv",
        "category": "program",
        "file_ext": ("bin", ""),
        "mime": (u"application/octet-stream",),
        "min_size": 40*8, # smallest possible header
        "magic": ((MAGIC, 0),),
        "description": "EFI Platform Initialization Firmware Volume",
    }

    def validate(self):
        return True
        return len(self.array('firmware_volume')) and \
            self['firmware_volume[0]/volume_header/zero_vector'].value == \
            self.MAGIC

    def createFields(self):
        while self.current_size < self.size:
            yield FirmwareVolume(self, "firmware_volume[]")

