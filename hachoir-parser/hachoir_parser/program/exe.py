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
    Bit, UInt16, UInt32,
    Bytes, String, Enum,
    PaddingBytes, NullBits)
from hachoir_core.endian import LITTLE_ENDIAN
from hachoir_core.text_handler import timestampUNIX, hexadecimal

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
        if not(0 < self["init_ss_sp"].value < 0x1fffffff):
            return "Invalid value of init_ss_sp"
        if 1024 < self["pe_offset"].value:
            return "Invalid value of pe_offset"
        return ""

class PE_Header(FieldSet):
    static_size = 24*8
    cpu_name = {
        0x0184: "Alpha AXP",
        0x01c0: "ARM",
        0x014C: "Intel 80386 or greater",
        0x014D: "Intel 80486 or greater",
        0x014E: "Intel Pentium or greader",
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
        yield UInt16(self, "nb_sections", "Number of sections")
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
        yield Bit(self, "debug_stripped", "Debugging information removed?")
        yield Bit(self, "swap", "If image is on removable media, copy and run from swap file")
        yield NullBits(self, "reserved2", 1)
        yield Bit(self, "system", "It's a system file")
        yield Bit(self, "dll", "It's a dynamic-link library (DLL)")
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
            code = self.seekBit(offset, "msdos_code", relative=False)
            if code:
                yield code
            yield PE_Header(self, "pe_header")
        else:
            offset = self["msdos/code_offset"].value * 16
            raw = self.seekByte(offset, "raw[]", relative=False)
            if raw:
                yield raw
            size = (self.size - self.current_size) // 8
            yield Bytes(self, "code", size)

    def isPE(self):
        return "pe_header" in self

    def createDescription(self):
        if self.isPE():
            return "Microsoft Windows Portable Executable: %s" % self["pe_header/cpu"].display
        else:
            return "MS-DOS executable"

