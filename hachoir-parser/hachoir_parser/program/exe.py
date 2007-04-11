"""
Microsoft Windows Portable Executable (PE) file parser.

Informations:
- Microsoft Portable Executable and Common Object File Format Specification:
  http://www.microsoft.com/whdc/system/platform/firmware/PECOFF.mspx

Author: Victor Stinner
Creation date: 2006-08-13
"""

from hachoir_parser import Parser
from hachoir_core.endian import LITTLE_ENDIAN
from hachoir_core.field import (StaticFieldSet,
    UInt16, UInt32, Bytes, String,
    RawBytes, PaddingBytes)
from hachoir_core.text_handler import hexadecimal
from hachoir_parser.program.exe_ne import NE_Header
from hachoir_parser.program.exe_pe import PE_Header, PE_OptHeader, SectionHeader
from hachoir_parser.program.exe_res import PE_Resource, NE_VersionInfoNode

MAX_NB_SECTION = 50

class MSDosHeader(StaticFieldSet):
    format = (
        (String, "header", 2, "File header (MZ)", {"charset": "ASCII"}),
        (UInt16, "size_mod_512", "File size in bytes modulo 512"),
        (UInt16, "size_div_512", "File size in bytes divide by 512"),
        (UInt16, "reloc_entries", "Number of relocation entries"),
        (UInt16, "code_offset", "Offset to the code in the file (divided by 16)"),
        (UInt16, "needed_memory", "Memory needed to run (divided by 16)"),
        (UInt16, "max_memory", "Maximum memory needed to run (divided by 16)"),
        (UInt32, "init_ss_sp", "Initial value of SP:SS registers.", {"text_handler": hexadecimal}),
        (UInt16, "checksum", "Checksum"),
        (UInt32, "init_cs_ip", "Initial value of CS:IP registers.", {"text_handler": hexadecimal}),
        (UInt16, "reloc_offset", "Offset in file to relocation table"),
        (UInt16, "overlay_number", "Overlay number"),
        (PaddingBytes, "reserved[]", 8, "Reserverd"),
        (UInt16, "oem_id", "OEM id"),
        (UInt16, "oem_info", "OEM info"),
        (PaddingBytes, "reserved[]", 20, "Reserved"),
        (UInt32, "next_offset", "Offset to next header (PE or NE)"))

    def isValid(self):
        if 512 <= self["size_mod_512"].value:
            return "Invalid field 'size_mod_512' value"
        if self["code_offset"].value < 4:
            return "Invalid code offset"
        looks_pe = self["size_div_512"].value < 4
        if looks_pe:
            if self["checksum"].value != 0:
                return "Invalid value of checksum"
            if not (80 <= self["next_offset"].value <= 1024):
                return "Invalid value of next_offset"
        return ""

class ExeFile(Parser):
    tags = {
        "id": "exe",
        "category": "program",
        "file_ext": ("exe", "dll", "ocx"),
        "mime": (u"application/x-dosexec",),
        "min_size": 64*8,
        #"magic": (("MZ", 0),),
        "magic_regex": (("MZ.[\0\1].{4}[^\0\1\2\3]", 0),),
        "description": "Microsoft Windows Portable Executable"
    }
    endian = LITTLE_ENDIAN

    def validate(self):
        if self.stream.readBytes(0, 2) != 'MZ':
            return "Wrong header"
        err = self["msdos"].isValid()
        if err:
            return "Invalid MSDOS header: "+err
        if self.isPE():
            if MAX_NB_SECTION < self["pe_header/nb_section"].value:
                return "Invalid number of section (%s)" \
                    % self["pe_header/nb_section"].value
        return True

    def createFields(self):
        yield MSDosHeader(self, "msdos", "MS-DOS program header")

        if self.isPE() or self.isNE():
            offset = self["msdos/next_offset"].value
            code = self.seekByte(offset, "msdos_code", relative=False)
            if code:
                yield code

        if self.isPE():
            for field in self.parsePortableExecutable():
                yield field
        elif self.isNE():
            for field in self.parseNE_Executable():
                yield field
        else:
            offset = self["msdos/code_offset"].value * 16
            raw = self.seekByte(offset, "raw[]", relative=False)
            if raw:
                yield raw
        if self.current_size < self._size:
            yield self.seekBit(self._size, "footer")


    def parseNE_Executable(self):
        yield NE_Header(self, "ne_header")

        # FIXME: Compute resource offset instead of using searchBytes()
        # Ugly hack to get find version info structure
        start = self.current_size
        addr = self.stream.searchBytes('VS_VERSION_INFO', start)
        if addr:
            padding = self.seekBit(addr-32)
            if padding:
                yield padding
            yield NE_VersionInfoNode(self, "info")

    def parsePortableExecutable(self):
        # Read PE header
        yield PE_Header(self, "pe_header")

        # Read PE optional header
        size = self["pe_header/opt_hdr_size"].value
        if size:
            yield PE_OptHeader(self, "pe_opt_header", size=size*8)

        # Read section headers
        sections = []
        for index in xrange(self["pe_header/nb_section"].value):
            section = SectionHeader(self, "section_hdr[]")
            yield section
            if section["phys_size"].value:
                sections.append(section)

        # Read sections
        sections.sort(key=lambda field: field["phys_off"].value)
        for section in sections:
            padding = self.seekByte(section["phys_off"].value)
            if padding:
                yield padding
            size = section["phys_size"].value
            if size:
                name = str(section["name"].value.strip("."))
                is_res = name.lower() == "rsrc"
                if name:
                    name = "section_%s" % name
                else:
                    name =  "section[]"
                if is_res:
                    yield PE_Resource(self, name, section, size=size*8)
                else:
                    yield RawBytes(self, name, size)

    def isPE(self):
        if not hasattr(self, "_is_pe"):
            self._is_pe = False
            offset = self["msdos/next_offset"].value * 8
            if 64*8 <= offset \
            and (offset+PE_Header.static_size) <= self.size \
            and self.stream.readBytes(offset, 4) == 'PE\0\0':
                self._is_pe = True
        return self._is_pe

    def isNE(self):
        if not hasattr(self, "_is_ne"):
            self._is_ne = False
            offset = self["msdos/next_offset"].value * 8
            if 64*8 <= offset \
            and (offset+NE_Header.static_size) <= self.size \
            and self.stream.readBytes(offset, 2) == 'NE':
                self._is_ne = True
        return self._is_ne

    def getRessource(self):
        # MS-DOS program: no resource
        if not self.isPE():
            return None

        # Check if PE has resource or not
        if "pe_opt_header/resource/size" in self:
            if not self["pe_opt_header/resource/size"].value:
                return None
        if "section_rsrc" in self:
            return self["section_rsrc"]
        return None

    def createDescription(self):
        if self.isPE():
            if self["pe_header/is_dll"].value:
                text = u"Microsoft Windows DLL"
            else:
                text = u"Microsoft Windows Portable Executable"
            info = [self["pe_header/cpu"].display]
            if "pe_opt_header" in self:
                hdr = self["pe_opt_header"]
                info.append(hdr["subsystem"].display)
            if self["pe_header/is_stripped"].value:
                info.append(u"stripped")
            return u"%s: %s" % (text, ", ".join(info))
        elif self.isNE():
            return u"New-style Executable (NE) for Microsoft MS Windows 3.x"
        else:
            return u"MS-DOS executable"

    def createContentSize(self):
        if self.isPE() or self.isNE():
            # TODO: Guess PE size
            return None
        else:
            size = self["msdos/size_mod_512"].value + (self["msdos/size_div_512"].value-1) * 512
            if size < 0:
                return None
        return size*8

