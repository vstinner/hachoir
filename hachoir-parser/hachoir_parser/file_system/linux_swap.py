"""
Linux swap file.

Documentation: Linux kernel source code, files:
 - mm/swapfile.c
 - include/linux/swap.h

Author: Victor Stinner
Creation date: 25 december 2006 (christmas ;-))
"""

from hachoir_parser import Parser
from hachoir_core.field import UInt32, PaddingBytes, RawBytes, String
from hachoir_core.endian import LITTLE_ENDIAN
from hachoir_core.tools import humanFilesize

PAGE_SIZE = 4096

class LinuxSwapFile(Parser):
    tags = {
        "id": "linux_swap",
        "category": "file_system",
        "min_size": PAGE_SIZE*8,
        "description": "Linux swap file",
        "magic": (
            ("SWAP-SPACE", (PAGE_SIZE-10)*8),
            ("SWAPSPACE2", (PAGE_SIZE-10)*8),
            ("S1SUSPEND\0", (PAGE_SIZE-10)*8),
        ),
    }
    endian = LITTLE_ENDIAN

    def validate(self):
        magic = self.stream.readBytes((PAGE_SIZE-10)*8, 10)
        if magic not in ("SWAP-SPACE", "SWAPSPACE2", "S1SUSPEND\0"):
            return "Unkown magic string"
        return True

    def getPageCount(self):
        """
        Number of pages which can really be used for swapping:
        number of page minus bad pages minus one page (used for the header)
        """
        # -1 because first page is used for the header
        return self["last_page"].value - self["nb_badpage"].value - 1

    def createDescription(self):
        if self["magic"].value == "S1SUSPEND\0":
            text = "Suspend swap file version 1"
        elif self["magic"].value == "SWAPSPACE2":
            text = "Linux swap file version 2"
        else:
            text = "Linux swap file version 1"
        nb_page = self.getPageCount()
        return "%s, page size: %s, %s pages" % (
            text, humanFilesize(PAGE_SIZE), nb_page)

    def createFields(self):
        yield RawBytes(self, "boot", 1024, "Space for disklabel etc.")
        yield UInt32(self, "version")
        yield UInt32(self, "last_page")
        # If swap file is a regular file, nb_badpage have to be zero
        yield UInt32(self, "nb_badpage")
        yield PaddingBytes(self, "padding[]", 125*4)
        for index in xrange(self["nb_badpage"].value):
            yield UInt32(self, "badpage[]")
        size = PAGE_SIZE - 10 - self.current_size//8
        if size:
            yield PaddingBytes(self, "padding[]", size)
        yield String(self, "magic", 10, charset="ASCII")

        for index in xrange(self["last_page"].value):
            yield RawBytes(self, "page[]", PAGE_SIZE)

