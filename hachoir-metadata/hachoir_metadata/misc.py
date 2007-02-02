from hachoir_metadata.metadata import Metadata, registerExtractor
from hachoir_parser.misc import TorrentFile

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

registerExtractor(TorrentFile, TorrentMetadata)

