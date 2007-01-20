"""
Parser for resource of Microsoft Windows Portable Executable (PE).

Author: Victor Stinner
Creation date: 2007-01-19
"""

from hachoir_core.field import (FieldSet, Enum,
    Bit, Bits,
    UInt8, UInt16, UInt32,
    RawBytes, NullBytes, String)
from hachoir_core.text_handler import timestampUNIX, humanFilesize
from hachoir_core.tools import createDict

RESOURCE_TYPE = {
    1: ("cursor[]", "Cursor", None),
    2: ("bitmap[]", "Bitmap", None),
    3: ("icon[]", "Icon", None),
    4: ("menu[]", "Menu", None),
    5: ("dialog[]", "Dialog", None),
    6: ("string_table[]", "String table", None),
    7: ("font_dir[]", "Font directory", None),
    8: ("font[]", "Font", None),
    9: ("accelerators[]", "Accelerators", None),
    10: ("raw_res[]", "Unformatted resource data", None),
    11: ("message_table[]", "Message table", None),
    12: ("group_cursor[]", "Group cursor", None),
    14: ("group_icon[]", "Group icon", None),
    16: ("version_info", "Version information", None),
}

class Entry(FieldSet):
    static_size = 16*8

    def __init__(self, parent, name, inode=None):
        FieldSet.__init__(self, parent, name)
        self.inode = inode

    def createFields(self):
        yield UInt32(self, "rva")
        yield UInt32(self, "size", text_handler=humanFilesize)
        yield UInt32(self, "codepage")
        yield NullBytes(self, "reserved", 4)

    def createDescription(self):
        return "Entry #%u: offset=%s size=%s" % (
            self.inode["offset"].value, self["rva"].value, self["size"].display)

class NameOffset(FieldSet):
    def createFields(self):
        yield UInt32(self, "name")
        yield Bits(self, "offset", 31)
        yield Bit(self, "is_name")

class IndexOffset(FieldSet):
    TYPE_DESC = createDict(RESOURCE_TYPE, 1)

    def __init__(self, parent, name, res_type=None):
        FieldSet.__init__(self, parent, name)
        self.res_type = res_type

    def createFields(self):
        yield Enum(UInt32(self, "type"), self.TYPE_DESC)
        yield Bits(self, "offset", 31)
        yield Bit(self, "is_subdir")

    def createDescription(self):
        if self["is_subdir"].value:
            return "Sub-directory: %s at %s" % (self["type"].display, self["offset"].value)
        else:
            return "Index: ID %s at %s" % (self["type"].display, self["offset"].value)

class ResourceContent(FieldSet):
    def __init__(self, parent, name, entry, size=None):
        FieldSet.__init__(self, parent, name, size=entry["size"].value*8)
        self.entry = entry
        res_type = self.getResType()
        if res_type in RESOURCE_TYPE:
            self._name, description, self._parser = RESOURCE_TYPE[res_type]
        else:
            self._parser = None

    def getResID(self):
        return self.entry.inode["offset"].value

    def getResType(self):
        return self.entry.inode.res_type

    def createFields(self):
        if self._parser:
            for field in self._parser(self):
                yield field
        else:
            yield RawBytes(self, "content", self.size//8)

    def createDescription(self):
        return "Resource #%u content: type=%s" % (
            self.getResID(), self.getResType())

class Header(FieldSet):
    static_size = 16*8
    def createFields(self):
        yield NullBytes(self, "options", 4)
        yield UInt32(self, "creation_date", text_handler=timestampUNIX)
        yield UInt16(self, "maj_ver", "Major version")
        yield UInt16(self, "min_ver", "Minor version")
        yield UInt16(self, "nb_name", "Number of named entries")
        yield UInt16(self, "nb_index", "Number of indexed entries")
    def createDescription(self):
        text = "Resource header"
        info = []
        if self["nb_name"].value:
            info.append("%u name" % self["nb_name"].value)
        if self["nb_index"].value:
            info.append("%u index" % self["nb_index"].value)
        if self["creation_date"].value:
            info.append(self["creation_date"].display)
        if info:
            return "%s: %s" % (text, ", ".join(info))
        else:
            return text

class Name(FieldSet):
    def createFields(self):
        yield UInt16(self, "length")
        size = min(self["length"].value, 255)
        if size:
            yield String(self, "name", size, charset="UTF-16LE")

class Directory(FieldSet):
    def __init__(self, parent, name, res_type=None):
        FieldSet.__init__(self, parent, name)
        nb_entries = self["header/nb_name"].value + self["header/nb_index"].value
        self._size = Header.static_size + nb_entries * 64
        self.res_type = res_type

    def createFields(self):
        yield Header(self, "header")
        hdr = self["header"]
        for index in xrange(hdr["nb_name"].value):
            yield NameOffset(self, "name[]")
        for index in xrange(hdr["nb_index"].value):
            yield IndexOffset(self, "index[]", self.res_type)

    def createDescription(self):
        return self["header"].description

class Resource(FieldSet):
    def parseSub(self, directory, name, depth):
        indexes = []
        for index in directory.array("index"):
            if index["is_subdir"].value:
                indexes.append(index)

        indexes.sort(key=lambda index: index["offset"].value)
        for index in indexes:
            try:
                padding = self.seekByte(index["offset"].value)
            except Exception, err:
                self.error("ERROR: %s, index=%s" % (err, index))
                raise
            if padding:
                yield padding
            if depth == 1:
                res_type = index["type"].value
            else:
                res_type = directory.res_type
            yield Directory(self, name, res_type)

    def createFields(self):
        # Parse directories
        depth = 0
        subdir = Directory(self, "root")
        yield subdir
        subdirs = [subdir]
        alldirs = [subdir]
        while subdirs:
            depth += 1
            newsubdirs = []
            for index, subdir in enumerate(subdirs):
                name = "directory[%u][%u][]" % (depth, index)
                for field in self.parseSub(subdir, name, depth):
                    newsubdirs.append(field)
                    yield field
            subdirs = newsubdirs
            alldirs.extend(subdirs)

        # Create resource list
        resources = []
        for directory in alldirs:
            for index in directory.array("index"):
                if not index["is_subdir"].value:
                    resources.append(index)

        # Parse entries
        entries = []
        for resource in resources:
            padding = self.seekByte(resource["offset"].value)
            if padding:
                yield padding
            entry = Entry(self, "entry[]", inode=resource)
            yield entry
            entries.append(entry)
        entries.sort(key=lambda entry: entry["rva"].value)

        # Parse resource content
        for entry in entries:
            offset = self.root.rva2file(entry["rva"].value)
            padding = self.seekByte(offset, relative=False, null=True)
            if padding:
                yield padding
            yield ResourceContent(self, "content[]", entry)

        size = (self.size - self.current_size) // 8
        if size:
            yield NullBytes(self, "padding_end", size)

