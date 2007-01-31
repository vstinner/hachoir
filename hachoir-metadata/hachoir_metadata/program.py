from hachoir_metadata.metadata import Metadata, registerExtractor
from hachoir_parser.program import ExeFile

class ExeMetadata(Metadata):
    KEY_TO_ATTR = {
        u"ProductName": "title",
        u"LegalCopyright": "copyright",
        u"LegalTrademarks": "copyright",
        u"LegalTrademarks1": "copyright",
        u"LegalTrademarks2": "copyright",
        u"CompanyName": "author",
        u"BuildDate": "creation_date",
        u"FileDescription": "title",
        u"ProductVersion": "version",
    }
    SKIP_KEY = set((u"InternalName", u"OriginalFilename", u"FileVersion", u"BuildVersion"))

    def extract(self, exe):
        if exe.isPE():
            # Read information from headers
            if "pe_header" in exe:
                self.usePE_Header(exe["pe_header"])
            if "pe_opt_header" in exe:
                self.usePE_OptHeader(exe["pe_opt_header"])

            # Sections name
#            names = [ "%s (%s)" % (section["name"].value.strip("."), section["phys_size"].display) \
#                for section in exe.array("section_hdr") if section["phys_size"].value ]
#            names.sort()
#            self.comment = "Sections: %s" % ", ".join(names)

            # Use PE ressource
            ressource = exe.getRessource()
            if ressource and "version_info/node[0]" in ressource:
                for node in ressource.array("version_info/node[0]/node"):
                    if node["name"].value == "StringFileInfo":
                        self.readVersionInfo(node["node[0]"])

    def usePE_Header(self, hdr):
        self.creation_date = hdr["creation_date"].value
        self.comment = "CPU: %s" % hdr["cpu"].display
        if hdr["is_dll"].value:
            self.format_version = "Microsoft Windows DLL"
        else:
            self.format_version = "Microsoft Windows Portable Executable"

    def usePE_OptHeader(self, hdr):
        self.comment = "Subsystem: %s" % hdr["subsystem"].display

    def readVersionInfo(self, info):
        values = {}
        for node in info.array("node"):
            if "value" not in node:
                continue
            value = node["value"].value
            key = node["name"].value
            values[key] = value
        if "ProductName" in values and "FileDescription" in values \
        and values["ProductName"] == values["FileDescription"]:
            del values["FileDescription"]

        for key, value in values.iteritems():
            if key in self.KEY_TO_ATTR:
                setattr(self, self.KEY_TO_ATTR[key], value)
            elif key not in self.SKIP_KEY:
                self.comment = "%s=%s" % (key, value)

registerExtractor(ExeFile, ExeMetadata)

