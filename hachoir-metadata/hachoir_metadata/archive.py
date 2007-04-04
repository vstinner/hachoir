from hachoir_metadata.metadata_item import QUALITY_BEST, QUALITY_FASTEST
from hachoir_metadata.metadata import (
    Metadata, MultipleMetadata, registerExtractor)
from hachoir_parser.archive import (Bzip2Parser, CabFile, GzipParser,
    TarFile, ZipFile, MarFile)
from hachoir_core.tools import humanUnixAttributes
from hachoir_core.i18n import _

def maxNbFile(meta):
    if meta.quality <= QUALITY_FASTEST:
        return 0
    if QUALITY_BEST <= meta.quality:
        return None
    return 1 + int(10 * meta.quality)

def computeCompressionRate(meta):
    """
    Compute compression rate, sizes have to be in byte.
    """
    if not meta.has("file_size") or not meta.has("compr_size"):
        return
    file_size, compr_size = meta.get("file_size"), meta.get("compr_size")
    if not file_size:
        return
    rate = 100 - float(compr_size) * 100 / file_size
    meta.compr_rate = u"%.1f%%" % rate

class Bzip2Metadata(Metadata):
    def extract(self, zip):
        self.compr_size = zip["file"].size/8

class GzipMetadata(Metadata):
    def extract(self, gzip):
        if "filename" in gzip:
            self.filename = gzip["filename"].value
        self.compr_size = gzip["file"].size/8
        self.compression = gzip["compression"].display
        self.file_size = gzip["size"].value
        self.last_modification = gzip["mtime"].value
        self.os = gzip["os"].display
        if "comment" in gzip:
            self.comment = gzip["comment"].value
        computeCompressionRate(self)

class ZipMetadata(MultipleMetadata):
    def extract(self, zip):
        max_nb = maxNbFile(self)
        for index, field in enumerate(zip.array("file")):
            if max_nb is not None and max_nb <= index:
                self.warning("ZIP archive contains many files, but only first %s files are processed" % max_nb)
                break
            meta = Metadata(parent=self)
            meta.filename = field["filename"].value
            meta.creation_date = field["last_mod"].value
            meta.compression = field["compression"].display
            if "data_desc" in field:
                meta.file_size = field["data_desc/file_uncompressed_size"].value
                if field["data_desc/file_compressed_size"].value:
                    meta.compr_size = field["data_desc/file_compressed_size"].value
                    computeCompressionRate(meta)
            else:
                meta.file_size = field["uncompressed_size"].value
                if field["compressed_size"].value:
                    meta.compr_size = field["compressed_size"].value
                    computeCompressionRate(meta)
            self.addGroup(field.name, meta, "File \"%s\"" % meta.get('filename'))

class TarMetadata(MultipleMetadata):
    def extract(self, tar):
        max_nb = maxNbFile(self)
        for index, field in enumerate(tar.array("file")):
            if max_nb is not None and max_nb <= index:
                self.warning("TAR archive contains many files, but only first %s files are processed" % max_nb)
                break
            meta = Metadata(parent=self)
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
            if meta.has("filename"):
                title = _("File \"%s\"") % meta.getText('filename')
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
        max_nb = maxNbFile(self)
        for index, field in enumerate(cab.array("file")):
            if max_nb is not None and max_nb <= index:
                self.warning("CAB archive contains many files, but only first %s files are processed" % max_nb)
                break
            meta = Metadata(parent=self)
            meta.filename = field["filename"].value
            meta.file_size = field["filesize"].value
            meta.creation_date = field["timestamp"].value
            attr = field["attributes"].value
            if attr != "(none)":
                meta.file_attr = attr
            if meta.has("filename"):
                title = _("File \"%s\"") % meta.getText('filename')
            else:
                title = _("File")
            self.addGroup(field.name, meta, title)

class MarMetadata(MultipleMetadata):
    def extract(self, mar):
        self.comment = "Contains %s files" % mar["nb_file"].value
        self.format_version = "Microsoft Archive version %s" % mar["version"].value
        max_nb = maxNbFile(self)
        for index, field in enumerate(mar.array("file")):
            if max_nb is not None and max_nb <= index:
                self.warning("MAR archive contains many files, but only first %s files are processed" % max_nb)
                break
            meta = Metadata(parent=self)
            meta.filename = field["filename"].value
            meta.compression = "None"
            meta.file_size = field["filesize"].value
            self.addGroup(field.name, meta, "File \"%s\"" % meta.getText('filename'))

registerExtractor(CabFile, CabMetadata)
registerExtractor(GzipParser, GzipMetadata)
registerExtractor(Bzip2Parser, Bzip2Metadata)
registerExtractor(TarFile, TarMetadata)
registerExtractor(ZipFile, ZipMetadata)
registerExtractor(MarFile, MarMetadata)

