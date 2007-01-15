import re
import types
from hachoir_core.error import HachoirError
from hachoir_core.i18n import _

### Parser list ################################################################

class ParserList:
    VALID_CATEGORY = ("archive", "audio", "container", "file_system",
        "game", "image", "misc", "program", "video")
    ID_REGEX = re.compile("^[a-z0-9][a-z0-9_]{2,}$")

    def __init__(self):
        self.parser_list = None

    def add(self, parser):
        pass

    def load(self):
        """
        Load all parsers from "hachoir.parser" module.

        Return the list of loaded parsers.
        """
        # Parser list is already loaded?
        if self.parser_list:
            return self.parser_list

        self.parser_list = []
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
                err = validParser(parser)
                if err:
                    raise HachoirError("Invalid parser %s: %s" % (parser.__name__, err))
            self.parser_list.extend(parsers)
        assert 1 <= len(self.parser_list)
        return self.parser_list

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

    def print_(title=None):
        """Display a list of parser with its title
         * title : title of the list to display
         * self.parser_list : list of parser (default get from loadParser())
        """

        if title:
            print title
        else:
            print _("List of Hachoir parsers.")

        # Get parser list (if not specified)
        if not self.parser_list:
            self.parser_list = loadParsers()

        # Create parser list sorted by module
        parsers_by_module = {}
        for parser in self.parser_list:
            module = parser.__module__.split(".")[1]
            if module in parsers_by_module:
                parsers_by_module[module].append(parser)
            else:
                parsers_by_module[module] = [parser]
        for module in sorted(parsers_by_module):
            print "\n[%s]" % module
            for parser in parsers_by_module[module]:
                text = ["- "]
                mimes = parser.tags.get("mime", ())
                if not isinstance(mimes, str):
                    if len(mimes):
                        mimes = ", ".join(mimes)
                        text.append(mimes)
                        text.append(": ")
                    else:
                        mimes = "(no mime type)"
                text.append(parser.tags["description"])
                print "".join(text)
        print


import re
import types
from hachoir_core.error import HachoirError
from hachoir_core.i18n import _

### Parser list ################################################################

class ParserList:
    VALID_CATEGORY = ("archive", "audio", "container", "file_system",
        "game", "image", "misc", "program", "video")
    ID_REGEX = re.compile("^[a-z0-9][a-z0-9_]{2,}$")

    def __init__(self):
        self.parser_list = None

    def add(self, parser):
        pass

    def load(self):
        """
        Load all parsers from "hachoir.parser" module.

        Return the list of loaded parsers.
        """
        # Parser list is already loaded?
        if self.parser_list:
            return self.parser_list

        self.parser_list = []
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
                err = validParser(parser)
                if err:
                    raise HachoirError("Invalid parser %s: %s" % (parser.__name__, err))
            self.parser_list.extend(parsers)
        assert 1 <= len(self.parser_list)
        return self.parser_list

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

    def print_(title=None):
        """Display a list of parser with its title
         * title : title of the list to display
         * self.parser_list : list of parser (default get from loadParser())
        """

        if title:
            print title
        else:
            print _("List of Hachoir parsers.")

        # Get parser list (if not specified)
        if not self.parser_list:
            self.parser_list = loadParsers()

        # Create parser list sorted by module
        parsers_by_module = {}
        for parser in self.parser_list:
            module = parser.__module__.split(".")[1]
            if module in parsers_by_module:
                parsers_by_module[module].append(parser)
            else:
                parsers_by_module[module] = [parser]
        for module in sorted(parsers_by_module):
            print "\n[%s]" % module
            for parser in parsers_by_module[module]:
                text = ["- "]
                mimes = parser.tags.get("mime", ())
                if not isinstance(mimes, str):
                    if len(mimes):
                        mimes = ", ".join(mimes)
                        text.append(mimes)
                        text.append(": ")
                    else:
                        mimes = "(no mime type)"
                text.append(parser.tags["description"])
                print "".join(text)
        print


