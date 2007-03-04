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
            self.extractPE(exe)
        elif exe.isNE():
            self.extractNE(exe)

    def extractNE(self, exe):
        if "ne_header" in exe:
            self.useNE_Header(exe["ne_header"])
        if "info" in exe:
            for node in exe.array("info/node"):
                if node["name"].value == "StringFileInfo":
                    self.readVersionInfo(node["node[0]"])

    def extractPE(self, exe):
        # Read information from headers
        if "pe_header" in exe:
            self.usePE_Header(exe["pe_header"])
        if "pe_opt_header" in exe:
            self.usePE_OptHeader(exe["pe_opt_header"])

        # Use PE ressource
        ressource = exe.getRessource()
        if ressource and "version_info/node[0]" in ressource:
            for node in ressource.array("version_info/node[0]/node"):
                if node["name"].value == "StringFileInfo":
                    self.readVersionInfo(node["node[0]"])

    def useNE_Header(self, hdr):
        if hdr["is_dll"].value:
            self.format_version = "New-style executable: Dynamic-link library (DLL)"
        elif hdr["is_win_app"].value:
            self.format_version = "New-style executable: Windows 3.x application"
        else:
            self.format_version = "New-style executable for Windows 3.x"

    def usePE_Header(self, hdr):
        self.creation_date = hdr["creation_date"].value
        self.comment = "CPU: %s" % hdr["cpu"].display
        if hdr["is_dll"].value:
            self.format_version = "Portable Executable: Dynamic-link library (DLL)"
        else:
            self.format_version = "Portable Executable: Windows application"

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

