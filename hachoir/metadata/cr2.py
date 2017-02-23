from hachoir.metadata.metadata import (registerExtractor, Metadata,
                                       RootMetadata, MultipleMetadata)
from hachoir.parser.image import CR2File
from hachoir.parser.image.png import getBitsPerPixel as pngBitsPerPixel
from hachoir.parser.image.xcf import XcfProperty
from hachoir.metadata.safe import fault_tolerant

class CR2Metadata(RootMetadata):
    key_to_attr = {
        "ImageWidth": "width",
        "ImageLength": "height",
        "ImageDescription": "comment",
        "DocumentName": "title",
        "XResolution": "width_dpi",
        "YResolution": "height_dpi",
        "DateTime": "creation_date"
    }

    def extract(self, tiff):
        if "ifd[0]" in tiff:
            self.useIFD(tiff["ifd[0]"])
        if "exif[0]" in tiff:
            self.date_time_original = tiff["exif[0]"]["value[7]"].value
            self.date_time_digitized = tiff["exif[0]"]["value[8]"].value

    def useIFD(self, ifd):
        attr = {}
        for entry in ifd.array("entry"):
            self.processIfdEntry(ifd, entry, attr)
        if 'BitsPerSample' in attr and 'SamplesPerPixel' in attr:
            self.bits_per_pixel = attr[
                'BitsPerSample'] * attr['SamplesPerPixel']

    @fault_tolerant
    def processIfdEntry(self, ifd, entry, attr):
        tag = entry["tag"].display
        if tag in {"BitsPerSample", "SamplesPerPixel"}:
            value = ifd.getEntryValues(entry)[0].value
            attr[tag] = value
            return

        try:
            attrname = self.key_to_attr[tag]
        except KeyError:
            return
        value = ifd.getEntryValues(entry)[0].value
        if tag in {"XResolution", "YResolution"}:
            value = round(value)
        setattr(self, attrname, value)

registerExtractor(CR2File, CR2Metadata)
