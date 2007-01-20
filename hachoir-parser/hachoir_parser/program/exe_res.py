"""
Parser for resource of Microsoft Windows Portable Executable (PE).

Author: Victor Stinner
Creation date: 2007-01-19
"""

from hachoir_core.field import (FieldSet, RawBytes,
    Bit, Bits, UInt8, UInt16, UInt32, NullBytes, String)
from hachoir_core.text_handler import timestampUNIX, humanFilesize

class Entry(FieldSet):
    size = 16*8
    def createFields(self):
        yield UInt32(self, "offset")
        yield UInt32(self, "size", text_handler=humanFilesize)
        yield UInt32(self, "codepage")
        yield NullBytes(self, "reserved", 4)

    def createDescription(self):
        return "Entry: offset=%s size=%s" % (
            self["offset"].value, self["size"].display)

class ResourceContent(FieldSet):
    def createFields(self):
        yield RawBytes(self, "content", size=self.size)

#class Entry(FieldSet):
#    def createFields(self):
#        yield UInt8(self, "is_directory", "(boolean: 1 is True, 0 is False)")
#        yield UInt8(self, "is_named", "Offset points to a name?")
#        yield UInt16(self, "name_length", "Name length")
#        yield UInt32(self, "name_off", "Name offset")
#        if self["is_directory"].value:
#            desc = "Offset of next level"
#        else:
#            desc = "Offset of resource header"
#        yield UInt32(self, "offset", desc)

class NameOffset(FieldSet):
    def createFields(self):
        yield UInt32(self, "name")
        yield Bits(self, "offset", 31)
        yield Bit(self, "is_name")

class IndexOffset(FieldSet):
    def createFields(self):
        yield UInt32(self, "name")
        yield Bits(self, "offset", 31)
        yield Bit(self, "is_subdir")

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
    def __init__(self, *args):
        FieldSet.__init__(self, *args)
        nb_entries = self["header/nb_name"].value + self["header/nb_index"].value
        self._size = Header.static_size + nb_entries * 64

    def createFields(self):
        yield Header(self, "header")
        hdr = self["header"]
        for index in xrange(hdr["nb_name"].value):
            yield NameOffset(self, "name[]")
        for index in xrange(hdr["nb_index"].value):
            yield IndexOffset(self, "index[]")

    def createDescription(self):
        return self["header"].description

class Resource(FieldSet):
    def parseSub(self, directory, name):
        subdirs = []
        for subdir in directory.array("index"):
            if subdir["is_subdir"].value:
                subdirs.append(subdir)

        subdirs.sort(key=lambda subdir: subdir["offset"].value)
        for subdir in subdirs:
            try:
                padding = self.seekByte(subdir["offset"].value)
            except Exception, err:
                self.error("ERROR: %s, subdir=%s" % (err, subdir))
                raise
            if padding:
                yield padding
            yield Directory(self, name)

    def createFields(self):
        # Parse directories
        depth = 0
        subdir = Directory(self, "directory[%u]" % depth)
        yield subdir
        subdirs = [subdir]
        alldirs = [subdir]
        while subdirs:
            depth += 1
            newsubdirs = []
            for index, subdir in enumerate(subdirs):
                for field in self.parseSub(subdir, "directory[%u][%u][]" % (depth, index)):
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
            entry = Entry(self, "entry[]")
            yield entry
            entries.append(entry)
        entries.sort(key=lambda entry: entry["offset"].value)

        # Parse resource content
        for entry in entries:
            offset = self.root.rva2file(entry["offset"].value)
            padding = self.seekByte(offset, relative=False, null=True)
            if padding:
                yield padding
            yield ResourceContent(self, "content[]", "Content of %s" % entry.path, size=entry["size"].value*8)

        size = (self.size - self.current_size) // 8
        if size:
            yield NullBytes(self, "padding_end", size)

