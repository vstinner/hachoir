from hachoir_metadata.metadata import Metadata, registerExtractor
from hachoir_parser.image.exif import ExifEntry
from hachoir_parser.image.jpeg import (JpegFile,
    QUALITY_HASH_COLOR, QUALITY_SUM_COLOR,
    QUALITY_HASH_GRAY, QUALITY_SUM_GRAY)
from hachoir_core.field import MissingField
from hachoir_core.i18n import _
from hachoir_core.error import warning
import types

class JpegMetadata(Metadata):
    exif_key = {
        # Exif metadatas
        ExifEntry.TAG_CAMERA_MANUFACTURER: "camera_manufacturer",
        ExifEntry.TAG_CAMERA_MODEL: "camera_model",
        ExifEntry.TAG_ORIENTATION: "image_orientation",
        ExifEntry.TAG_EXPOSURE: "camera_exposure",
        ExifEntry.TAG_FOCAL: "camera_focal",
        ExifEntry.TAG_BRIGHTNESS: "camera_brightness",
        ExifEntry.TAG_APERTURE: "camera_aperture",

        # Generic metadatas
        ExifEntry.TAG_IMG_TITLE: "title",
        ExifEntry.TAG_SOFTWARE: "producer",
        ExifEntry.TAG_FILE_TIMESTAMP: "creation_date",
        ExifEntry.TAG_WIDTH: "width",
        ExifEntry.TAG_HEIGHT: "height",
    }

    iptc_key = {
         80: "author",
        101: "country",
        116: "copyright",
        120: "title",
        231: "comment",
    }

    orientation_name = {
        1: _('Horizontal (normal)'),
        2: _('Mirrored horizontal'),
        3: _('Rotated 180'),
        4: _('Mirrored vertical'),
        5: _('Mirrored horizontal then rotated 90 counter-clock-wise'),
        6: _('Rotated 90 clock-wise'),
        7: _('Mirrored horizontal then rotated 90 clock-wise'),
        8: _('Rotated 90 counter clock-wise'),
    }

    def extract(self, jpeg):
        if "sof/content" in jpeg:
            sof = jpeg["sof/content"]
            self.width = sof["width"].value
            self.height = sof["height"].value
            nb_components = sof["nr_components"].value
            self.bits_per_pixel = 8 * nb_components
            if nb_components == 3:
                self.pixel_format = _("YCbCr")
            else:
                self.pixel_format = _("Grayscale")
                self.nb_colors = 256
        self.compression = "JPEG"
        if "app0/content" in jpeg:
            app0 = jpeg["app0/content"]
            self.format_version = "JFIF %u.%02u" \
                % (app0["ver_maj"].value, app0["ver_min"].value)

        if "exif/content" in jpeg:
            for ifd in jpeg.array("exif/content/ifd"):
                for entry in ifd.array("entry"):
                    self.processIfdEntry(ifd, entry)
        if "psd/content" in jpeg:
            psd = jpeg["psd/content"]
            if "iptc" in psd:
                self.parseIPTC(psd["iptc/content"])
        for comment in jpeg.array("comment"):
            self.comment = comment["data"].value
        self.computeQuality(jpeg)

    def computeQuality(self, jpeg):
        # This function is an adaption to Python of ImageMagick code
        # to compute JPEG quality using quantization tables

        # Read quantization tables
        qtlist = []
        for dqt in jpeg.array("dqt"):
            for qt in dqt.array("content/qt"):
                # TODO: Take care of qt["index"].value?
                qtlist.append(qt)
        if not qtlist:
            return

        # Compute sum of all coefficients
        sumcoeff = 0
        for qt in qtlist:
           coeff = qt.array("coeff")
           for index in xrange(64):
                sumcoeff += coeff[index].value

        # Choose the right quality table and compute hash value
        try:
            hashval= qtlist[0]["coeff[2]"].value +  qtlist[0]["coeff[53]"].value
            if 2 <= len(qtlist):
                hashval += qtlist[1]["coeff[0]"].value + qtlist[1]["coeff[63]"].value
                hashtable = QUALITY_HASH_COLOR
                sumtable = QUALITY_SUM_COLOR
            else:
                hashtable = QUALITY_HASH_GRAY
                sumtable = QUALITY_SUM_GRAY
        except (MissingField, IndexError):
            # A coefficient is missing, so don't compute JPEG quality
            return

        # Find the JPEG quality
        for index in xrange(100):
            if (hashval >= hashtable[index]) or (sumcoeff >= sumtable[index]):
                quality = "%s%%" % (index + 1)
                if (hashval > hashtable[index]) or (sumcoeff > sumtable[index]):
                    quality += " " + _("(approximate)")
                self.comment = "JPEG quality: %s" % quality
                return

    def processIfdEntry(self, ifd, entry):
        # Skip unknown tags
        tag = entry["tag"].value
        if tag not in self.exif_key:
            return
        key = self.exif_key[tag]
        if key in ("width", "height") and hasattr(self, key):
            # EXIF "valid size" are sometimes not updated when the image is scaled
            # so we just ignore it
            return

        # Read value
        rational = False
        if "value" in entry:
            value = entry["value"].value
        elif entry["type"].value in (ExifEntry.TYPE_RATIONAL, ExifEntry.TYPE_SIGNED_RATIONAL):
            denominator = ifd[ "value_%s[1]" % entry.name ].value
            if not denominator:
                return
            value  = float(ifd[ "value_%s[0]" % entry.name ].value)
            value /= denominator
            rational = True
        else:
            value = ifd["value_%s" % entry.name].value

        # Convert value to string
        if tag == ExifEntry.TAG_ORIENTATION:
            value = self.orientation_name.get(value, value)
        elif tag == ExifEntry.TAG_EXPOSURE:
            if not value:
                return
            value = "1/%g" % (1/value)
        elif rational:
            value = "%.3g" % value

        # Store information
        setattr(self, key, value)

    def parseIPTC(self, iptc):
        for field in iptc:
            # Skip incomplete field
            if "tag" not in field or "content" not in field:
                continue

            # Get value
            value = field["content"].value
            if isinstance(value, types.StringTypes):
                value = value.replace("\r", " ")
                value = value.replace("\n", " ")

            # Skip unknown tag
            tag = field["tag"].value
            if tag not in self.iptc_key:
                if tag != 0:
                    warning("Skip IPTC key %s: %s" % (tag, value))
                continue
            setattr(self, self.iptc_key[tag], value)

registerExtractor(JpegFile, JpegMetadata)

