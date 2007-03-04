from hachoir_core.field import (FieldSet,
    UInt16, UInt32, Enum, String, Bytes)
from hachoir_parser.video.fourcc import video_fourcc_name
from hachoir_core.bits import str2hex
from hachoir_core.text_handler import hexadecimal

class GUID(FieldSet):
    """ Windows GUID (128 bits) """
    static_size = 128
    def createFields(self):
        yield UInt32(self, "a", text_handler=hexadecimal)
        yield UInt16(self, "b", text_handler=hexadecimal)
        yield UInt16(self, "c", text_handler=hexadecimal)
        yield Bytes(self, "d", 8)

#        yield UInt16(self, "d", text_handler=hexadecimal)
#        yield UInt16(self, "e", text_handler=hexadecimal)
#        yield UInt32(self, "f", text_handler=hexadecimal)

    def createValue(self):
        d = self["d"].value
        return "%08X-%04X-%04X-%s-%s-%s-%s" % (
            self["a"].value,
            self["b"].value,
            self["c"].value,
            str2hex(d[:2]), str2hex(d[2:4]), str2hex(d[4:6]),str2hex(d[6:8]))

    def createRawDisplay(self):
        value = self.stream.readBytes(self.absolute_address, 16)
        return str2hex(value, format=r"\x%02x")

class BitmapInfoHeader(FieldSet):
    """ Win32 BITMAPINFOHEADER structure from GDI """
    static_size = 40*8

    compression_name = {
        0: "Uncompressed (RGB)",
        1: "RLE (8 bits)",
        2: "RLE (4 bits)",
        3: "Bitfields",
        4: "JPEG",
        5: "PNG"
    }

    def __init__(self, parent, name, use_fourcc=False):
        FieldSet.__init__(self, parent, name)
        self._use_fourcc = use_fourcc

    def createFields(self):
        yield UInt32(self, "hdr_size", "Header size (in bytes) (=40)")
        yield UInt32(self, "width", "Width")
        yield UInt32(self, "height", "Height")
        yield UInt16(self, "nb_planes", "Color planes")
        yield UInt16(self, "bpp", "Bits/pixel")
        if self._use_fourcc:
            yield Enum(String(self, "codec", 4, charset="ASCII"), video_fourcc_name)
        else:
            yield Enum(UInt32(self, "codec", "Compression"), self.compression_name)
        yield UInt32(self, "size", "Image size (in bytes)")
        yield UInt32(self, "xres", "X pixels per meter")
        yield UInt32(self, "yres", "Y pixels per meter")
        yield UInt32(self, "color_used", "Number of used colors")
        yield UInt32(self, "color_important", "Number of important colors")

    def createDescription(self):
        return "Bitmap info header: %ux%u pixels, %u bits/pixel" % \
            (self["width"].value, self["height"].value, self["bpp"].value)

