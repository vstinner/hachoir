import re
import types
from hachoir_core.error import HachoirError
from hachoir_core.i18n import _
from hachoir_parser import Parser
from hachoir_core import config

### Parser list ################################################################

class ParserList(object):
    VALID_CATEGORY = ("archive", "audio", "container", "file_system",
        "game", "image", "misc", "program", "video")
    ID_REGEX = re.compile("^[a-z0-9][a-z0-9_]{2,}$")

    def __init__(self):
        self.parser_list = []
        self.byid = {}
        self.bycategory = {}

    def add(self, parser):
        # Check parser
        err = self.checkParser(parser)
        if err:
            raise HachoirError("Invalid parser %s: %s" % (parser.__name__, err))

        # Store parser in parser list
        self.parser_list.append(parser)

        # Store parser with its identifier
        parser_id = parser.tags["id"]
        if parser_id in self.byid:
            raise HachoirError("Duplicate parser id: %s used by %s and %s" %
                (parser_id, self.byid[parser_id].__name__, parser.__name__))
        self.byid[parser_id] = parser

        # Store parser by its category
        category = parser.tags["category"]
        if category in self.bycategory:
            self.bycategory[category].append(parser)
        else:
            self.bycategory[category] = [parser]

    def __iter__(self):
        return iter(self.parser_list)

    def checkParser(self, parser):
        """
        Check 'tags' attribute of a parser.
        Return a string describing the error, or "" if the parser is valid.
        """
        # Check tags attribute
        if not hasattr(parser, "tags"):
            return "No tags attribute (tags)"
        tags = parser.tags
        if not tags.get("description", ""):
            return "Empty description (description)"
        if not tags.get("min_size", 0):
            return "Nul minimum size (min_size)"
        if not self.ID_REGEX.match(tags.get("id", "")):
            return "Invalid identifier ('%s'), have to be at least 3 alphanumeric characters (small case)" % tags.get("id", "")
        if tags.get("category", "") not in self.VALID_CATEGORY:
            return "Invalid category: %s" % tags.get("category", "")
        if "mime" in tags and not isinstance(tags["mime"], (list, tuple)):
            return "MIME type (mime) have to be a list or tuple"
        if "file_ext" in tags and not isinstance(tags["file_ext"], (list, tuple)):
            return "File extensions (file_ext) have to be a list or tuple"
        return ""

    def printParser(self, parser, verbose):
        tags = parser.tags
        print "- %s: %s" % (tags["id"], tags["description"])
        if not verbose:
            return
        if "mime" in tags:
            print "  MIME type: %s" % (", ".join(tags["mime"]))
        if "file_ext" in tags:
            file_ext = ", ".join(
                ".%s" % file_ext for file_ext in tags["file_ext"])
            print "  File extension: %s" % file_ext

    def print_(self, title=None, verbose=False):
        """Display a list of parser with its title
         * title : title of the list to display
        """

        if title:
            print title
        else:
            print _("List of Hachoir parsers.")

        # Create parser list sorted by module
        for category in sorted(self.bycategory.iterkeys()):
            print
            print "[%s]" % category
            parser_list = sorted(self.bycategory[category],
                key=lambda parser: parser.tags["id"])
            for parser in parser_list:
                self.printParser(parser, verbose)
        print
        print "Total: %s parsers" % len(self.parser_list)

    def __getitem__(self, key):
        return self.byid[key]

class HachoirParserList(ParserList):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self):
        ParserList.__init__(self)
        self._load()

    def _load(self):
        """
        Load all parsers from "hachoir.parser" module.

        Return the list of loaded parsers.
        """
        # Parser list is already loaded?
        if self.parser_list:
            return self.parser_list

        todo = []
        module = __import__("hachoir_parser")
        for attrname in dir(module):
            attr = getattr(module, attrname)
            if isinstance(attr, types.ModuleType):
                parser = attr
                todo.append(attr)

        for module in todo:
            attributes = ( getattr(module, name) for name in dir(module) )
            parsers = list( attr for attr in attributes \
                if isinstance(attr, type) \
                   and issubclass(attr, Parser) \
                   and hasattr(attr, "tags"))
            for parser in parsers:
                self.add(parser)
        assert 1 <= len(self.parser_list)
        return self.parser_list

