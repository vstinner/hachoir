"""
FLAC (audio) parser

Documentation:

 * http://flac.sourceforge.net/format.html#metadata_block_data

Author: Esteban Loiseau <baal AT tuxfamily.org>
Creation date: 2008-04-09
"""

from hachoir_parser import Parser
from hachoir_core.field import FieldSet, String, Bit, Bits, UInt24, RawBytes, Enum, NullBytes
from hachoir_core.stream import BIG_ENDIAN, LITTLE_ENDIAN
from hachoir_core.tools import createDict
from hachoir_parser.container.ogg import parseVorbisComment

class VorbisComment(FieldSet):
    endian = LITTLE_ENDIAN
    createFields = parseVorbisComment

class MetadataBlock(FieldSet):
    "Metadata block field: http://flac.sourceforge.net/format.html#metadata_block"

    BLOCK_TYPES = {
        0: ("stream_info[]", u"Stream info", None),
        1: ("padding[]", u"Padding", None),
        2: ("application[]", u"Application", None),
        3: ("seek_table", u"Seek table", None),
        4: ("comment[]", u"Vorbis comment", VorbisComment),
        5: ("cue_sheet[]", u"Cue sheet", None),
        6: ("picture[]", u"Picture", None),
    }
    BLOCK_TYPE_DESC = createDict(BLOCK_TYPES, 1)

    def __init__(self, *args, **kw):
        FieldSet.__init__(self, *args, **kw)
        self._size = 32 + self["metadata_length"].value * 8
        try:
            key = self["block_type"].value
            self._name, self._description, self.handler = self.BLOCK_TYPES[key]
        except KeyError:
            self.handler = None

    def createFields(self):
        yield Bit(self, "last_metadata_block", "True if this is the last metadata block")
        yield Enum(Bits(self, "block_type", 7, "Metadata block header type"), self.BLOCK_TYPE_DESC)
        yield UInt24(self, "metadata_length", "Length of following metadata in bytes (doesn't include this header)")

        block_type = self["block_type"].value
        size = self["metadata_length"].value
        if not size:
            return
        try:
            name = self.BLOCK_TYPES[block_type][0]
            handler = self.BLOCK_TYPES[block_type][2]
        except KeyError:
            handler = None
        if handler:
            yield handler(self, name, size=size*8)
        elif self["block_type"].value == 1:
            yield NullBytes(self, "padding", size)
        else:
            yield RawBytes(self, "rawdata", size)

class Metadata(FieldSet):
    def createFields(self):
        while True:
            field = MetadataBlock(self,"metadata_block[]")
            yield field
            if field["last_metadata_block"].value:
                break

class FlacParser(Parser):
    "Parse FLAC audio files: FLAC is a lossless audio codec"
    MAGIC = "fLaC\x00"
    PARSER_TAGS = {
        "id": "flac",
        "category": "audio",
        "file_ext": ("flac",),
        "mime": (u"audio/x-flac",),
        "magic": ((MAGIC, 0),),
        "min_size": 4*8,
        "description": "FLAC audio",
    }
    endian = BIG_ENDIAN

    def validate(self):
        if self.stream.readBytes(0, len(self.MAGIC)) != self.MAGIC:
            return u"Invalid magic string"
        return True

    def createFields(self):
        yield String(self, "signature", 4,charset="ASCII", description="FLAC signature: fLaC string")
        yield Metadata(self,"metadata")
#        yield FlacFrames(self,"frames")

