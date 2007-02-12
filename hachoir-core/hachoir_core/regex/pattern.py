from hachoir_core.regex import RegexEmpty, RegexOr, parse, createString
from hachoir_core.tools import makePrintable
from hachoir_core.error import warning

class Pattern:
    def __init__(self, user):
        self.user = user

class StringPattern(Pattern):
    def __init__(self, text, user=None):
        Pattern.__init__(self, user)
        self.text = text

    def __repr__(self):
        return "<StringPattern '%s'>" % makePrintable(self.text, 'ASCII', to_unicode=True)

class RegexPattern(Pattern):
    def __init__(self, regex, user=None):
        Pattern.__init__(self, user)
        self.regex = parse(regex)
        self.compiled_regex = self.regex.compile(python=True)

    def __repr__(self):
        return "<RegexPattern '%s'>" % self.regex

    def match(self, data):
        return self.compiled_regex.match(data)

class PatternMatching:
    """
    Fast pattern matching class.

    Create your patterns:

    >>> p=PatternMatching()
    >>> p.addString("a")
    >>> p.addString("b")
    >>> p.addRegex("[cd]")
    >>> p.commit()

    Search patterns:

    >>> list( p.search("a b c") )
    [(0, <StringPattern 'a'>), (2, <StringPattern 'b'>), (4, <RegexPattern '[cd]'>)]
    """
    def __init__(self):
        self.string_patterns = []
        self.string_dict = {}
        self.regex_patterns = []

    def commit(self):
        length = 0
        regex = None
        for item in self.string_patterns:
            if regex:
                regex |= createString(item.text)
            else:
                regex = createString(item.text)
            length = max(length, len(item.text))
        for item in self.regex_patterns:
            if regex:
                regex |= item.regex
            else:
                regex = item.regex
            length = max(length, item.regex.maxLength())
        if not regex:
            regex = RegexEmpty()
        self.regex = regex.compile(python=True)
        self.max_length = length

    def addString(self, magic, user=None):
        item = StringPattern(magic, user)
        if item.text not in self.string_dict:
            self.string_patterns.append(item)
            self.string_dict[item.text] = item
        else:
            text = makePrintable(item.text, "ASCII", to_unicode=True)
            warning("Skip duplicate string pattern (%s)" % text)

    def addRegex(self, regex, user=None):
        item = RegexPattern(regex, user)
        if item.regex.maxLength() is not None:
            self.regex_patterns.append(item)
        else:
            regex = makePrintable(str(item.regex), 'ASCII', to_unicode=True)
            warning("Skip invalid regex pattern (%s)" % regex)

    def getPattern(self, data):
        """
        Get pattern item matching data.
        Raise KeyError if no pattern does match it.
        """
        # Try in string patterns
        try:
            return self.string_dict[data]
        except KeyError:
            pass

        # Try in regex patterns
        for item in self.regex_patterns:
            if item.match(data):
                return item
        raise KeyError("Unable to get pattern item")

    def search(self, data):
        """
        Search patterns in data.
        Return a generator (offset, item)
        """
        for match in self.regex.finditer(data):
            item = self.getPattern(match.group(0))
            yield (match.start(0), item)

if __name__ == "__main__":
    import doctest, sys
    failure, nb_test = doctest.testmod()
    if failure:
        sys.exit(1)

