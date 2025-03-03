"""
Gimp image parser (XCF file, ".xcf" extension).

You can find informations about XCF file in Gimp source code :
  https://gitlab.gnome.org/GNOME/gimp/-/tree/master/app/xcf
  files xcf-read.c and xcf-load.c

Author: Victor Stinner
"""

from hachoir.parser import Parser
from hachoir.field import (StaticFieldSet, FieldSet, ParserError,
                           UInt8, UInt32, UInt64, Enum, Float32, String, PascalString32, RawBytes)
from hachoir.parser.image.common import RGBA
from hachoir.core.endian import NETWORK_ENDIAN


class XcfCompression(FieldSet):
    static_size = 8
    COMPRESSION_NAME = {
        0: "None",
        1: "RLE",
        2: "Zlib",
        3: "Fractal"
    }

    def createFields(self):
        yield Enum(UInt8(self, "compression", "Compression method"), self.COMPRESSION_NAME)


class XcfResolution(StaticFieldSet):
    format = (
        (Float32, "xres", "X resolution in DPI"),
        (Float32, "yres", "Y resolution in DPI")
    )


class XcfTattoo(StaticFieldSet):
    format = ((UInt32, "tattoo", "Tattoo"),)


class LayerOffsets(StaticFieldSet):
    format = (
        (UInt32, "ofst_x", "Offset X"),
        (UInt32, "ofst_y", "Offset Y")
    )


class LayerMode(FieldSet):
    static_size = 32
    MODE_NAME = {
        # Since "ancient times":
        0: "Normal (legacy)",
        1: "Dissolve (legacy) [random dithering to discrete alpha)",
        2: "Behind (legacy) [not selectable in the GIMP UI]",
        3: "Multiply (legacy)",
        4: "Screen (legacy)",
        5: "Old broken Overlay",
        6: "Difference (legacy)",
        7: "Addition (legacy)",
        8: "Subtract (legacy)",
        9: "Darken only (legacy)",
        10: "Lighten only (legacy)",
        11: "Hue (HSV) (legacy)",
        12: "Saturation (HSV) (legacy)",
        13: "Color (HSL) (legacy)",
        14: "Value (HSV) (legacy)",
        15: "Divide (legacy)",
        16: "Dodge (legacy)",
        17: "Burn (legacy)",
        18: "Hard light (legacy)",
        # Since XCF 2 (GIMP 2.8)
        19: "Soft light (legacy)",
        20: "Grain extract (legacy)",
        21: "Grain merge (legacy)",
        22: "Color erase (legacy)",
        # Since XCF 9 (GIMP 2.10.0)
        23: "Overlay",
        24: "Hue (LCH)",
        25: "Chroma (LCH)",
        26: "Color (LCH)",
        27: "Lightness (LCH)",
        # Since XCF 10 (GIMP 2.10.0)
        29: "Behind",
        30: "Multiply",
        31: "Screen",
        32: "Difference",
        33: "Addition",
        34: "Subtract",
        35: "Darken only",
        36: "Lighten only",
        37: "Hue (HSV)",
        38: "Saturation (HSV)",
        39: "Color (HSL)",
        40: "Value (HSV)",
        41: "Divide",
        42: "Dodge",
        43: "Burn",
        44: "Hard light",
        45: "Soft light",
        46: "Grain extract",
        47: "Grain merge",
        48: "Vivid light",
        49: "Pin light",
        50: "Linear light",
        51: "Hard mix",
        52: "Exclusion",
        53: "Linear burn",
        54: "Luma/Luminance darken only",
        55: "Luma/Luminance lighten only",
        56: "Luminance",
        57: "Color erase",
        58: "Erase",
        59: "Merge",
        60: "Split",
        61: "Pass through",
    }

    def createFields(self):
        yield Enum(UInt32(self, "mode", "Layer mode"), self.MODE_NAME)


class GimpBoolean(UInt32):

    def __init__(self, parent, name):
        UInt32.__init__(self, parent, name)

    def createValue(self):
        return 1 == UInt32.createValue(self)


class XcfUnit(StaticFieldSet):
    format = ((UInt32, "unit", "Unit"),)


class XcfParasiteEntry(FieldSet):

    def createFields(self):
        yield PascalString32(self, "name", "Name", strip="\0", charset="UTF-8")
        yield UInt32(self, "flags", "Flags")
        yield PascalString32(self, "data", "Data", strip=" \0", charset="UTF-8")


class XcfLevel(FieldSet):

    def createFields(self):
        yield UInt32(self, "width", "Width in pixel")
        yield UInt32(self, "height", "Height in pixel")
        yield UInt32(self, "offset", "Offset")
        offset = self["offset"].value
        if offset == 0:
            return
        data_offsets = []
        while (self.absolute_address + self.current_size) // 8 < offset:
            if self._parent._parent._parent.version >= 11:
                chunk = UInt64(self, "data_offset[]", "Data offset")
            else:
                chunk = UInt32(self, "data_offset[]", "Data offset")
            yield chunk
            if chunk.value == 0:
                break
            data_offsets.append(chunk)
        if (self.absolute_address + self.current_size) // 8 != offset:
            raise ParserError("Problem with level offset.")
        previous = offset
        for chunk in data_offsets:
            data_offset = chunk.value
            size = data_offset - previous
            yield RawBytes(self, "data[]", size, "Data content of %s" % chunk.name)
            previous = data_offset


class XcfHierarchy(FieldSet):

    def createFields(self):
        yield UInt32(self, "width", "Width")
        yield UInt32(self, "height", "Height")
        yield UInt32(self, "bpp", "Bits/pixel")

        offsets = []
        while True:
            if self._parent._parent.version >= 11:
                chunk = UInt64(self, "offset[]", "Level offset")
            else:
                chunk = UInt32(self, "offset[]", "Level offset")
            yield chunk
            if chunk.value == 0:
                break
            offsets.append(chunk.value)
        for offset in offsets:
            padding = self.seekByte(offset, relative=False)
            if padding is not None:
                yield padding
            yield XcfLevel(self, "level[]", "Level")
#        yield XcfChannel(self, "channel[]", "Channel"))


class XcfChannel(FieldSet):

    def createFields(self):
        yield UInt32(self, "width", "Channel width")
        yield UInt32(self, "height", "Channel height")
        yield PascalString32(self, "name", "Channel name", strip="\0", charset="UTF-8")
        yield from readProperties(self)

        if self._parent.version >= 11:
            yield UInt64(self, "hierarchy_ofs", "Hierarchy offset")
        else:
            yield UInt32(self, "hierarchy_ofs", "Hierarchy offset")

        yield XcfHierarchy(self, "hierarchy", "Hierarchy")

    def createDescription(self):
        return 'Channel "%s"' % self["name"].value


class XcfLayer(FieldSet):

    def createFields(self):
        yield UInt32(self, "width", "Layer width in pixels")
        yield UInt32(self, "height", "Layer height in pixels")
        yield Enum(UInt32(self, "type", "Layer type"), XcfFile.IMAGE_TYPE_NAME)
        yield PascalString32(self, "name", "Layer name", strip="\0", charset="UTF-8")
        for prop in readProperties(self):
            yield prop

        if self._parent.version >= 11:
            yield UInt64(self, "hierarchy_ofs", "Hierarchy offset")
            yield UInt64(self, "mask_ofs", "Layer mask offset")
        else:
            # --
            # TODO: Hack for Gimp 1.2 files
            # --
            yield UInt32(self, "hierarchy_ofs", "Hierarchy offset")
            yield UInt32(self, "mask_ofs", "Layer mask offset")
        padding = self.seekByte(self["hierarchy_ofs"].value, relative=False)
        if padding is not None:
            yield padding
        yield XcfHierarchy(self, "hierarchy", "Hierarchy")
        # TODO: Read layer mask if needed: self["mask_ofs"].value != 0

    def createDescription(self):
        return 'Layer "%s"' % self["name"].value


class XcfParasites(FieldSet):

    def createFields(self):
        size = self["../size"].value * 8
        while self.current_size < size:
            yield XcfParasiteEntry(self, "parasite[]", "Parasite")


class XcfProperty(FieldSet):
    PROP_COMPRESSION = 17
    PROP_RESOLUTION = 19
    PROP_PARASITES = 21
    TYPE_NAME = {
        0: "End",
        1: "Colormap",
        2: "Active layer",
        3: "Active channel",
        4: "Selection",
        5: "Floating selection",
        6: "Opacity",
        7: "Mode",
        8: "Visible",
        9: "Linked",
        10: "Lock alpha",
        11: "Apply mask",
        12: "Edit mask",
        13: "Show mask",
        14: "Show masked",
        15: "Offsets",
        16: "Color",
        17: "Compression",
        18: "Guides",
        19: "Resolution",
        20: "Tattoo",
        21: "Parasites",
        22: "Unit",
        23: "Paths",
        24: "User unit",
        25: "Vectors",
        26: "Text layer flags",
        27: "Old Sample points",
        28: "Lock content",
        29: "Group item",
        30: "Item path",
        31: "Group item flags",
        32: "Lock position",
        33: "Float opacity",
        34: "Color tag",
        35: "Composite mode",
        36: "Composite space",
        37: "Blend space",
        38: "Float color",
        39: "Sample points",
        40: "Item set",
        41: "Item set item",
        42: "Lock visibility",
        43: "Selected path",
        44: "Filter region",
        45: "Filter argument",
        46: "Filter clip",
    }

    handler = {
        6: RGBA,
        7: LayerMode,
        8: GimpBoolean,
        9: GimpBoolean,
        10: GimpBoolean,
        11: GimpBoolean,
        12: GimpBoolean,
        13: GimpBoolean,
        15: LayerOffsets,
        17: XcfCompression,
        19: XcfResolution,
        20: XcfTattoo,
        21: XcfParasites,
        22: XcfUnit
    }

    def __init__(self, *args, **kw):
        FieldSet.__init__(self, *args, **kw)
        self._size = (8 + self["size"].value) * 8

    def createFields(self):
        yield Enum(UInt32(self, "type", "Property type"), self.TYPE_NAME)
        yield UInt32(self, "size", "Property size")

        size = self["size"].value
        if 0 < size:
            cls = self.handler.get(self["type"].value, None)
            if cls:
                yield cls(self, "data", size=size * 8)
            else:
                yield RawBytes(self, "data", size, "Data")

    def createDescription(self):
        return "Property: %s" % self["type"].display


def readProperties(parser):
    while True:
        prop = XcfProperty(parser, "property[]")
        yield prop
        if prop["type"].value == 0:
            return


class XcfFile(Parser):
    PARSER_TAGS = {
        "id": "xcf",
        "category": "image",
        "file_ext": ("xcf",),
        "mime": ("image/x-xcf", "application/x-gimp-image"),
        # header+empty property+layer offset+channel offset
        "min_size": (26 + 8 + 4 + 4) * 8,
        "magic": (
            (b'gimp xcf file\0', 0),
            (b'gimp xcf v002\0', 0),
        ),
        "description": "Gimp (XCF) picture"
    }
    endian = NETWORK_ENDIAN
    IMAGE_TYPE_NAME = {
        0: "RGB",
        1: "Gray",
        2: "Indexed"
    }

    # Doc : https://testing.developer.gimp.org/core/standards/xcf/#header
    # NOTE: XCF 3 or older's precision was always "8-bit gamma integer".

    # For XCF 4 (which was a development version, hence
    # this format should not be found often and may be
    # ignored by readers), its value may be one of:
    IMAGE_PRECISION_NAME_XCF4 = {
        0: "8-bit gamma integer",
        1: "16-bit gamma integer",
        2: "32-bit linear integer",
        3: "16-bit linear floating point",
        4: "32-bit linear floating point",
    }

    # For XCF 5 or 6 (which were development versions,
    # hence these formats may be ignored by readers),
    # its value may be one of:
    IMAGE_PRECISION_NAME_XCF5 = {
        100: "8-bit linear integer",
        150: "8-bit gamma integer",
        200: "16-bit linear integer",
        250: "16-bit gamma integer",
        300: "32-bit linear integer",
        350: "32-bit gamma integer",
        400: "16-bit linear floating point",
        450: "16-bit gamma floating point",
        500: "32-bit linear floating point",
        550: "32-bit gamma floating point"
    }

    IMAGE_PRECISION_NAME_XCF7 = {
        100: "8-bit linear integer",
        150: "8-bit gamma integer",
        200: "16-bit linear integer",
        250: "16-bit gamma integer",
        300: "32-bit linear integer",
        350: "32-bit gamma integer",
        500: "16-bit linear floating point",
        550: "16-bit gamma floating point",
        600: "32-bit linear floating point",
        650: "32-bit gamma floating point",
        700: "64-bit linear floating point",
        750: "64-bit gamma floating point",
    }

    version = 0

    def validate(self):
        if self.stream.readBytes(0, 9) != b'gimp xcf ':
            return "Wrong signature"
        return True

    def createFields(self):
        # Read signature
        signature = String(self, "signature", 14, "Gimp picture signature (ends with nul byte)", charset="ASCII")
        yield signature
        if signature.createValue() != 'gimp xcf file\0':
            self.version = int(str(signature)[11:-3])

        # Read image general informations (width, height, type)
        yield UInt32(self, "width", "Image width")
        yield UInt32(self, "height", "Image height")
        yield Enum(UInt32(self, "type", "Image type"), self.IMAGE_TYPE_NAME)
        if self.version == 4:
            yield Enum(UInt32(self, "precision", "Image precision"), self.IMAGE_PRECISION_NAME_XCF4)
        elif self.version in [5, 6]:
            yield Enum(UInt32(self, "precision", "Image precision"), self.IMAGE_PRECISION_NAME_XCF5)
        elif self.version >= 7:
            yield Enum(UInt32(self, "precision", "Image precision"), self.IMAGE_PRECISION_NAME_XCF7)
        for prop in readProperties(self):
            yield prop

        # Read layer offsets
        layer_offsets = []
        while True:
            if self.version >= 11:
                chunk = UInt64(self, "layer_offset[]", "Layer offset")
            else:
                chunk = UInt32(self, "layer_offset[]", "Layer offset")
            yield chunk
            if chunk.value == 0:
                break
            layer_offsets.append(chunk.value)

        # Read channel offsets
        channel_offsets = []
        while True:
            if self.version >= 11:
                chunk = UInt64(self, "channel_offset[]", "Channel offset")
            else:
                chunk = UInt32(self, "channel_offset[]", "Channel offset")
            yield chunk
            if chunk.value == 0:
                break
            channel_offsets.append(chunk.value)

        # Read layers
        for index, offset in enumerate(layer_offsets):
            if index + 1 < len(layer_offsets):
                size = (layer_offsets[index + 1] - offset) * 8
            else:
                size = None
            padding = self.seekByte(offset, relative=False)
            if padding:
                yield padding
            yield XcfLayer(self, "layer[]", size=size)

        # Read channels
        for index, offset in enumerate(channel_offsets):
            if index + 1 < len(channel_offsets):
                size = (channel_offsets[index + 1] - offset) * 8
            else:
                size = None
            padding = self.seekByte(offset, relative=False)
            if padding is not None:
                yield padding
            yield XcfChannel(self, "channel[]", "Channel", size=size)
