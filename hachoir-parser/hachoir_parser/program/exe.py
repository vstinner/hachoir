"""
Microsoft Windows Portable Executable (PE) file parser.

Informations:
- Microsoft Portable Executable and Common Object File Format Specification:
  http://www.microsoft.com/whdc/system/platform/firmware/PECOFF.mspx

Author: Victor Stinner
Creation date: 2006-08-13
"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, StaticFieldSet,
    MatchError,
    Bit, Bits, UInt8, UInt16, UInt32,
    Bytes, String, Enum,
    RawBytes, PaddingBytes, NullBytes, NullBits)
from hachoir_core.endian import LITTLE_ENDIAN
from hachoir_core.text_handler import timestampUNIX, hexadecimal, humanFilesize
from hachoir_parser.program.exe_res import Resource

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
        (UInt32, "pe_offset", "Offset to PE header"))

    def isValid(self):
        if 512 <= self["size_mod_512"].value:
            return "Invalid field 'size_mod_512' value"
        if self["code_offset"].value < 4:
            return "Invalid code offset"
        if self["checksum"].value != 0:
            return "Invalid value of checksum"
#        if not(0 < self["init_ss_sp"].value < 0x4fffffff):
#            return "Invalid value of init_ss_sp"
#        if 1024 < self["pe_offset"].value:
#            return "Invalid value of pe_offset"
        return ""

class SectionHeader(FieldSet):
    static_size = 40 * 8
    def createFields(self):
        yield String(self, "name", 8, charset="ASCII", strip="\0")
        yield UInt32(self, "mem_size", "Size in memory", text_handler=humanFilesize)
        yield UInt32(self, "rva", "RVA (location) in memory", text_handler=hexadecimal)
        yield UInt32(self, "phys_size", "Physical size (on disk)", text_handler=humanFilesize)
        yield UInt32(self, "phys_off", "Physical location (on disk)", text_handler=humanFilesize)
        yield PaddingBytes(self, "reserved", 12)
        if False:
            yield UInt32(self, "flags", text_handler=hexadecimal)
        else:
            # 0x0000000#
            yield NullBits(self, "reserved[]", 4)
            # 0x000000#0
            yield NullBits(self, "reserved[]", 1)
            yield Bit(self, "has_code", "Contains code")
            yield Bit(self, "has_init_data", "Contains initialized data")
            yield Bit(self, "has_uinit_data", "Contains uninitialized data")
            # 0x00000#00
            yield NullBits(self, "reserved[]", 1)
            yield Bit(self, "has_comment", "Contains comments?")
            yield NullBits(self, "reserved[]", 1)
            yield Bit(self, "remove", "Contents will not become part of image")
            # 0x0000#000
            yield Bit(self, "has_comdata", "Contains comdat?")
            yield NullBits(self, "reserved[]", 1)
            yield Bit(self, "no_defer_spec_exc", "Reset speculative exceptions handling bits in the TLB entries")
            yield Bit(self, "gp_rel", "Content can be accessed relative to GP")
            # 0x000#0000
            yield NullBits(self, "reserved[]", 4)
            # 0x00#00000
            yield NullBits(self, "reserved[]", 4)
            # 0x0#000000
            yield Bit(self, "ext_reloc", "Contains extended relocations?")
            yield Bit(self, "discarded", "Can be discarded?")
            yield Bit(self, "is_not_cached", "Is not cachable?")
            yield Bit(self, "is_not_paged", "Is not pageable?")
            # 0x#0000000
            yield Bit(self, "is_shareable", "Is shareable?")
            yield Bit(self, "is_executable", "Is executable?")
            yield Bit(self, "is_readable", "Is readable?")
            yield Bit(self, "is_writable", "Is writable?")

    def createDescription(self):
        info = [
            "rva=%s" % self["rva"].display,
            "size=%s" % self["mem_size"].display]
        if self["is_executable"].value:
            info.append("exec")
        if self["is_readable"].value:
            info.append("read")
        if self["is_writable"].value:
            info.append("write")
        return 'Section "%s": %s' % (self["name"].value, ", ".join(info))

class DataDirectory(FieldSet):
    def createFields(self):
        yield UInt32(self, "rva", "Virtual address", text_handler=hexadecimal)
        yield UInt32(self, "size", text_handler=humanFilesize)

    def createDescription(self):
        if self["size"].value:
            return "Directory at %s (%s)" % (
                self["rva"].display, self["size"].display)
        else:
            return "(empty directory)"

class PE_OptHeader(FieldSet):
    SUBSYSTEM_NAME = {
        1: "Native",
        2: "Windows/GUI",
        3: "Windows non-GUI",
        5: "OS/2",
        7: "POSIX",
    }
    DIRECTORY_NAME = {
        0: "export",
        1: "import",
        2: "resource",
        11: "bound_import",
    }
    def createFields(self):
        yield UInt16(self, "signature", "PE optional header signature (267)")
        if self["signature"].value != 267:
            raise ParserError("Invalid PE optional header signature")
        yield UInt8(self, "maj_lnk_ver", "Major linker version")
        yield UInt8(self, "min_lnk_ver", "Minor linker version")
        yield UInt32(self, "size_code", "Size of code", text_handler=humanFilesize)
        yield UInt32(self, "size_init_data", "Size of initialized data", text_handler=humanFilesize)
        yield UInt32(self, "size_uninit_data", "Size of uninitialized data", text_handler=humanFilesize)
        yield UInt32(self, "entry_point", "Address (RVA) of the code entry point", text_handler=hexadecimal)
        yield UInt32(self, "base_code", "Base (RVA) of code", text_handler=hexadecimal)
        yield UInt32(self, "base_data", "Base (RVA) of data", text_handler=hexadecimal)
        yield UInt32(self, "image_base", "Image base (RVA)", text_handler=hexadecimal)
        yield UInt32(self, "sect_align", "Section alignment", text_handler=humanFilesize)
        yield UInt32(self, "file_align", "File alignment", text_handler=humanFilesize)
        yield UInt16(self, "maj_os_ver", "Major OS version")
        yield UInt16(self, "min_os_ver", "Minor OS version")
        yield UInt16(self, "maj_img_ver", "Major image version")
        yield UInt16(self, "min_img_ver", "Minor image version")
        yield UInt16(self, "maj_subsys_ver", "Major subsystem version")
        yield UInt16(self, "min_subsys_ver", "Minor subsystem version")
        yield NullBytes(self, "reserved", 4)
        yield UInt32(self, "size_img", "Size of image", text_handler=humanFilesize)
        yield UInt32(self, "size_hdr", "Size of headers", text_handler=humanFilesize)
        yield UInt32(self, "checksum", text_handler=hexadecimal)
        yield Enum(UInt16(self, "subsystem"), self.SUBSYSTEM_NAME)
        yield UInt16(self, "dll_flags")
        yield UInt32(self, "size_stack_reserve", text_handler=humanFilesize)
        yield UInt32(self, "size_stack_commit", text_handler=humanFilesize)
        yield UInt32(self, "size_heap_reserve", text_handler=humanFilesize)
        yield UInt32(self, "size_heap_commit", text_handler=humanFilesize)
        yield UInt32(self, "loader_flags")
        yield UInt32(self, "nb_directory", "Number of RVA and sizes")
        for index in xrange(self["nb_directory"].value):
            try:
                name = self.DIRECTORY_NAME[index]
            except KeyError:
                name = "data_dir[%u]" % index
            yield DataDirectory(self, name)

class PE_Header(FieldSet):
    static_size = 24*8
    cpu_name = {
        0x0184: "Alpha AXP",
        0x01c0: "ARM",
        0x014C: "Intel 80386",
        0x014D: "Intel 80486",
        0x014E: "Intel Pentium",
        0x0200: "Intel IA64",
        0x0268: "Motorolla 68000",
        0x0266: "MIPS",
        0x0284: "Alpha AXP 64 bits",
        0x0366: "MIPS with FPU",
        0x0466: "MIPS16 with FPU",
        0x01f0: "PowerPC little endian",
        0x0162: "R3000",
        0x0166: "MIPS little endian (R4000)",
        0x0168: "R10000",
        0x01a2: "Hitachi SH3",
        0x01a6: "Hitachi SH4",
        0x0160: "R3000 (MIPS), big endian",
        0x0162: "R3000 (MIPS), little endian",
        0x0166: "R4000 (MIPS), little endian",
        0x0168: "R10000 (MIPS), little endian",
        0x0184: "DEC Alpha AXP",
        0x01F0: "IBM Power PC, little endian",
    }

    def createFields(self):
        yield Bytes(self, "header", 4, r"PE header signature (PE\0\0)")
        if self["header"].value != "PE\0\0":
            raise MatchError("Invalid PE header signature")
        yield Enum(UInt16(self, "cpu", "CPU type"), self.cpu_name)
        yield UInt16(self, "nb_section", "Number of sections")
        yield UInt32(self, "creation_date", "Creation date", text_handler=timestampUNIX)
        yield UInt32(self, "ptr_to_sym", "Pointer to symbol table")
        yield UInt32(self, "nb_symbols", "Number of symbols")
        yield UInt16(self, "opt_hdr_size", "Optional header size")

        yield Bit(self, "reloc_stripped", "If true, don't contain base relocations.")
        yield Bit(self, "exec_image", "Exectuable image?")
        yield Bit(self, "line_nb_stripped", "COFF line numbers stripped?")
        yield Bit(self, "local_sym_stripped", "COFF symbol table entries stripped?")
        yield Bit(self, "aggr_ws", "Aggressively trim working set")
        yield Bit(self, "large_addr", "Application can handle addresses greater than 2 GB")
        yield NullBits(self, "reserved", 1)
        yield Bit(self, "reverse_lo", "Little endian: LSB precedes MSB in memory")
        yield Bit(self, "32bit", "Machine based on 32-bit-word architecture")
        yield Bit(self, "is_stripped", "Debugging information removed?")
        yield Bit(self, "swap", "If image is on removable media, copy and run from swap file")
        yield NullBits(self, "reserved2", 1)
        yield Bit(self, "is_system", "It's a system file")
        yield Bit(self, "is_dll", "It's a dynamic-link library (DLL)")
        yield Bit(self, "up", "File should be run only on a UP machine")
        yield Bit(self, "reverse_hi", "Big endian: MSB precedes LSB in memory")

class ExeFile(Parser):
    tags = {
        "id": "exe",
        "category": "program",
        "file_ext": ("exe",),
        "mime": ("application/x-dosexec",),
        "min_size": 64*8,
        "magic": (("MZ", 0),),
        "description": "Microsoft Windows Portable Executable"
    }
    endian = LITTLE_ENDIAN

    def validate(self):
        if self.stream.readBytes(0, 2) != 'MZ':
            return "Wrong header"
        err = self["msdos"].isValid()
        if err:
            return "Invalid MSDOS header: "+err
        return True

    def createFields(self):
        yield MSDosHeader(self, "msdos", "MS-DOS program header")
        offset = self["msdos/pe_offset"].value * 8
        if offset \
        and (offset+PE_Header.static_size) <= self.size \
        and self.stream.readBytes(offset, 4) == 'PE\0\0':
            # Read MS-DOS code
            code = self.seekBit(offset, "msdos_code", relative=False)
            if code:
                yield code

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
                padding = self.seekByte(section["phys_off"].value, null=True)
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
                        yield Resource(self, name, size=size*8)
                    else:
                        yield RawBytes(self, name, size)
        else:
            offset = self["msdos/code_offset"].value * 16
            raw = self.seekByte(offset, "raw[]", relative=False)
            if raw:
                yield raw
        size = (self.size - self.current_size) // 8
        if size:
            yield RawBytes(self, "raw", size)

    def isPE(self):
        return "pe_header" in self

    def createDescription(self):
        if self.isPE():
            if self["pe_header/is_dll"].value:
                text = "Microsoft Windows DLL"
            else:
                text = "Microsoft Windows Portable Executable"
            info = [self["pe_header/cpu"].display]
            if "pe_opt_header" in self:
                hdr = self["pe_opt_header"]
                info.append(hdr["subsystem"].display)
            if self["pe_header/is_stripped"].value:
                info.append("stripped")
            return "%s: %s" % (text, ", ".join(info))
        else:
            return "MS-DOS executable"

    def createContentSize(self):
        if self.isPE():
            size = None
        else:
            size = self["msdos/size_mod_512"].value + (self["msdos/size_div_512"].value-1) * 512
            if size < 0:
                return None
        return size*8

