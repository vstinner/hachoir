"""
TrueType Font parser.

Documents:
 - "The OpenType Specification"
   https://docs.microsoft.com/en-us/typography/opentype/spec/
 - "An Introduction to TrueType Fonts: A look inside the TTF format"
   written by "NRSI: Computers & Writing Systems"
   http://scripts.sil.org/cms/scripts/page.php?site_id=nrsi&item_id=IWS-Chapter08

Author: Victor Stinner
Creation date: 2007-02-08
"""

from hachoir.parser import Parser
from hachoir.field import (
    FieldSet,
    ParserError,
    UInt8,
    UInt16,
    UInt32,
    Int16,
    Bit,
    Bits,
    PaddingBits,
    NullBytes,
    String,
    RawBytes,
    Bytes,
    Enum,
    TimestampMac32,
    GenericVector,
    PascalString8,
)
from hachoir.core.endian import BIG_ENDIAN
from hachoir.core.text_handler import textHandler, hexadecimal, filesizeHandler

MAX_NAME_COUNT = 300
MIN_NB_TABLE = 3
MAX_NB_TABLE = 30

DIRECTION_NAME = {
    0: "Mixed directional",
    1: "Left to right",
    2: "Left to right + neutrals",
    -1: "Right to left",
    -2: "Right to left + neutrals",
}

NAMEID_NAME = {
    0: "Copyright notice",
    1: "Font family name",
    2: "Font subfamily name",
    3: "Unique font identifier",
    4: "Full font name",
    5: "Version string",
    6: "Postscript name",
    7: "Trademark",
    8: "Manufacturer name",
    9: "Designer",
    10: "Description",
    11: "URL Vendor",
    12: "URL Designer",
    13: "License Description",
    14: "License info URL",
    16: "Preferred Family",
    17: "Preferred Subfamily",
    18: "Compatible Full",
    19: "Sample text",
    20: "PostScript CID findfont name",
}

PLATFORM_NAME = {
    0: "Unicode",
    1: "Macintosh",
    2: "ISO",
    3: "Microsoft",
    4: "Custom",
}

CHARSET_MAP = {
    # (platform, encoding) => charset
    0: {3: "UTF-16-BE"},
    1: {0: "MacRoman"},
    3: {1: "UTF-16-BE"},
}


FWORD = Int16
UFWORD = UInt16


class Tag(String):
    def __init__(self, parent, name, description=None):
        String.__init__(self, parent, name, 4, description)


class Version16Dot16(FieldSet):
    static_size = 32

    def createFields(self):
        yield UInt16(self, "major")
        yield UInt16(self, "minor")

    def createValue(self):
        return float("%u.%x" % (self["major"].value, self["minor"].value))


class Fixed(FieldSet):
    def createFields(self):
        yield UInt16(self, "int_part")
        yield UInt16(self, "float_part")

    def createValue(self):
        return self["int_part"].value + float(self["float_part"].value) / 65536


class TableHeader(FieldSet):
    def createFields(self):
        yield Tag(self, "tag")
        yield textHandler(UInt32(self, "checksum"), hexadecimal)
        yield UInt32(self, "offset")
        yield filesizeHandler(UInt32(self, "size"))

    def createDescription(self):
        return "Table entry: %s (%s)" % (self["tag"].display, self["size"].display)


class NameHeader(FieldSet):
    def createFields(self):
        yield Enum(UInt16(self, "platformID"), PLATFORM_NAME)
        yield UInt16(self, "encodingID")
        yield UInt16(self, "languageID")
        yield Enum(UInt16(self, "nameID"), NAMEID_NAME)
        yield UInt16(self, "length")
        yield UInt16(self, "offset")

    def getCharset(self):
        platform = self["platformID"].value
        encoding = self["encodingID"].value
        try:
            return CHARSET_MAP[platform][encoding]
        except KeyError:
            self.warning("TTF: Unknown charset (%s,%s)" % (platform, encoding))
            return "ISO-8859-1"

    def createDescription(self):
        platform = self["platformID"].display
        name = self["nameID"].display
        return "Name record: %s (%s)" % (name, platform)


def parseFontHeader(self):
    yield UInt16(self, "maj_ver", "Major version")
    yield UInt16(self, "min_ver", "Minor version")
    yield UInt16(self, "font_maj_ver", "Font major version")
    yield UInt16(self, "font_min_ver", "Font minor version")
    yield textHandler(UInt32(self, "checksum"), hexadecimal)
    yield Bytes(self, "magic", 4, r"Magic string (\x5F\x0F\x3C\xF5)")
    if self["magic"].value != b"\x5F\x0F\x3C\xF5":
        raise ParserError("TTF: invalid magic of font header")

    # Flags
    yield Bit(self, "y0", "Baseline at y=0")
    yield Bit(self, "x0", "Left sidebearing point at x=0")
    yield Bit(self, "instr_point", "Instructions may depend on point size")
    yield Bit(self, "ppem", "Force PPEM to integer values for all")
    yield Bit(self, "instr_width", "Instructions may alter advance width")
    yield Bit(self, "vertical", "e laid out vertically?")
    yield PaddingBits(self, "reserved[]", 1)
    yield Bit(self, "linguistic", "Requires layout for correct linguistic rendering?")
    yield Bit(self, "gx", "Metamorphosis effects?")
    yield Bit(self, "strong", "Contains strong right-to-left glyphs?")
    yield Bit(self, "indic", "contains Indic-style rearrangement effects?")
    yield Bit(self, "lossless", "Data is lossless (Agfa MicroType compression)")
    yield Bit(self, "converted", "Font converted (produce compatible metrics)")
    yield Bit(self, "cleartype", "Optimised for ClearType")
    yield Bits(self, "adobe", 2, "(used by Adobe)")

    yield UInt16(self, "unit_per_em", "Units per em")
    if not (16 <= self["unit_per_em"].value <= 16384):
        raise ParserError("TTF: Invalid unit/em value")
    yield UInt32(self, "created_high")
    yield TimestampMac32(self, "created")
    yield UInt32(self, "modified_high")
    yield TimestampMac32(self, "modified")
    yield UInt16(self, "xmin")
    yield UInt16(self, "ymin")
    yield UInt16(self, "xmax")
    yield UInt16(self, "ymax")

    # Mac style
    yield Bit(self, "bold")
    yield Bit(self, "italic")
    yield Bit(self, "underline")
    yield Bit(self, "outline")
    yield Bit(self, "shadow")
    yield Bit(self, "condensed", "(narrow)")
    yield Bit(self, "expanded")
    yield PaddingBits(self, "reserved[]", 9)

    yield UInt16(self, "lowest", "Smallest readable size in pixels")
    yield Enum(UInt16(self, "font_dir", "Font direction hint"), DIRECTION_NAME)
    yield Enum(UInt16(self, "ofst_format"), {0: "short offsets", 1: "long"})
    yield UInt16(self, "glyph_format", "(=0)")


def parseNames(self):
    # Read header
    yield UInt16(self, "format")
    if self["format"].value != 0:
        raise ParserError("TTF (names): Invalid format (%u)" % self["format"].value)
    yield UInt16(self, "count")
    yield UInt16(self, "offset")
    if MAX_NAME_COUNT < self["count"].value:
        raise ParserError("Invalid number of names (%s)" % self["count"].value)

    # Read name index
    entries = []
    for index in range(self["count"].value):
        entry = NameHeader(self, "header[]")
        yield entry
        entries.append(entry)

    # Sort names by their offset
    entries.sort(key=lambda field: field["offset"].value)

    # Read name value
    last = None
    for entry in entries:
        # Skip duplicates values
        new = (entry["offset"].value, entry["length"].value)
        if last and last == new:
            self.warning("Skip duplicate %s %s" % (entry.name, new))
            continue
        last = (entry["offset"].value, entry["length"].value)

        # Skip negative offset
        offset = entry["offset"].value + self["offset"].value
        if offset < self.current_size // 8:
            self.warning("Skip value %s (negative offset)" % entry.name)
            continue

        # Add padding if any
        padding = self.seekByte(offset, relative=True, null=True)
        if padding:
            yield padding

        # Read value
        size = entry["length"].value
        if size:
            yield String(
                self, "value[]", size, entry.description, charset=entry.getCharset()
            )

    padding = (self.size - self.current_size) // 8
    if padding:
        yield NullBytes(self, "padding_end", padding)


def parseMaxp(self):
    # Read header
    yield Version16Dot16(self, "format", "format version")
    yield UInt16(self, "numGlyphs", "Number of glyphs")
    if self["format"].value >= 1:
        yield UInt16(self, "maxPoints", "Maximum points in a non-composite glyph")
        yield UInt16(self, "maxContours", "Maximum contours in a non-composite glyph")
        yield UInt16(self, "maxCompositePoints", "Maximum points in a composite glyph")
        yield UInt16(
            self, "maxCompositeContours", "Maximum contours in a composite glyph"
        )
        yield UInt16(self, "maxZones", "Do instructions use the twilight zone?")
        yield UInt16(self, "maxTwilightPoints", "Maximum points used in Z0")
        yield UInt16(self, "maxStorage", "Number of Storage Area locations")
        yield UInt16(self, "maxFunctionDefs", "Number of function definitions")
        yield UInt16(self, "maxInstructionDefs", "Number of instruction definitions")
        yield UInt16(self, "maxStackElements", "Maximum stack depth")
        yield UInt16(
            self, "maxSizeOfInstructions", "Maximum byte count for glyph instructions"
        )
        yield UInt16(
            self,
            "maxComponentElements",
            "Maximum number of components at glyph top level",
        )
        yield UInt16(self, "maxComponentDepth", "Maximum level of recursion")


def parseHhea(self):
    yield UInt16(self, "majorVersion", "Major version")
    yield UInt16(self, "minorVersion", "Minor version")
    yield FWORD(self, "ascender", "Typographic ascent")
    yield FWORD(self, "descender", "Typographic descent")
    yield FWORD(self, "lineGap", "Typographic linegap")
    yield UFWORD(self, "advanceWidthMax", "Maximum advance width")
    yield FWORD(self, "minLeftSideBearing", "Minimum left sidebearing value")
    yield FWORD(self, "minRightSideBearing", "Minimum right sidebearing value")
    yield FWORD(self, "xMaxExtent", "Maximum X extent")
    yield Int16(self, "caretSlopeRise", "Caret slope rise")
    yield Int16(self, "caretSlopeRun", "Caret slope run")
    yield Int16(self, "caretOffset", "Caret offset")
    yield GenericVector(self, "reserved", 4, Int16)
    yield Int16(self, "metricDataFormat", "Metric data format")
    yield Int16(self, "numberOfHMetrics", "Number of horizontal metrics")


def parseOS2(self):
    yield UInt16(self, "version", "Table version")
    yield Int16(self, "xAvgCharWidth")
    yield UInt16(self, "usWeightClass")
    yield UInt16(self, "usWidthClass")
    yield UInt16(self, "fsType")
    yield Int16(self, "ySubscriptXSize")
    yield Int16(self, "ySubscriptYSize")
    yield Int16(self, "ySubscriptXOffset")
    yield Int16(self, "ySubscriptYOffset")
    yield Int16(self, "ySuperscriptXSize")
    yield Int16(self, "ySuperscriptYSize")
    yield Int16(self, "ySuperscriptXOffset")
    yield Int16(self, "ySuperscriptYOffset")
    yield Int16(self, "yStrikeoutSize")
    yield Int16(self, "yStrikeoutPosition")
    yield Int16(self, "sFamilyClass")
    yield GenericVector(self, "panose", 10, UInt8)
    yield UInt32(self, "ulUnicodeRange1")
    yield UInt32(self, "ulUnicodeRange2")
    yield UInt32(self, "ulUnicodeRange3")
    yield UInt32(self, "ulUnicodeRange4")
    yield Tag(self, "achVendID", "Vendor ID")
    yield UInt16(self, "fsSelection")
    yield UInt16(self, "usFirstCharIndex")
    yield UInt16(self, "usLastCharIndex")
    yield Int16(self, "sTypoAscender")
    yield Int16(self, "sTypoDescender")
    yield Int16(self, "sTypoLineGap")
    yield UInt16(self, "usWinAscent")
    yield UInt16(self, "usWinDescent")
    if self["version"].value >= 1:
        yield UInt32(self, "ulCodePageRange1")
        yield UInt32(self, "ulCodePageRange2")
    if self["version"].value >= 2:
        yield Int16(self, "sxHeight")
        yield Int16(self, "sCapHeight")
        yield UInt16(self, "usDefaultChar")
        yield UInt16(self, "usBreakChar")
        yield UInt16(self, "usMaxContext")
    if self["version"].value >= 5:
        yield UInt16(self, "usLowerOpticalPointSize")
        yield UInt16(self, "usUpperOpticalPointSize")


def parsePost(self):
    yield Version16Dot16(self, "version", "Table version")
    yield Fixed(
        self,
        "italicAngle",
        "Italic angle in counter-clockwise degrees from the vertical.",
    )
    yield FWORD(self, "underlinePosition", "Top of underline to baseline")
    yield FWORD(self, "underlineThickness", "Suggested underline thickness")
    yield UInt32(self, "isFixedPitch", "Is the font fixed pitch?")
    yield UInt32(self, "minMemType42", "Minimum memory usage (OpenType)")
    yield UInt32(self, "maxMemType42", "Maximum memory usage (OpenType)")
    yield UInt32(self, "minMemType1", "Minimum memory usage (Type 1)")
    yield UInt32(self, "maxMemType1", "Maximum memory usage (Type 1)")
    if self["version"].value == 2.0:
        yield UInt16(self, "numGlyphs")
        indices = GenericVector(
            self,
            "Array of indices into the string data",
            self["numGlyphs"].value,
            UInt16,
            "glyphNameIndex",
        )
        yield indices
        for gid, index in enumerate(indices):
            if index.value >= 258:
                yield PascalString8(self, "glyphname[%i]" % gid)
    elif self["version"].value == 2.0:
        yield UInt16(self, "numGlyphs")
        indices = GenericVector(
            self,
            "Difference between graphic index and standard order of glyph",
            self["numGlyphs"].value,
            UInt16,
            "offset",
        )
        yield indices


parseScriptList = parseFeatureList = parseLookupList = lambda x: None


def parseGSUB(self):
    yield UInt16(self, "majorVersion", "Major version")
    yield UInt16(self, "minorVersion", "Minor version")
    SUBTABLES = [
        ("script list", parseScriptList),
        ("feature list", parseFeatureList),
        ("lookup list", parseLookupList),
    ]
    offsets = []
    for description, parser in SUBTABLES:
        name = description.title().replace(" ", "")
        offset = UInt16(
            self, name[0].lower() + name[1:], "Offset to %s table" % description
        )
        yield offset
        offsets.append((offset.value, parser))
    if self["min_ver"].value == 1:
        offset = UInt32(
            self, "featureVariationsOffset", "Offset to feature variations table"
        )
        offsets.append((offset.value, parseFeatureVariationsTable))

    offsets.sort(key=lambda field: field[0])
    padding = self.seekByte(offsets[0][0], null=True)
    if padding:
        yield padding
    lastOffset, first_parser = offsets[0]
    for offset, parser in offsets[1:]:
        # yield parser(self)
        yield RawBytes(self, "content", offset - lastOffset)
        lastOffset = offset


class Table(FieldSet):
    TAG_INFO = {
        "head": ("header", "Font header", parseFontHeader),
        "name": ("names", "Names", parseNames),
        "maxp": ("maxp", "Maximum Profile", parseMaxp),
        "hhea": ("hhea", "Horizontal Header", parseHhea),
        "GSUB": ("GSUB", "Glyph Substitutions", parseGSUB),
        "OS/2": ("OS/2", "OS/2 and Windows Metrics", parseOS2),
        "post": ("post", "PostScript", parsePost),
    }

    def __init__(self, parent, name, table, **kw):
        FieldSet.__init__(self, parent, name, **kw)
        self.table = table
        tag = table["tag"].value
        if tag in self.TAG_INFO:
            self._name, self._description, self.parser = self.TAG_INFO[tag]
        else:
            self.parser = None

    def createFields(self):
        if self.parser:
            yield from self.parser(self)
        else:
            yield RawBytes(self, "content", self.size // 8)

    def createDescription(self):
        return "Table %s (%s)" % (self.table["tag"].value, self.table.path)


class TrueTypeFontFile(Parser):
    endian = BIG_ENDIAN
    PARSER_TAGS = {
        "id": "ttf",
        "category": "misc",
        "file_ext": ("ttf",),
        "min_size": 10 * 8,  # FIXME
        "description": "TrueType font",
    }

    def validate(self):
        if self["maj_ver"].value == 1 and self["min_ver"].value == 0:
            pass
        elif self["maj_ver"].value == 0x4F54 and self["min_ver"].value == 0x544F:
            pass
        else:
            return "Invalid version (%u.%u)" % (
                self["maj_ver"].value,
                self["min_ver"].value,
            )
        if not (MIN_NB_TABLE <= self["nb_table"].value <= MAX_NB_TABLE):
            return "Invalid number of table (%u)" % self["nb_table"].value
        return True

    def createFields(self):
        yield UInt16(self, "maj_ver", "Major version")
        yield UInt16(self, "min_ver", "Minor version")
        yield UInt16(self, "nb_table")
        yield UInt16(self, "search_range")
        yield UInt16(self, "entry_selector")
        yield UInt16(self, "range_shift")
        tables = []
        for index in range(self["nb_table"].value):
            table = TableHeader(self, "table_hdr[]")
            yield table
            tables.append(table)
        tables.sort(key=lambda field: field["offset"].value)
        for table in tables:
            padding = self.seekByte(table["offset"].value, null=True)
            if padding:
                yield padding
            size = table["size"].value
            if size:
                yield Table(self, "table[]", table, size=size * 8)
        padding = self.seekBit(self.size, null=True)
        if padding:
            yield padding
