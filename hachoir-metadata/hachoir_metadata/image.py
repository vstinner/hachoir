from hachoir_metadata.metadata import (Metadata, MultipleMetadata,
    registerExtractor)
from hachoir_parser.image import (
    BmpFile, IcoFile, PcxFile, GifFile, PngFile, TiffFile,
    XcfFile, TargaFile, WMF_File, PsdFile)
from hachoir_parser.image.png import getBitsPerPixel as pngBitsPerPixel
from hachoir_parser.image.xcf import XcfProperty
from hachoir_core.i18n import _
from hachoir_core.error import HACHOIR_ERRORS

def computeComprRate(meta, compr_size):
    """
    Compute image compression rate. Skip size of color palette, focus on
    image pixels. Original size is width x height x bpp. Compressed size
    is an argument (in bits).

    Set "compr_data" with a string like "1.52x".
    """
    if not hasattr(meta, "width") \
    or not hasattr(meta, "height") \
    or not hasattr(meta, "bits_per_pixel"):
        return
    orig_size = meta.width[0] * meta.height[0] * meta.bits_per_pixel[0]
    meta.compr_rate = "%.3gx" % (float(orig_size) / compr_size)

class BmpMetadata(Metadata):
    def extract(self, image):
        if "header" not in image:
            return
        hdr = image["header"]
        self.width = hdr["width"].value
        self.height = hdr["height"].value
        bpp = hdr["bpp"].value
        if bpp:
            if bpp <= 8 and "used_colors" in hdr:
                self.nb_colors = hdr["used_colors"].value
            self.bits_per_pixel = bpp
        self.compression = hdr["compression"].display
        self.format_version = "Microsoft Bitmap version %s" % hdr.getFormatVersion()
        computeComprRate(self, image["pixels"].size)

class TiffMetadata(Metadata):
    key_to_attr = {
        "img_width": "width",
        "img_height": "width",

        # TODO: Enable that (need link to value)
#        "description": "comment",
#        "doc_name": "title",
#        "orientation": "image_orientation",
    }
    def extract(self, tiff):
        for field in tiff["ifd"]:
            key = field.name
            try:
                attrname = self.key_to_attr[field.name]
            except KeyError:
                continue
            if "value" not in field:
                continue
            value = field["value"].value
            setattr(self, attrname, value)

class IcoMetadata(MultipleMetadata):
    color_to_bpp = {
        2: 1,
        16: 4,
        256: 8
    }

    def extract(self, icon):
        for index, header in enumerate(icon.array("icon_header")):
            image = Metadata()

            # Read size and colors from header
            image.width = header["width"].value
            image.height = header["height"].value
            bpp = header["bpp"].value
            nb_colors = header["nb_color"].value
            if nb_colors != 0:
                image.nb_colors = nb_colors
                if bpp == 0 and nb_colors in self.color_to_bpp:
                    bpp = self.color_to_bpp[nb_colors]
            elif bpp == 0:
                bpp = 8
            image.bits_per_pixel = bpp
            image.setHeader(_("Icon #%u (%ux%u)")
                % (1+index, image.get("width"), image.get("height")))

            # Read compression from data (if available)
            key = "icon_data[%u]/header/codec" % index
            if key in icon:
                image.compression = icon[key].display
            key = "icon_data[%u]/pixels" % index
            if key in icon:
                computeComprRate(image, icon[key].size)

            # Store new image
            self.addGroup("image[%u]" % index, image)

class PcxMetadata(Metadata):
    def extract(self, pcx):
        self.width = 1 + pcx["xmax"].value
        self.height = 1 + pcx["ymax"].value
        self.bits_per_pixel = pcx["bpp"].value
        if 1 <= pcx["bpp"].value <= 8:
            self.nb_colors = 2 ** pcx["bpp"].value
        self.compression = _("Run-length encoding (RLE)")
        self.format_version = "PCX: %s" % pcx["version"].display
        computeComprRate(self, pcx["image_data"].size)

class XcfMetadata(Metadata):
    # Map image type to bits/pixel
    type_to_bpp = {
        0: 24,
        1: 8,
        2: 8
    }

    def processProperty(self, prop):
        type = prop["type"].value
        if type == XcfProperty.PROP_PARASITES:
            for field in prop["data"]:
                if field["name"].value == "gimp-comment":
                    self.comment = field["data"].value
        elif type == XcfProperty.PROP_COMPRESSION:
            self.compression = prop["data/compression"].display

    def readProperties(self, xcf):
        for prop in xcf.array("property"):
            self.processProperty(prop)

    def extract(self, xcf):
        self.width = xcf["width"].value
        self.height = xcf["height"].value
        try:
            self.bits_per_pixel = self.type_to_bpp[ xcf["type"].value ]
        except KeyError:
            pass
        self.format_version = xcf["type"].display
        self.readProperties(xcf)

class PngMetadata(Metadata):
    def extract(self, png):
        header = png["/header"]
        self.width = header["width"].value
        self.height = header["height"].value

        # Read number of colors and pixel format
        if header["has_palette"].value:
            nb_colors = png["/palette/size"].value // 3
        else:
            nb_colors = None
        if not header["has_palette"].value:
            if header["has_alpha"].value:
                self.pixel_format = _("RGBA")
            else:
                self.pixel_format = _("RGB")
        elif "transparency" in png:
            self.pixel_format = _("Color index with transparency")
            nb_colors -= 1
        else:
            self.pixel_format = _("Color index")
        self.bits_per_pixel = pngBitsPerPixel(header)
        if nb_colors:
            self.nb_colors = nb_colors

        # Read compression, timestamp, etc.
        self.compression = header["compression"].display
        if "time" in png:
            try:
                self.creation_date = png["time"].value
            except HACHOIR_ERRORS:
                pass
        for comment in png.array("text"):
            if "text" not in comment:
                continue
            keyword = comment["keyword"].value
            text = comment["text"].display
            if keyword.lower() != "comment":
                self.comment = "%s=%s" % (keyword, text)
            else:
                self.comment = text
        compr_size = sum( data.size for data in png.array("data") )
        computeComprRate(self, compr_size)

class GifMetadata(Metadata):
    def extract(self, gif):
        header = gif["/screen"]
        self.width = header["width"].value
        self.height = header["height"].value
        self.bits_per_pixel = (1 + header["bpp"].value)
        self.nb_colors = (1 << self.bits_per_pixel[0])
        self.compression = _("LZW")
        self.format_version =  "GIF version %s" % gif["header"].value[-3:]
        if "comments" in gif:
            for comment in gif.array("comments/comment"):
                self.comment = comment.value
        if "graphic_ctl/has_transp" in gif and gif["graphic_ctl/has_transp"].value:
            self.pixel_format = _("Color index with transparency")
        else:
            self.pixel_format = _("Color index")

class TargaMetadata(Metadata):
    def extract(self, tga):
        self.width = tga["width"].value
        self.height = tga["height"].value
        self.bits_per_pixel = tga["bpp"].value
        if tga["nb_color"].value:
            self.nb_colors = tga["nb_color"].value
        self.compression = tga["codec"].display
        computeComprRate(self, tga["pixels"].size)

class WmfMetadata(Metadata):
    def extract(self, wmf):
        if wmf.isAPM():
            if "amf_header/rect" in wmf:
                rect = wmf["amf_header/rect"]
                self.width = (rect["right"].value - rect["left"].value)
                self.height = (rect["bottom"].value - rect["top"].value)
            self.bits_per_pixel = 24
        elif wmf.isEMF():
            emf = wmf["emf_header"]
            if "description" in emf:
                desc = emf["description"].value
                if "\0" in desc:
                    self.producer, self.title = desc.split("\0", 1)
                else:
                    self.producer = desc
            if emf["nb_colors"].value:
                self.nb_colors = emf["nb_colors"].value
                self.bits_per_pixel = 8
            else:
                self.bits_per_pixel = 24
            self.width = emf["width_px"].value
            self.height = emf["height_px"].value

class PsdMetadata(Metadata):
    def extract(self, psd):
        self.width = psd["width"].value
        self.height = psd["height"].value
        self.bits_per_pixel = psd["depth"].value * psd["nb_channels"].value
        self.pixel_format = psd["color_mode"].display
        self.compression = psd["compression"].display

registerExtractor(IcoFile, IcoMetadata)
registerExtractor(GifFile, GifMetadata)
registerExtractor(XcfFile, XcfMetadata)
registerExtractor(TargaFile, TargaMetadata)
registerExtractor(PcxFile, PcxMetadata)
registerExtractor(BmpFile, BmpMetadata)
registerExtractor(PngFile, PngMetadata)
registerExtractor(TiffFile, TiffMetadata)
registerExtractor(WMF_File, WmfMetadata)
registerExtractor(PsdFile, PsdMetadata)

