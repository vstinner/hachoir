from hachoir_metadata.metadata import (
    Metadata, MultipleMetadata, registerExtractor)
from hachoir_parser.archive import Bzip2Parser, CabFile, GzipParser, TarFile, ZipFile
from hachoir_core.tools import humanFilesize, humanUnixAttributes
from hachoir_core.i18n import _

MAX_NB_FILE = 5

class FileMetadata(Metadata):
    header = _("File")
    def __init__(self):
        Metadata.__init__(self)
        self.register("filename", 300, _("File name"))
        self.register("file_size", 301, _("File size"), handler=humanFilesize)
        self.register("compr_size", 310, _("Compressed file size"), handler=humanFilesize)
        self.register("compr_rate", 320, _("Compression rate"))

        self.register("file_attr", 400, _("File attributes"))
        self.register("file_type", 401, _("File type"))

    def computeCompressionRate(self):
        """
        Compute compression rate, sizes have to be in byte.
        """
        file_size, compr_size = self.file_size[0], self.compr_size[0]
        if file_size:
            rate = 100 - float(compr_size) * 100 / file_size
            self.compr_rate = "%.1f%%" % rate

class Bzip2Metadata(FileMetadata):
    def extract(self, zip):
        self.compr_size = zip["file"].size/8

class GzipMetadata(FileMetadata):
    def extract(self, gzip):
        if "filename" in gzip:
            self.filename = gzip["filename"].value
        self.compr_size = gzip["file"].size/8
        self.compression = gzip["compression"].display
        self.file_size = gzip["size"].value
        self.last_modification = gzip["mtime"].display
        self.producer = _("Created on operating system: %s") % gzip["os"].display
        if "comment" in gzip:
            self.comment = gzip["comment"].value
        self.computeCompressionRate()

class ZipMetadata(MultipleMetadata):
    def extract(self, zip):
        for index, field in enumerate(zip.array("file")):
            if MAX_NB_FILE <= index:
                self.warning("ZIP archive contains many files, but only first %s files are processed" % MAX_NB_FILE)
                break
            meta = FileMetadata()
            meta.filename = field["filename"].value
            meta.creation_date = field["last_mod"].display
            meta.compression = field["compression"].display
            if "data_desc" in field:
                meta.file_size = field["data_desc/file_uncompressed_size"].value
                if field["data_desc/file_compressed_size"].value:
                    meta.compr_size = field["data_desc/file_compressed_size"].value
                    meta.computeCompressionRate()
            else:
                meta.file_size = field["uncompressed_size"].value
                if field["compressed_size"].value:
                    meta.compr_size = field["compressed_size"].value
                    meta.computeCompressionRate()
            self.addGroup(field.name, meta, "File \"%s\"" % meta.filename[0])

class TarMetadata(MultipleMetadata):
    def extract(self, tar):
        for index, field in enumerate(tar.array("file")):
            if MAX_NB_FILE <= index:
                self.warning("TAR archive contains many files, but only first %s files are processed" % MAX_NB_FILE)
                break
            meta = FileMetadata()
            meta.filename = field["name"].value
            meta.file_size = field.getOctal("size")
            try:
                meta.last_modification = field.getDatetime()
            except ValueError:
                pass
            meta.file_attr = humanUnixAttributes(field.getOctal("mode"))
            meta.file_type = field["type"].display
            meta.author = "%s (uid=%s), group %s (gid=%s)" %\
                (field["uname"].value, field.getOctal("uid"),
                 field["gname"].value, field.getOctal("gid"))
            if hasattr(meta, "filename"):
                title = _("File \"%s\"") % meta.filename[0]
            else:
                title = _("File")
            self.addGroup(field.name, meta, title)

class CabMetadata(MultipleMetadata):
    def extract(self, cab):
        compr = cab["folder[0]/compr_method"].display
        if cab["folder[0]/compr_method"].value != 0:
            compr += " (level %u)" % cab["folder[0]/compr_level"].value
        self.compression = compr
        self.format_version = "Microsoft Cabinet version %s" % cab["cab_version"].display
        self.comment = "%s folders, %s files" % (
            cab["nb_folder"].value, cab["nb_files"].value)
        for index, field in enumerate(cab.array("file")):
            if MAX_NB_FILE <= index:
                self.warning("CAB archive contains many files, but only first %s files are processed" % MAX_NB_FILE)
                break
            meta = FileMetadata()
            meta.filename = field["filename"].value
            meta.file_size = field["filesize"].value
            meta.creation_date = field["timestamp"].value
            attr = field["attributes"].value
            if attr != "(none)":
                meta.file_attr = attr
            if hasattr(meta, "filename"):
                title = _("File \"%s\"") % meta.filename[0]
            else:
                title = _("File")
            self.addGroup(field.name, meta, title)

registerExtractor(CabFile, CabMetadata)
registerExtractor(GzipParser, GzipMetadata)
registerExtractor(Bzip2Parser, Bzip2Metadata)
registerExtractor(TarFile, TarMetadata)
registerExtractor(ZipFile, ZipMetadata)

