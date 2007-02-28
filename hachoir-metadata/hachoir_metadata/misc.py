from hachoir_metadata.metadata import Metadata, registerExtractor
from hachoir_parser.misc import TorrentFile, TrueTypeFontFile

class TorrentMetadata(Metadata):
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
            if field.name in self.KEY_TO_ATTR:
                key = self.KEY_TO_ATTR[field.name]
                value = field.value
                setattr(self, key, value)
            elif field.name == "info" and "value" in field:
                self.processInfo(field["value"])
    def processInfo(self, info):
        for field in info:
            if field.name in self.INFO_TO_ATTR:
                key = self.INFO_TO_ATTR[field.name]
                value = field.value
                setattr(self, key, value)
            elif field.name == "piece_length":
                self.comment = "Piece length: %s" % field.display

class TTF_Metadata(Metadata):
    NAMEID_TO_ATTR = {
        0: "copyright",   # Copyright notice
        1: "title",       # Font family name
        3: "title",       # Unique font identifier
        4: "title",       # Full font name
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

    def extractHeader(self, header):
        self.creation_date = header["created"].value
        self.last_modification = header["modified"].value
        self.comment = "Smallest readable size in pixels: %s pixels" % header["lowest"].value
        self.comment = "Font direction: %s" % header["font_dir"].display

    def extractNames(self, names):
        offset = names["offset"].value
        for header in names.array("header"):
            key = header["nameID"].value
            foffset = offset + header["offset"].value
            field = names.getFieldByAddress(foffset*8)
            if not field:
                continue
            value = field.value
            if key not in self.NAMEID_TO_ATTR:
                continue
            key = self.NAMEID_TO_ATTR[key]
            setattr(self, key, value)

registerExtractor(TorrentFile, TorrentMetadata)
registerExtractor(TrueTypeFontFile, TTF_Metadata)

