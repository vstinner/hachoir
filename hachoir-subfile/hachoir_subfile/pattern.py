from hachoir_parser import QueryParser
from hachoir_regex import PatternMatching

class HachoirPatternMatching(PatternMatching):
    def __init__(self, categories=None, parser_ids=None):
        PatternMatching.__init__(self)

        # Load parser list
        tags = []
        if categories: tags += [ ("category", cat) for cat in categories ]
        if parser_ids: tags += [ ("id", parser_id) for parser_id in parser_ids ]
        if tags      : tags += [ None ]
        parser_list = QueryParser(tags)

        # Create string patterns
        for parser in parser_list:
            for (magic, offset) in parser.getParserTags().get("magic",()):
                self.addString(magic, (offset, parser))

        # Create regex patterns
        for parser in parser_list:
            for (regex, offset) in parser.getParserTags().get("magic_regex",()):
                self.addRegex(regex, (offset, parser))
        self.commit()

    def search(self, data):
        for start, stop, item in PatternMatching.search(self, data):
            yield (item.user[1], start*8 - item.user[0])

