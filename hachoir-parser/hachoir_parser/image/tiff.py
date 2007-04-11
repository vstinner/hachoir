"""
TIFF image parser.

Author: Victor Stinner
Creation date: 30 september 2006
"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    UInt16, UInt32, String)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN
from hachoir_parser.image.exif import BasicIFDEntry
from hachoir_core.tools import createDict

MAX_COUNT = 250

class IFDEntry(BasicIFDEntry):
    static_size = 12*8

    TAG_INFO = {
        254: ("new_subfile_type", "New subfile type"),
        256: ("img_width", "Image width in pixels"),
        257: ("img_height", "Image height in pixels"),
        258: ("bits_per_sample", "Bits per sample"),
        259: ("compression", "Compression method"),
        262: ("photo_interpret", "Photometric interpretation"),
        263: ("thres", "Threshholding"),
        264: ("cell_width", "Cellule width"),
        265: ("cell_height", "Cellule height"),
        266: ("fill_order", "Fill order"),
        269: ("doc_name", "Document name"),
        270: ("description", "Image description"),
        271: ("make", "Make"),
        272: ("model", "Model"),
        273: ("strip_ofs", "Strip offsets"),
        274: ("orientation", "Orientation"),
        277: ("sample_pixel", "Samples per pixel"),
        278: ("row_per_strip", "Rows per strip"),
        279: ("strip_byte", "Strip byte counts"),
        280: ("min_sample_value", "Min sample value"),
        281: ("max_sample_value", "Max sample value"),
        282: ("xres", "X resolution"),
        283: ("yres", "Y resolution"),
        284: ("planar_conf", "Planar configuration"),
        285: ("page_name", "Page name"),
        286: ("xpos", "X position"),
        287: ("ypos", "Y position"),
        288: ("free_ofs", "Free offsets"),
        289: ("free_byte", "Free byte counts"),
        290: ("gray_resp_unit", "Gray response unit"),
        291: ("gray_resp_curve", "Gray response curve"),
        292: ("group3_opt", "Group 3 options"),
        293: ("group4_opt", "Group 4 options"),
        296: ("res_unit", "Resolution unit"),
        297: ("page_nb", "Page number"),
        301: ("color_respt_curve", "Color response curves"),
        305: ("software", "Software"),
        306: ("date_time", "Date time"),
        307: ("artist", "Artist"),
        308: ("host_computer", "Host computer"),
        317: ("predicator", "Predicator"),
        318: ("white_pt", "White point"),
        319: ("prim_chomat", "Primary chromaticities"),
        320: ("color_map", "Color map"),
    }
    TAG_NAME = createDict(TAG_INFO, 0)

    def __init__(self, *args):
        FieldSet.__init__(self, *args)
        tag = self["tag"].value
        if tag in self.TAG_INFO:
            self._name, self._description = self.TAG_INFO[tag]
        else:
            self._parser = None

class IFD(FieldSet):
    def __init__(self, *args):
        FieldSet.__init__(self, *args)
        self._size = 16 + self["count"].value * IFDEntry.static_size

    def createFields(self):
        yield UInt16(self, "count")
        if MAX_COUNT < self["count"].value:
            raise ParserError("TIFF IFD: Invalid count (%s)"
                % self["count"].value)
        for index in xrange(self["count"].value):
            yield IFDEntry(self, "entry[]")

class TiffFile(Parser):
    tags = {
        "id": "tiff",
        "category": "image",
        "file_ext": ("tif", "tiff"),
        "mime": ("image/tiff",),
        "min_size": 8*8,
# TODO: Re-enable magic
#        "magic": (("II\x2A\0", 0), ("MM\0\x2A", 0)),
        "description": "TIFF picture"
    }

    # Correct endian is set in constructor
    endian = LITTLE_ENDIAN
#    endian = BIG_ENDIAN

    def validate(self):
        endian = self.stream.readBytes(0, 2)
        if endian == "II":
            self.endian = LITTLE_ENDIAN
        elif endian == "MM":
            self.endian = BIG_ENDIAN
        else:
            return "Invalid endian"
        if self["version"].value != 42:
            return "Unknown TIFF version"
        if self["img_dir_ofs"].value % 2:
            return "Invalid first image directory offset"
        return True

    def createFields(self):
        yield String(self, "endian", 2, 'Endian ("II" or "MM")', charset="ASCII")
        yield UInt16(self, "version", "TIFF version number")
        yield UInt32(self, "img_dir_ofs", "First image directory offset (in bytes from the beginning)")

        raw = self.seekByte(self["img_dir_ofs"].value, relative=False)
        if raw:
            yield raw

        yield IFD(self, "ifd")

        if self.current_size < self._size:
            yield self.seekBit(self._size, "end")

