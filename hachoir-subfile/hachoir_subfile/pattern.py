from hachoir_parser import QueryParser
from hachoir_subfile.create_regex import createRegex, dumpRegex
from hachoir_core.regex import parse as parseRegex, createString as regexFromString, RegexOr

class Patterns:
    def __init__(self, categories=None, parser_ids=None):
        self.magics = []
        self.magic_regex = []
        self.load(categories, parser_ids)
        assert self.magics or self.magic_regex
        self.max_length = self.createMaxLength()

    def createMaxLength(self):
        if self.magics:
            length = max( len(magic) for magic in self.magics )
        else:
            length = 0
        for regex, compiled_regex, magic_offset, parser_cls in self.magics_regex:
            length = max(length, regex.maxLength())
        return length

    def load(self, categories, parser_ids):
        # Choose parsers to use
        tags = []
        if categories: tags += [ ("category", cat) for cat in categories ]
        if parser_ids: tags += [ ("id", parser_id) for parser_id in parser_ids ]
        if tags      : tags += [ None ]
        parser_list = QueryParser(tags)

        # Load parser magics
        magics = []
        for parser in parser_list:
            for (magic, offset) in parser.getTags().get("magic",()):
                # FIXME: Re-enable this code
#                if self.slice_size < offset:
#                    self.slice_size = offset + 8
#                    error("Use slice size of %s because of '%s' parser magic offset" % (
#                        (self.slice_size//8), parser.__name__))
                magics.append((magic, offset, parser))

        # Build regex
        self.magics = {}
        magic_strings = []
        for magic, offset, parser in magics:
            magic_strings.append(magic)
            self.magics[magic] = (offset, parser)
        if magic_strings:
            regex = createRegex(magic_strings)
        else:
            regex = None
        self.magics_regex = []
        for parser in parser_list:
            for (magic_regex, offset) in parser.getTags().get("magic_regex",()):
                new_regex = parseRegex(magic_regex)
                self.magics_regex.append( (new_regex, new_regex.compile(python=True), offset, parser) )
                if new_regex.maxLength() is None:
                    raise RuntimeError("Regex without maximum length")
                if regex:
                    regex = regex | new_regex
                else:
                    regex = new_regex
#        if self.debug:
#            print "Use regex: %s" % makePrintable(str(regex), 'ASCII')
        self.magic_regex = regex.compile(python=True)

    def getParser(self, data):
        # Try in string patterns
        try:
            return self.magics[data]
        except KeyError:
            pass

        # Try in regex patterns
        for regex, compiled_regex, magic_offset, parser_cls in self.magics_regex:
            if compiled_regex.match(data):
                return magic_offset, parser_cls
        raise RuntimeError("Unable to get parser")

    def search(self, stream, start, end):
        regex = self.magic_regex
        data = stream.readBytes(start, (end-start)//8)
        for match in regex.finditer(data):
            magic_offset, parser_cls = self.getParser(match.group(0))
            offset = start + match.start(0)*8 - magic_offset
            yield (parser_cls, offset)

