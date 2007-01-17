# -*- coding: utf-8 -*-

from hachoir_core.compatibility import sorted
from hachoir_core.endian import endian_name
from hachoir_core.tools import (
    humanDuration, makePrintable, humanBitRate,
    humanFrequency, humanBitSize)
from hachoir_core.dict import Dict
from hachoir_core.i18n import _
from hachoir_core.error import warning
from datetime import datetime
from hachoir_metadata.filter import Filter, NumberFilter

MAX_STR_LENGTH = 80*10
MAX_SAMPLE_RATE = 192000
MAX_DURATION = 366*24*60*60*1000
MAX_NB_CHANNEL = 16
MAX_WIDTH = 200000
MAX_HEIGHT = MAX_WIDTH
MAX_NB_COLOR = 2 ** 24
MAX_BITS_PER_PIXEL = 64
MIN_YEAR = 1900
MAX_YEAR = 2030
MAX_FRAME_RATE = 150
DATETIME_FILTER = Filter(datetime, datetime(MIN_YEAR, 1, 1), datetime(MAX_YEAR, 12, 31))

extractors = {}

class Data:
    def __init__(self, key, priority, description,  handler=None, filter=None):
        """
        handler is only used if value is not string nor unicode, prototype:
           def handler(value) -> str/unicode
        """
        assert Metadata.MIN_PRIORITY <= priority <= Metadata.MAX_PRIORITY
        assert isinstance(description, unicode)
        self.key = key
        self.description = description
        self.values = []
        self.handler = handler
        self.filter = filter
        self.priority = priority

    def __contains__(self, value):
        return value in self.values

    def __cmp__(self, other):
        return cmp(self.priority, other.priority)

class Metadata(object):
    MIN_PRIORITY = 100
    MAX_PRIORITY = 999
    header = u"Metadata"

    def __init__(self):
        assert isinstance(self.header, unicode)

        object.__init__(self)
        object.__setattr__(self, "_Metadata__data", {})
        header = self.__class__.header
        object.__setattr__(self, "_Metadata__header", header)

        self.register("title", 100, _("Title"))
        self.register("author", 101, _("Author"))
        self.register("music_composer", 102, _("Music composer"))

        self.register("album", 200, _("Album"))
        self.register("duration", 201, _("Duration"), # integer in milliseconde
            handler=humanDuration, filter=NumberFilter(1, MAX_DURATION))
        self.register("music_genre", 202, _("Music genre"))
        self.register("language", 203, _("Language"))
        self.register("track_number", 204, _("Track number"),
            filter=NumberFilter(1, 99))
        self.register("organization", 205, _("Organization"))

        self.register("nb_channel", 300, _("Channel"),
            handler=humanAudioChannel, filter=NumberFilter(1, MAX_NB_CHANNEL))
        self.register("sample_rate", 301, _("Sample rate"),
            handler=humanFrequency, filter=NumberFilter(1, MAX_SAMPLE_RATE))
        self.register("bits_per_sample", 302, _("Bits/sample"),
            handler=humanBitSize, filter=NumberFilter(1, 64))
        self.register("artist", 303, _("Artist"))
        self.register("width", 304, _("Image width"),
            filter=NumberFilter(1, MAX_WIDTH))
        self.register("height", 305, _("Image height"),
            filter=NumberFilter(1, MAX_HEIGHT))
        self.register("image_orientation", 306, _("Image orientation"))
        self.register("nb_colors", 315, _("Number of colors"),
            filter=NumberFilter(1, MAX_NB_COLOR))
        self.register("bits_per_pixel", 316, _("Bits/pixel"),
            filter=NumberFilter(1, MAX_BITS_PER_PIXEL))
        self.register("pixel_format", 317, _("Pixel format"))

        self.register("subtitle_author", 400, _("Subtitle author"))

        self.register("creation_date", 500, _("Creation date"),
            filter=DATETIME_FILTER)
        self.register("last_modification", 501, _("Last modification"),
            filter=DATETIME_FILTER)
        self.register("country", 502, _("Country"))

        self.register("camera_aperture", 520, _("Camera aperture"))
        self.register("camera_focal", 521, _("Camera focal"))
        self.register("camera_exposure", 522, _("Camera exposure"))
        self.register("camera_brightness", 530, _("Camera brightness"))
        self.register("camera_model", 531, _("Camera model"))
        self.register("camera_manufacturer", 532, _("Camera manufacturer"))

        self.register("compression", 600, _("Compression"))
        self.register("copyright", 601, _("Copyright"))
        self.register("url", 602, _("URL"))
        self.register("frame_rate", 603, _("Frame rate"),
            filter=NumberFilter(1, MAX_FRAME_RATE))
        self.register("bit_rate", 604, _("Bit rate"), handler=humanBitRate)
        self.register("aspect_ratio", 604, _("Aspect ratio"))

        self.register("producer", 901, _("Producer"))
        self.register("comment", 902, _("Comment"))
        self.register("format_version", 950, _("Format version"))
        self.register("mime_type", 951, _("MIME type"))
        self.register("endian", 952, _("Endian"))

    def __setattr__(self, key, value):
        """
        Add a new value to data with name 'key'. Skip duplicates.
        """
        # Invalid key?
        if key not in self.__data:
            raise KeyError(_("%s has no metadata '%s'") % (self.__class__.__name__, key))

        # Convert string to Unicode string using charset ISO-8859-1
        if isinstance(value, str):
            value = unicode(value, "ISO-8859-1")

        # Skip empty strings
        if isinstance(value, unicode):
            value = value.strip(" \t\v\n\r\0")
            if not value:
                return
            if MAX_STR_LENGTH < len(value):
                value = value[:MAX_STR_LENGTH] + "(...)"

        # Skip duplicates
        data = self.__data[key]
        if value in data:
            return

        # Use filter
        if data.filter and not data.filter(value):
            warning("Skip value %s=%r (filter)" % (key, value))
            return

        # For string, if you have "verlongtext" and "verylo",
        # keep the longer value
        if isinstance(value, unicode):
            for index, item in enumerate(data.values):
                if isinstance(item, unicode):
                    if value.startswith(item):
                        # Find longer value, replace the old one
                        data.values[index] = value
                        return
                    if item.startswith(value):
                        # Find truncated value, skip it
                        return

        # Add new value
        data.values.append(value)

    def setHeader(self, text):
        object.__setattr__(self, "header", text)

    def __getattr__(self, key):
        """
        Read values of tag with name 'key'.

        >>> a = Metadata()
        >>> a.author = "haypo"
        >>> a.author = "julien"
        >>> a.author
        ['haypo', 'julien']
        >>> a.duration = 2300
        >>> a.duration
        [2300]
        """
        if key not in self.__data:
            raise AttributeError(_("%s has no attribute '%s'")
                % (self.__class__.__name__, key))
        data = self.__data[key]
        if data.values:
            return data.values
        else:
            raise AttributeError(_("Attribute '%s' of %s is not set")
                % (key, self.__class__.__name__))

    def get(self, name, glue=", ", charset="ISO-8859-1"):
        r"""
        Get an attribute as Unicode string. If the attribute doesn't exist,
        empty string is returned. If the attribute has multiple value, they
        will be joined with glue (optional argument, default value is ", ").
        Basic string are converted to Unicode using charset (optional
        argumet, default value is ISO-8859-1).

        >>> a = Metadata()
        >>> a.author = "haypo"
        >>> a.author = "julien"
        >>> a.get("author")
        u'haypo, julien'
        >>> a.get("author", glue=" and ")
        u'haypo and julien'
        >>> a.get("title")
        u''
        """
        try:
            value = getattr(self, name)
            if isinstance(value, list):
                return glue.join( unicode(item) for item in value )
            elif isinstance(value, str):
                return makePrintable("ISO-8859-1", to_unicode=True)
            else:
                return value
        except AttributeError:
            return u''


    def register(self, key, priority, title, handler=None, filter=None):
        assert key not in self.__data
        self.__data[key] = Data(key, priority, title, handler, filter)

    def __iter__(self):
        return self.__data.itervalues()

    def __str__(self):
        r"""
        Create a multi-line ASCII string (end of line is "\n") which
        represents all datas.

        >>> a = Metadata()
        >>> a.author = "haypo"
        >>> a.copyright = unicode("© Hachoir", "UTF-8")
        >>> print a
        Metadata:
        - Author: haypo
        - Copyright: \xa9 Hachoir

        @see __unicode__() and exportPlaintext()
        """
        text = self.exportPlaintext()
        return "\n".join( makePrintable(line, "ASCII") for line in text )

    def __unicode__(self):
        r"""
        Create a multi-line Unicode string (end of line is "\n") which
        represents all datas.

        >>> a = Metadata()
        >>> a.copyright = unicode("© Hachoir", "UTF-8")
        >>> print repr(unicode(a))
        u'Metadata:\n- Copyright: \xa9 Hachoir'

        @see __str__() and exportPlaintext()
        """

        return "\n".join(self.exportPlaintext())

    def exportPlaintext(self, priority=None, human=True, line_prefix=u"- "):
        r"""
        Convert metadata to multi-line Unicode string and skip datas
        with priority lower than specified priority.

        Default priority is Metadata.MAX_PRIORITY. If human flag is True, data
        key are translated to better human name (eg. "bit_rate" becomes
        "Bit rate") which may be translated using gettext.

        If priority is too small, metadata are empty and so None is returned.

        >>> print Metadata().exportPlaintext()
        None
        >>> meta = Metadata()
        >>> meta.copyright = unicode("© Hachoir", "UTF-8")
        >>> print repr(meta.exportPlaintext())
        [u'Metadata:', u'- Copyright: \xa9 Hachoir']

        @see __str__() and __unicode__()
        """
        if priority is not None:
            priority = max(priority, self.MIN_PRIORITY)
            priority = min(priority, self.MAX_PRIORITY)
        else:
            priority = self.MAX_PRIORITY
        text = ["%s:" % self.header]
        for data in sorted(self):
            if priority < data.priority:
                break
            if not data.values:
                continue
            if human:
                title = data.description
            else:
                title = data.key
            for value in data.values:
                if data.handler and not isinstance(value, (str, unicode)):
                    value = data.handler(value)
                if isinstance(value, str):
                    value = makePrintable(value, "ISO-8859-1", to_unicode=True)
                text.append("%s%s: %s" % (line_prefix, title, value))
        if 1 < len(text):
            return text
        else:
            return None

class MultipleMetadata(Metadata):
    header = _("Common")
    def __init__(self):
        Metadata.__init__(self)
        object.__setattr__(self, "_MultipleMetadata__groups", Dict())
        object.__setattr__(self, "_MultipleMetadata__key_counter", {})

    def __contains__(self, key):
        return key in self.__groups

    def __getitem__(self, key):
        return self.__groups[key]

    def addGroup(self, key, metadata, header=None):
        if key.endswith("[]"):
            key = key[:-2]
            if key in self.__key_counter:
                self.__key_counter[key] += 1
            else:
                self.__key_counter[key] = 1
            key += "[%u]" % self.__key_counter[key]
        if header:
            metadata.setHeader(header)
        self.__groups.append(key, metadata)

    def exportPlaintext(self, priority=None, human=True):
        common = Metadata.exportPlaintext(self, priority, human)
        if common:
            text = common
        else:
            text = []
        for metadata in self.__groups:
            value = metadata.exportPlaintext(priority, human)
            if value:
                text.extend(value)
        if len(text):
            return text
        else:
            return None

def registerExtractor(parser, extractor):
    assert parser not in extractors
    extractors[parser] = extractor

def extractMetadata(parser):
    """
    Create a Metadata class from a parser. Returns None if no metadata
    extractor does exist for the parser class.
    """
    try:
        extractor = extractors[parser.__class__]
    except KeyError:
        return None
    metadata = extractor()
    metadata.extract(parser)
    metadata.mime_type = parser.mime_type
    metadata.endian = endian_name[parser.endian]
    return metadata

### Handler to give data a better human representation ####################

nb_channel_name = {
    1: _("mono"),
    2: _("stereo")
}
def humanAudioChannel(value):
    return nb_channel_name.get(value, unicode(value))

