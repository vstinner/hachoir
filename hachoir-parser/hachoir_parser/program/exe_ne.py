from hachoir_core.field import (FieldSet,
    UInt8, UInt16, UInt32, Bytes,
    PaddingBits, NullBits, NullBytes,
    Bit)
from hachoir_core.text_handler import hexadecimal, humanFilesize

class NE_Header(FieldSet):
    static_size = 64*8
    def createFields(self):
        yield Bytes(self, "signature", 2, "New executable signature (NE)")
        yield UInt8(self, "link_ver", "Linker version number")
        yield UInt8(self, "link_rev", "Linker revision number")
        yield UInt16(self, "entry_table_ofst", "Offset to the entry table")
        yield UInt16(self, "entry_table_size", "Length (in bytes) of the entry table")
        yield NullBytes(self, "reserved[]", 4)

        yield Bit(self, "is_dll", "Is a dynamic-link library (DLL)?")
        yield Bit(self, "is_win_app", "Is a Windows application?")
        yield PaddingBits(self, "reserved[]", 9)
        yield Bit(self, "first_seg_code", "First segment contains code that loads the application?")
        yield NullBits(self, "reserved[]", 1)
        yield Bit(self, "link_error", "Load even if linker detects errors?")
        yield NullBits(self, "reserved[]", 1)
        yield Bit(self, "is_lib", "Is a library module?")

        yield UInt16(self, "auto_data_seg", "Automatic data segment number")
        yield UInt16(self, "local_heap_size", "Initial size (in bytes) of the local heap", text_handler=humanFilesize)
        yield UInt16(self, "stack_size", "Initial size (in bytes) of the stack", text_handler=humanFilesize)
        yield UInt32(self, "cs_ip", "Value of CS:IP", text_handler=hexadecimal)
        yield UInt32(self, "ss_sp", "Value of SS:SP", text_handler=hexadecimal)

        yield UInt16(self, "nb_entry_seg_tab", "Number of entries in the segment table")
        yield UInt16(self, "nb_entry_modref_tab", "Number of entries in the module-reference table")
        yield UInt16(self, "size_nonres_name_tab", "Number of bytes in the nonresident-name table", text_handler=humanFilesize)
        yield UInt16(self, "seg_tab_ofs", "Segment table offset")
        yield UInt16(self, "rsrc_ofs", "Resource offset")

        yield UInt16(self, "res_name_tab_ofs", "Resident-name table offset")
        yield UInt16(self, "mod_ref_tab_ofs", "Module-reference table offset")
        yield UInt16(self, "import_tab_ofs", "Imported-name table offset")

        yield UInt32(self, "non_res_name_tab_ofs", "Nonresident-name table offset")
        yield UInt16(self, "nb_mov_ent_pt", "Number of movable entry points")
        yield UInt16(self, "log2_sector_size", "Log2 of the segment sector size")
        yield UInt16(self, "nb_rsrc_seg", "Number of resource segments")

        yield Bit(self, "unknown_os_format", "Operating system format is unknown")
        yield PaddingBits(self, "reserved[]", 1)
        yield Bit(self, "os_windows", "Operating system is Microsoft Windows")
        yield NullBits(self, "reserved[]", 6)
        yield Bit(self, "is_win20_prot", "Is Windows 2.x application running in version 3.x protected mode")
        yield Bit(self, "is_win20_font", "Is Windows 2.x application supporting proportional fonts")
        yield Bit(self, "fast_load", "Contains a fast-load area?")
        yield NullBits(self, "reserved[]", 4)

        yield UInt16(self, "fastload_ofs", "Fast-load area offset (in sector)")
        yield UInt16(self, "fastload_size", "Fast-load area length (in sector)")

        yield NullBytes(self, "reserved[]", 2)
        yield UInt16(self, "win_version", "Expected Windows version number", text_handler=hexadecimal)

