"""
.torrent metainfo file parser

http://wiki.theory.org/BitTorrentSpecification#Metainfo_File_Structure

Status: To statufy
Author: Christophe Gisquet <christophe.gisquet@free.fr>
"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    String, RawBytes)
from hachoir_core.text_handler import (humanFilesize,
    humanDatetime, doTimestampUNIX)
from hachoir_core.endian import LITTLE_ENDIAN
from hachoir_core.tools import makePrintable

# Maximum number of bytes for string length
MAX_STRING_LENGTH = 6   # length in 0..999999

# Maximum number of bytes for integer value
MAX_INTEGER_SIZE = 11    # value in -9999999999..99999999999

TAGS = {
    # Means start of a byte string...
    '1': "String",
    '2': "String",
    '3': "String",
    '4': "String",
    '5': "String",
    '6': "String",
    '7': "String",
    '8': "String",
    '9': "String",
    'd': "Dictionary",
    'i': "Integer",
    'l': "List",
}

class Entry(FieldSet):
    def parseString(self):
        addr = self.absolute_address
#        self._name = "string[]"
        # <string length encoded in base ten ASCII>:<string data>
        len = self.stream.searchBytesLength(':', False, addr, addr+(MAX_STRING_LENGTH+1)*8)
        if len is None:
            raise ParserError("Torrent: unable to find string separator (':')")
        val = String(self, "length", len, "String length")
        yield val
        try:
            len = int(val.value)
        except ValueError:
            len = -1
        if len < 0:
            raise ParserError("Invalid string length (%s)" % makePrintable(val.value, "ASCII", to_unicode=True))
        yield String(self, "separator", 1, "String length/value separator")
        if not len:
            self.info("Empty string: len=%i" % len)
            return
        if len<512: # Probably raw data
            val = String(self, "value", len, "String value")
            yield val
            self.info("String '%s': len=%i" % (val.value, len))
#            self._name = val.value.replace(" ", "_").replace("/", "_")
        else:
            yield RawBytes(self, "value", len, "Raw data")
            self.info("Raw data: len=%i" % len)
#            self._name = "raw_data"

    def parseDictionary(self):
        self._name = "dictionary[]"
        # d<bencoded string><bencoded element>e
        yield String(self, "start", 1, "Dictionary start delimiter (d)", charset="ASCII")
        while self.stream.readBytes(self.absolute_address+self.current_size, 1) != "e":
            yield DictionaryItem(self, "item[]")
        yield String(self, "end", 1, "Dictionary end delimiter")

    def parseInteger(self):
        # i<integer encoded in base ten ASCII>e
        yield String(self, "start", 1, "Integer start delimiter (i)", charset="ASCII")
        addr = self.absolute_address+self.current_size
        len = self.stream.searchBytesLength('e', False, addr, addr+(MAX_INTEGER_SIZE+1)*8)
        if len is None:
            raise ParserError("Torrent: Unable to find integer end delimiter (e)!")
        if not len:
            raise ParserError("Torrent: error, empty integer!")
        val = String(self, "value", len, "Integer value", charset="ASCII")
        yield val
        self.info("%i" % int(val.value))
        yield String(self, "end", 1, "Integer end delimiter")

    def parseList(self):
        # l<bencoded values>e
        self._name = "list[]"
        yield String(self, "start", 1, "List start delimiter")
        while self.stream.readBytes(self.absolute_address+self.current_size, 1) != "e":
            yield Entry(self, "element[]")
        yield String(self, "end", 1, "List end delimiter")

    def createFields(self):
        type = self.stream.readBytes(self.absolute_address, 1)
        name = TAGS.get(type, None)
        if name == "String":
            for field in self.parseString():
                yield field
        elif name == "Dictionary":
            for field in self.parseDictionary():
                yield field
        elif name == "Integer":
            for field in self.parseInteger():
                yield field
        elif name == "List":
            for field in self.parseList():
                yield field
        else:
            raise ParserError("Torrent: Entry of type %r not handled" % type)

class DictionaryItem(Entry):
    def createDescription(self):
        #return "%s=%s" % (self["key"].value, self["value"].display)
        key = self[0]
        if "value" in key:
            key = key["value"].value
        else:
            key = key.path
        value = self[1]
        if "value" in value:
            return "%s=%s" % (key, value["value"].value)
        else:
            return key

    def createFields(self):
        input = Entry(self, "key")
        yield input
        output = Entry(self, "value")
        yield output

        # Postprocess names
        if input._name == "creation_date":
            timestamp = doTimestampUNIX(int(output._name))
            output._name = humanDatetime(timestamp).replace(" ", "_")
        #if input._name == "length":
        #    output._name = humanFilesize(output._name)
        #self.info("%s => %s" % (input._name, output._name))

class TorrentFile(Parser):
    endian = LITTLE_ENDIAN
    MAGIC = "d8:announce"
    tags = {
        "id": "torrent",
        "category": "misc",
        "file_ext": ("torrent",),
        "min_size": 50*8,
        "magic": ((MAGIC, 0),),
        "description": "Torrent metainfo file"
    }

    def validate(self):
        self.info(">>>>>>>>>>>>   THERE   <<<<<<<<<<<")
        if self.stream.readBytes(0, len(self.MAGIC)) != self.MAGIC:
            return "Invalid magic"
        return True

    def createFields(self):
        yield Entry(self, "root", size=self.size)

