"""
Mach-O (Mac OS X executable file format) parser.

Author: Robert Xiao
Creation date: February 11, 2015
"""

from hachoir.parser import HachoirParser
from hachoir.field import (RootSeekableFieldSet, FieldSet, ParserError, Bit, NullBits, RawBits,
    Int32, UInt8, UInt16, UInt32, UInt64, Enum,
    String, RawBytes, Bytes)
from hachoir.core.text_handler import textHandler, hexadecimal
from hachoir.core.endian import LITTLE_ENDIAN, BIG_ENDIAN


CPU_ARCH_ABI64 = 0x01000000
CPU_TYPE = {
    -1: 'Any',
    1: 'VAX',
    6: 'MC680x0',
    7: 'i386',
    7|CPU_ARCH_ABI64: 'x86_64',
    8: 'MIPS',
    10: 'MC98000',
    11: 'HPPA',
    12: 'ARM',
    12|CPU_ARCH_ABI64: 'ARM64',
    13: 'MC88000',
    14: 'SPARC',
    15: 'I860',
    16: 'Alpha',
    18: 'PowerPC',
    18|CPU_ARCH_ABI64: 'PowerPC64',
}

FILE_TYPE = {
    1: 'Relocatable object',
    2: 'Demand-paged executable',
    3: 'Fixed VM shared library',
    4: 'Core file',
    5: 'Preloaded executable',
    6: 'Dynamically bound shared library',
    7: 'Dynamic link editor',
    8: 'Dynamically bound bundle',
    9: 'Shared library stub for static linking only',
    10: 'Companion file with only debug sections',
    11: 'x86_64 kext',
}

MACHO_MAGICS = {
    b"\xfe\xed\xfa\xce": (0, BIG_ENDIAN), # 32-bit big endian
    b"\xce\xfa\xed\xfe": (0, LITTLE_ENDIAN), # 32-bit little endian
    b"\xfe\xed\xfa\xcf": (1, BIG_ENDIAN), # 64-bit big endian
    b"\xcf\xfa\xed\xfe": (1, LITTLE_ENDIAN), # 64-bit little endian
}

class MachoHeader(FieldSet):
    def createFields(self):
        yield Bytes(self, "magic", 4, "Mach-O signature")
        yield Enum(Int32(self, "cputype"), CPU_TYPE)
        yield Int32(self, "cpusubtype")
        yield Enum(UInt32(self, "filetype"), FILE_TYPE)
        yield UInt32(self, "ncmds")
        yield UInt32(self, "sizeofcmds")
        yield UInt32(self, "flags")
        if self.parent.is64bit:
            yield UInt32(self, "reserved")

class MachoLoadCommand(FieldSet):
    LOAD_COMMANDS = {
    }

    def createFields(self):
        yield Enum(UInt32(self, "cmd"), self.LOAD_COMMANDS)
        yield UInt32(self, "cmdsize")
        self._size = self['cmdsize'].value * 8

class MachoFileBase(RootSeekableFieldSet):
    def createFields(self):
        baseaddr = self.absolute_address
        # Choose size and endianness based on magic
        magic = self.stream.readBytes(baseaddr, 4)
        self.is64bit, self.endian = MACHO_MAGICS[magic]

        yield MachoHeader(self, "header", "Header")
        for i in range(self['header/ncmds'].value):
            yield MachoLoadCommand(self, "load_command[]")

    def createDescription(self):
        return "Mach-O program/library: %s" % (self["header/cputype"].display)

class MachoFile(HachoirParser, MachoFileBase):
    PARSER_TAGS = {
        "id": "macho",
        "category": "program",
        "file_ext": ("dylib", "bundle", "o", ""),
        "min_size": (28+56)*8,  # Header + one segment load command
        "mime": (
            "application/x-executable",
            "application/x-object",
            "application/x-sharedlib",
            "application/x-executable-file",
            "application/x-coredump"),
        "magic": tuple((m,0) for m in MACHO_MAGICS),
        "description": "Mach-O program/library"
    }
    endian = BIG_ENDIAN

    def __init__(self, stream, **args):
        MachoFileBase.__init__(self, None, "root", stream, None, stream.askSize(self))
        HachoirParser.__init__(self, stream, **args)

    def validate(self):
        if self.stream.readBytes(0, 4) not in MACHO_MAGICS:
            return "Invalid magic"
        return True

class MachoFatArch(FieldSet):
    def createFields(self):
        yield Enum(Int32(self, "cputype"), CPU_TYPE)
        yield Int32(self, "cpusubtype")
        yield textHandler(UInt32(self, "offset"), hexadecimal)
        yield UInt32(self, "size")
        yield UInt32(self, "align")
        self['align'].createDescription = lambda: str(1 << self['align'].value)

class MachoFatHeader(FieldSet):
    def createFields(self):
        yield Bytes(self, "magic", 4, "Mach-O signature")
        yield UInt32(self, "nfat_arch", "Number of architectures in this fat file")
        for i in range(self['nfat_arch'].value):
            yield MachoFatArch(self, 'arch[]')

class MachoFatFile(HachoirParser, RootSeekableFieldSet):
    MAGIC_BE = b"\xca\xfe\xba\xbe"
    MAGIC_LE = b"\xbe\xba\xfe\xca"

    PARSER_TAGS = {
        "id": "macho_fat",
        "category": "program",
        "file_ext": ("dylib", "bundle", ""),
        # One page + size for one arch
        "min_size": 4096*8 + MachoFile.PARSER_TAGS['min_size'],
        "mime": (
            "application/x-executable",
            "application/x-object",
            "application/x-sharedlib",
            "application/x-executable-file",
            "application/x-coredump"),
        "magic": ((MAGIC_LE, 0), (MAGIC_BE, 0)),
        "description": "Mach-O fat program/library"
    }
    endian = BIG_ENDIAN

    def __init__(self, stream, **args):
        RootSeekableFieldSet.__init__(self, None, "root", stream, None, stream.askSize(self))
        HachoirParser.__init__(self, stream, **args)

    def validate(self):
        if self.stream.readBytes(0, 4) not in (self.MAGIC_LE, self.MAGIC_BE):
            return "Invalid magic"
        if self['header/nfat_arch'].value >= 16:
            # This helps to distinguish mach-o from java.
            return "Too many architectures"
        return True

    def createFields(self):
        # Choose the right endian based on file magic
        if self.stream.readBytes(0, 4) == self.MAGIC_LE:
            self.endian = LITTLE_ENDIAN
        else:
            self.endian = BIG_ENDIAN

        # Parse header and program headers
        yield MachoFatHeader(self, "header", "Header")
        for arch in self['header'].array('arch'):
            self.seekByte(arch['offset'].value)
            yield MachoFileBase(self, 'file[]', self.stream, None, arch['size'].value * 8)
