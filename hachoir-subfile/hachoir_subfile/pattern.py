from hachoir_parser import QueryParser
from hachoir_subfile.create_regex import createRegex, dumpRegex
from hachoir_core.tools import makePrintable
from hachoir_core.error import warning
from hachoir_core.regex import (
    parse as parseRegex,
    createString as regexFromString,
    RegexOr, RegexEmpty)
import re

class Pattern:
    def __init__(self, parser, offset):
        self.parser = parser
        self.offset = offset

class StringPattern(Pattern):
    def __init__(self, text, offset, parser):
        Pattern.__init__(self, parser, offset)
        self.text = text

class RegexPattern(Pattern):
    def __init__(self, regex, offset, parser):
        Pattern.__init__(self, parser, offset)
        self.regex = parseRegex(regex)
        self.compiled_regex = self.regex.compile(python=True)

    def match(self, data):
        return self.compiled_regex.match(data)

class PatternMatching:
    def __init__(self, categories=None, parser_ids=None):
        self.string_patterns = []
        self.string_dict = {}
        self.regex_patterns = []

        # Load parser list
        tags = []
        if categories: tags += [ ("category", cat) for cat in categories ]
        if parser_ids: tags += [ ("id", parser_id) for parser_id in parser_ids ]
        if tags      : tags += [ None ]
        parser_list = QueryParser(tags)

        # Create string patterns
        for parser in parser_list:
            for (magic, offset) in parser.getTags().get("magic",()):
                self._addString(magic, offset, parser)

        # Create regex patterns
        for parser in parser_list:
            for (regex, offset) in parser.getTags().get("magic_regex",()):
                self._addRegex(regex, offset, parser)

        self._update()
        assert self.string_patterns or self.regex_patterns

    def _update(self):
        length = 0
        regex = None
        for item in self.string_patterns:
            if regex:
                regex |= regexFromString(item.text)
            else:
                regex = regexFromString(item.text)
            length = max(length, len(item.text))
        for item in self.regex_patterns:
            if regex:
                regex |= item.regex
            else:
                regex = item.regex
            length = max(length, item.regex.maxLength())
        self.regex = regex.compile(python=True)
        self.max_length = length

    def _addString(self, magic, offset, parser):
        item = StringPattern(magic, offset, parser)
        if item.text not in self.string_dict:
            self.string_patterns.append(item)
            self.string_dict[item.text] = item
        else:
            text = makePrintable(item.text, "ASCII", to_unicode=True)
            warning("Skip parser %s: duplicate pattern (%s)" % (
                item.parser.__name__, text))

    def _addRegex(self, regex, offset, parser):
        item = RegexPattern(regex, offset, parser)
        if item.regex.maxLength() is not None:
            self.regex_patterns.append(item)
        else:
            regex = makePrintable(str(item.regex), 'ASCII', to_unicode=True)
            warning("Skip parser %s: invalid regex (%s)" % (
                item.parser.__name__, regex))

    def getPattern(self, data):
        # Try in string patterns
        try:
            return self.string_dict[data]
        except KeyError:
            pass

        # Try in regex patterns
        for item in self.regex_patterns:
            if item.match(data):
                return item
        raise RuntimeError("Unable to get parser")

    def search(self, data):
        for match in self.regex.finditer(data):
            item = self.getPattern(match.group(0))
            offset = match.start(0)*8 - item.offset
            yield (item.parser, offset)

