from hachoir_core.field import (FieldSet, RawBytes,
    Bit, Bits, UInt8, UInt16, UInt32, NullBytes, String)
from hachoir_core.text_handler import timestampUNIX

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
        yield Bit(self, "is_subdir")

class Header(FieldSet):
    def createFields(self):
        yield NullBytes(self, "options", 4)
        yield UInt32(self, "creation_date", text_handler=timestampUNIX)
        yield UInt16(self, "maj_ver", "Major version")
        yield UInt16(self, "min_ver", "Minor version")
        yield UInt16(self, "nb_name_entry", "Number of named entries")
        yield UInt16(self, "nb_index_entry", "Number of indexed entries")

class Name(FieldSet):
    def createFields(self):
        yield UInt16(self, "length")
        size = min(self["length"].value, 255)
        if size:
            yield String(self, "name", size, charset="UTF-16LE")

class Directory(FieldSet):
    def createFields(self):
        yield Header(self, "header")
        hdr = self["header"]
        for index in xrange(hdr["nb_name_entry"].value + hdr["nb_index_entry"].value):
            yield NameOffset(self, "directory[]")

class Resource(FieldSet):
    def parseSub(self, directory, name):
        subdirs = []
        for subdir in directory.array("directory"):
            if subdir["is_subdir"].value:
                subdirs.append(subdir)

        subdirs.sort(key=lambda subdir: subdir["offset"].value)
        for subdir in subdirs:
            padding = self.seekByte(subdir["offset"].value)
            if padding:
                yield padding
            yield Directory(self, name)

    def createFields(self):
        yield Directory(self, "root")
        for field in self.parseSub(self["root"], "subdir[]"):
            yield field

        size = (self.size - self.current_size) // 8
        if size:
            yield RawBytes(self, "end", size)

