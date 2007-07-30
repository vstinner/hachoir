from hachoir_metadata.metadata import RootMetadata, registerExtractor
from hachoir_metadata.safe import fault_tolerant
from hachoir_parser.container import SwfFile
from hachoir_parser.misc import TorrentFile, TrueTypeFontFile, OLE2_File, PcfFile
from hachoir_core.field import isString
from hachoir_core.error import warning
from hachoir_parser import guessParser

class TorrentMetadata(RootMetadata):
    KEY_TO_ATTR = {
        u"announce": "url",
        u"comment": "comment",
        u"creation_date": "creation_date",
    }
    INFO_TO_ATTR = {
        u"length": "file_size",
        u"name": "filename",
    }

    def extract(self, torrent):
        for field in torrent[0]:
            self.processRoot(field)

    @fault_tolerant
    def processRoot(self, field):
        if field.name in self.KEY_TO_ATTR:
            key = self.KEY_TO_ATTR[field.name]
            value = field.value
            setattr(self, key, value)
        elif field.name == "info" and "value" in field:
            for field in field["value"]:
                self.processInfo(field)

    @fault_tolerant
    def processInfo(self, field):
        if field.name in self.INFO_TO_ATTR:
            key = self.INFO_TO_ATTR[field.name]
            value = field.value
            setattr(self, key, value)
        elif field.name == "piece_length":
            self.comment = "Piece length: %s" % field.display

class TTF_Metadata(RootMetadata):
    NAMEID_TO_ATTR = {
        0: "copyright",   # Copyright notice
        3: "title",       # Unique font identifier
        5: "version",     # Version string
        8: "author",      # Manufacturer name
        11: "url",        # URL Vendor
        14: "copyright",  # License info URL
    }

    def extract(self, ttf):
        if "header" in ttf:
            self.extractHeader(ttf["header"])
        if "names" in ttf:
            self.extractNames(ttf["names"])

    @fault_tolerant
    def extractHeader(self, header):
        self.creation_date = header["created"].value
        self.last_modification = header["modified"].value
        self.comment = u"Smallest readable size in pixels: %s pixels" % header["lowest"].value
        self.comment = u"Font direction: %s" % header["font_dir"].display

    @fault_tolerant
    def extractNames(self, names):
        offset = names["offset"].value
        for header in names.array("header"):
            key = header["nameID"].value
            foffset = offset + header["offset"].value
            field = names.getFieldByAddress(foffset*8)
            if not field or not isString(field):
                continue
            value = field.value
            if key not in self.NAMEID_TO_ATTR:
                continue
            key = self.NAMEID_TO_ATTR[key]
            if key == "version" and value.startswith(u"Version "):
                # "Version 1.2" => "1.2"
                value = value[8:]
            setattr(self, key, value)

class OLE2_Metadata(RootMetadata):
    SUMMARY_ID_TO_ATTR = {
         2: ("title", False),
         4: ("author", False),
         6: ("comment", False),
         8: ("author", False),
         9: ("version", True), # Revision number
        12: ("creation_date", False),
        13: ("last_modification", False),
        14: ("nb_page", False),
        15: ("comment", True), # Nb. words
        16: ("comment", True), # Nb. characters
        18: ("producer", False),
    }

    def extract(self, ole2):
        if "summary[0]" in ole2:
            self.useSummary(ole2["summary[0]"])

    def useSummary(self, summary):
        # FIXME: Remove this hack
        # Problem: there is no method to get all fragments from a file
        summary.parent._feedAll()
        # ---

        stream = summary.getSubIStream()
        summary = guessParser(stream)
        if not summary:
            print "Unable to create summary parser"

        if "os" in summary:
            self.os = summary["os"].display
        if "section[0]" not in summary:
            return
        summary = summary["section[0]"]
        for property in summary.array("property_index"):
            self.useProperty(summary, property)

    @fault_tolerant
    def useProperty(self, summary, property):
        field = summary.getFieldByAddress(property["offset"].value*8)
        if not field:
            return
        if not field.hasValue():
            return
        value = field.value
        try:
            key, use_prefix = self.SUMMARY_ID_TO_ATTR[property["id"].value]
        except LookupError:
#                warning("Skip %s[%s]=%s" % (
#                    property["id"].display, property["id"].value, value))
            return
        if use_prefix:
            value = "%s: %s" % (property["id"].display, value)
        setattr(self, key, value)

class PcfMetadata(RootMetadata):
    PROP_TO_KEY = {
        'CHARSET_REGISTRY': 'charset',
        'COPYRIGHT': 'copyright',
        'WEIGHT_NAME': 'font_weight',
        'FOUNDRY': 'author',
        'FONT': 'title',
        '_XMBDFED_INFO': 'producer',
    }

    def extract(self, pcf):
        if "properties" in pcf:
            self.useProperties(pcf["properties"])

    def useProperties(self, properties):
        last = properties["total_str_length"]
        offset0 = last.address + last.size
        for index in properties.array("property"):
            # Search name and value
            value = properties.getFieldByAddress(offset0+index["value_offset"].value*8)
            if not value:
                continue
            value = value.value
            if not value:
                continue
            name = properties.getFieldByAddress(offset0+index["name_offset"].value*8)
            if not name:
                continue
            name = name.value
            if name not in self.PROP_TO_KEY:
                warning("Skip %s=%r" % (name, value))
                continue
            key = self.PROP_TO_KEY[name]
            setattr(self, key, value)

class SwfMetadata(RootMetadata):
    def extract(self, swf):
        self.height = swf["rect/ymax"].value # twips
        self.width = swf["rect/xmax"].value # twips
        self.format_version = "flash version %s" % swf["version"].value
        self.frame_rate = swf["frame_rate"].value
        self.comment = "Frame count: %s" % swf["frame_count"].value

registerExtractor(TorrentFile, TorrentMetadata)
registerExtractor(TrueTypeFontFile, TTF_Metadata)
registerExtractor(OLE2_File, OLE2_Metadata)
registerExtractor(PcfFile, PcfMetadata)
registerExtractor(SwfFile, SwfMetadata)

