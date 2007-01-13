"""
PNG picture file parser.

Author: Victor Stinner
"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    UInt8, UInt16, UInt32,
    String, CString,
    Bytes, RawBytes,
    Bit, RawBits,
    Enum)
from hachoir_parser.image.common import RGB
from hachoir_core.text_handler import hexadecimal
from hachoir_core.endian import NETWORK_ENDIAN
from hachoir_core.tools import humanFilesize, humanDatetime
from datetime import datetime

COMPRESSION_NAME = {
    0: "deflate" # with 32K sliding window
}
MAX_CHUNK_SIZE = 500 * 1024 # Maximum chunk size (500 KB)

def headerParse(self):
    yield UInt32(self, "width", "Width (pixels)")
    yield UInt32(self, "height", "Height (pixels)")
    yield UInt8(self, "bpp", "Bits per pixel")
    yield RawBits(self, "reserved", 5)
    yield Bit(self, "alpha", "Alpha channel used?")
    yield Bit(self, "color", "Color used?")
    yield Bit(self, "palette", "Palette used?")
    yield Enum(UInt8(self, "compression", "Compression method"), COMPRESSION_NAME)
    yield UInt8(self, "filter", "Filter method")
    yield UInt8(self, "interlace", "Interlace method")

def headerDescription(self):
    return "Header: %ux%u pixels and %u bits/pixel" % \
        (self["width"].value, self["height"].value, self["bpp"].value)

def paletteParse(self):
    size = self["size"].value
    if (size % 3) != 0:
        raise ParserError("Palette have invalid size (%s), should be 3*n!" % size)
    nb_colors = size // 3
    for index in xrange(nb_colors):
        yield RGB(self, "color[]")

def paletteDescription(self):
    return "Palette: %u colors" % (self["size"].value // 3)

def gammaParse(self):
    yield UInt32(self, "gamma", "Gamma (x10,000)")
def gammaValue(self):
    return float(self["gamma"].value) / 10000
def gammaDescription(self):
    return "Gamma: %.3f" % self.value

def textParse(self):
    yield CString(self, "keyword", "Keyword", charset="ISO-8859-1")
    length = self["size"].value - self["keyword"].size/8
    if length:
        yield String(self, "text", length, "Text", charset="ISO-8859-1")

def textDescription(self):
    if "text" in self:
        return u'Text: %s' % self["text"].display
    else:
        return u'Text'

def timestampParse(self):
    yield UInt16(self, "year", "Year")
    yield UInt8(self, "month", "Month")
    yield UInt8(self, "day", "Day")
    yield UInt8(self, "hour", "Hour")
    yield UInt8(self, "minute", "Minute")
    yield UInt8(self, "second", "Second")

def timestampValue(self):
    value = datetime(
        self["year"].value, self["month"].value, self["day"].value,
        self["hour"].value, self["minute"].value, self["second"].value)
    return humanDatetime(value)

unit_name = {
    0: "Unknow",
    1: "Meter"
}

def physicalParse(self):
    yield UInt32(self, "pixel_per_unit_x", "Pixel per unit, X axis")
    yield UInt32(self, "pixel_per_unit_y", "Pixel per unit, Y axis")
    yield Enum(UInt8(self, "unit", "Unit type"), unit_name)

def physicalDescription(self):
    x = self["pixel_per_unit_x"].value
    y = self["pixel_per_unit_y"].value
    desc = "Physical: %ux%u pixels" % (x,y)
    if self["unit"].value == 1:
        desc += " per meter"
    return desc

def parseBackgroundColor(parent):
    yield UInt16(parent, "red")
    yield UInt16(parent, "green")
    yield UInt16(parent, "blue")

def backgroundColorDesc(parent):
    rgb = parent["red"].value, parent["green"].value, parent["blue"].value
    name = RGB.color_name.get(rgb)
    if not name:
        name = "#%02X%02X%02X" % rgb
    return "Background color: %s" % name


class Chunk(FieldSet):
    tag_info = {
        "tIME": ("time", timestampParse, "Timestamp", timestampValue),
        "pHYs": ("physical", physicalParse, physicalDescription, None),
        "IHDR": ("header", headerParse, headerDescription, None),
        "PLTE": ("palette", paletteParse, paletteDescription, None),
        "gAMA": ("gamma", gammaParse, gammaDescription, gammaValue),
        "tEXt": ("text[]", textParse, textDescription, None),

        "bKGD": ("background", parseBackgroundColor, backgroundColorDesc, None),
        "IDAT": ("data[]", None, "Image data", None),
        "iTXt": ("utf8_text[]", None, "International text (encoded in UTF-8)", None),
        "zTXt": ("comp_text[]", None, "Compressed text", None),
        "IEND": ("end", None, "End", None)
    }

    def createValueFunc(self):
        return self.value_func(self)

    def __init__(self, parent, name, description=None):
        FieldSet.__init__(self, parent, name, description)
        self._size = (self["size"].value + 3*4) * 8
        if MAX_CHUNK_SIZE < (self._size//8):
            raise ParserError("PNG: Chunk is too big (%s)"
                % humanFilesize(self._size//8))
        tag = self["tag"].value
        self.desc_func = None
        self.value_func = None
        if tag in self.tag_info:
            self._name, self.parse_func, desc, value_func = self.tag_info[tag]
            if value_func:
                self.value_func = value_func
                self.createValue = self.createValueFunc
            if desc:
                if isinstance(desc, str):
                    self._description = desc
                else:
                    self.desc_func = desc
        else:
            self._description = ""
            self.parse_func = None

    def createFields(self):
        yield UInt32(self, "size", "Size")
        yield String(self, "tag", 4, "Tag", charset="ASCII")

        size = self["size"].value
        if size != 0:
            if self.parse_func:
                for field in self.parse_func(self):
                    yield field
            else:
                yield RawBytes(self, "content", size, "Data")
        yield UInt32(self, "crc32", "CRC32", text_handler=hexadecimal)

    def createDescription(self):
        if self.desc_func:
            return self.desc_func(self)
        else:
            return "Chunk: %s" % self["tag"].display

class PngFile(Parser):
    tags = {
        "file_ext": ("png",),
        "mime": ("image/png", "image/x-png"),
        "min_size": 8*8, # just the identifier
        "magic": [('\x89PNG\r\n\x1A\n', 0)],
        "description": "Portable Network Graphics (PNG) picture"
    }
    endian = NETWORK_ENDIAN

    def validate(self):
        if self["id"].value != '\x89PNG\r\n\x1A\n':
            return "Invalid signature"
        if self[1].name != "header":
            return "First chunk is not header"
        return True

    def createFields(self):
        yield Bytes(self, "id", 8, r"PNG identifier ('\x89PNG\r\n\x1A\n')")
        while not self.eof:
            yield Chunk(self, "chunk[]")

    def createDescription(self):
        header = self["header"]
        desc = "PNG picture: %ux%ux%u" % (
            header["width"].value, header["height"].value, header["bpp"].value)
        if header["alpha"].value:
            desc += " (alpha layer)"
        return desc

    def createContentSize(self):
        field = self["header"]
        start = field.absolute_address + field.size
        end = self.stream.searchBytes("\0\0\0\0IEND\xae\x42\x60\x82", start)
        if end is not None:
            return end + 12*8
        return None

