"""
.torrent metainfo file parser

http://wiki.theory.org/BitTorrentSpecification#Metainfo_File_Structure

Status: To statufy
Author: Christophe Gisquet <christophe.gisquet@free.fr>
"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    Bit, Bits, Enum,
    UInt8, UInt16, UInt32, UInt64,
    String,
    RawBytes)
from hachoir_core.text_handler import (humanFilesize,
    hexadecimal,
    humanDatetime, doTimestampUNIX)
from hachoir_core.endian import LITTLE_ENDIAN
from hachoir_parser.archive.rar import MSDOSFileAttr
from hachoir_core.error import info

class Entry(FieldSet):
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
        'l': "List"
    }

    def createFields(self):
        type = self.stream.readBytes(self.absolute_address+self.current_size, 1)
        name = None
        if type in self.TAGS:
            name = self.TAGS[type]

        if name:
            if name == "String":
                # <string length encoded in base ten ASCII>:<string data>
                len = self.stream.searchBytesLength(':', False, self.absolute_address+self.current_size)
                if len is not None:
                    val = String(self, "length", len, "String length")
                    yield val
                    len = int(val.value)
                    yield String(self, "separator", 1, "String length/value separator")
                    if len>0:
                        if len<512: # Probably raw data
                            val = String(self, "value", len, "String value")
                            yield val
                            info("String '%s': len=%i" % (val.value, len))
                            self._name = val.value.replace(" ", "_").replace("/", "_")
                        else:
                            yield RawBytes(self, "value", len, "Raw data")
                            info("Raw data: len=%i" % len)
                            self._name = "raw_data"
                    else:
                        info("No string: len=%i" % len)
                        self._name = "string[]"
                else: self._name = "string[]"
            elif name == "Dictionary":
                # d<bencoded string><bencoded element>e
                yield String(self, "start", 1, "Dictionary start delimiter")
                while self.stream.readBytes(self.absolute_address+self.current_size, 1) != "e":
                    #iaddr = self.absolute_address + self.current_size
                    input = Entry(self, "in[]")
                    yield input
                    #oaddr = self.absolute_address + self.current_size
                    output = Entry(self, "out[]")
                    yield output

                    # Postprocess names
                    if input._name == "creation_date":
                        timestamp = doTimestampUNIX(int(output._name))
                        output._name = humanDatetime(timestamp).replace(" ", "_")
                    #if input._name == "length":
                    #    output._name = humanFilesize(output._name)
                    #info("%s => %s" % (input._name, output._name))
                yield String(self, "end", 1, "Dictionary end delimiter")
                self._name = "dictionary[]"
            elif name == "Integer":
                # i<integer encoded in base ten ASCII>e
                yield String(self, "start", 1, "Integer start delimiter")
                len = self.stream.searchBytesLength('e', False, self.absolute_address+self.current_size)
                if len is not None:
                    if len>0:
                        val = String(self, "value", len, "Integer value")
                        yield val
                        info("%i" % int(val.value))
                        self._name = val.value
                    yield String(self, "end", 1, "Integer end delimiter")
            elif name == "List":
                # l<bencoded values>e
                yield String(self, "start", 1, "List start delimiter")
                while self.stream.readBytes(self.absolute_address+self.current_size, 1) != "e":
                    yield Entry(self, "element[]")
                yield String(self, "end", 1, "List end delimiter")
                self._name = "list[]"
            else:
                yield String(self, "unknown[]", "Unknown element %s" % type)
        else:
            info("Entry of type '%s' not handled" % type)
            yield String(self, "unknown[]", "Unknown element %s" % type)

class TorrentFile(Parser):
    endian = LITTLE_ENDIAN
    MAGIC = "d8:announce"
    tags = {
        "id": "torrent",
        "category": "misc",
        "file_ext": ("torrent",),
        "mime": ["application/i-do-not-know"],
        "min_size": 50*8,
        "description": "Torrent metainfo file"
    }

    def validate(self):
        info(">>>>>>>>>>>>   THERE   <<<<<<<<<<<")
        if self.stream.readBytes(0, len(self.MAGIC)) != self.MAGIC:
            return "Invalid magic"
        return True

    def createFields(self):
        while not self.eof:
            yield Entry(self, "block[]")
