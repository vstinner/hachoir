import re
import operator

def escapeRegex(text):
    # Escape "^.+*?{}[]|()\\$": add "\"
    return re.sub(r"([][^.+*?{}|()\\$])", r"\\\1", text)

def _join(func, regex_list):
    if not isinstance(regex_list, (tuple, list)):
        regex_list = list(regex_list)
    if len(regex_list) == 0:
        return RegexEmpty()
    regex = regex_list[0]
    for item in regex_list[1:]:
        regex = func(regex, item)
    return regex

class Regex:
    def minLength(self):
        """
        Maximum length in characters of the regex.
        Returns None if there is no limit.
        """
        raise NotImplementedError()
    def maxLength(self):
        """
        Maximum length in characters of the regex.
        Returns None if there is no limit.
        """
        return self.minLength()

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        return "<%s '%s'>" % (
            self.__class__.__name__, self)

    def __add__(self, regex):
        """
        >>> RegexEmpty() + RegexString('a')
        <RegexString 'a'>
        """
        if regex.__class__ == RegexEmpty:
            return self
        else:
            return RegexAnd( (self, regex) )

    def __and__(self, regex):
        return RegexAnd( (self, regex) )

    def _or(self, regex):
        return None

    def __or__(self, regex):
        new_regex = self._or(regex)
        if new_regex:
            return new_regex
        else:
            return RegexOr( (self, regex) )

    def __eq__(self, regex):
        # TODO: Write better code...
        return str(self) == str(regex)

class RegexEmpty(Regex):
    def minLength(self):
        return 0

    def __str__(self):
        return ''

    def __repr__(self):
        return "<RegexEmpty>"

    def __add__(self, regex):
        return regex

class RegexString(Regex):
    def __init__(self, text=""):
        assert isinstance(text, str)
        self._text = text

    def minLength(self):
        return len(self._text)

    def __add__(self, regex):
        """
        >>> RegexString('a') + RegexString('b')
        <RegexString 'ab'>
        """
        if regex.__class__ == RegexString:
            return RegexString(self._text + regex._text)
        else:
            return Regex.__add__(self, regex)

    def __str__(self):
        return escapeRegex(self._text)

class RegexRange(Regex):
    def __init__(self, char_range, exclude=False):
        self.range = char_range
        self.exclude = exclude

    def minLength(self):
        # FIXME: len('a-z') is 1
        return len(self.range)

    def _or(self, regex):
        """
        >>> RegexRange("a") | RegexRange("b")
        <RegexRange '[ab]'>
        >>> RegexRange("^ab") | RegexRange("^ac")
        <RegexRange '[^abc]'>
        """
        if regex.__class__ != RegexRange or self.exclude != regex.exclude:
            return None
        crange = self.range
        for character in regex.range:
            if character not in crange:
                crange += character
        return RegexRange(crange, self.exclude)

    def __str__(self):
        if self.exclude:
            return "[^%s]" % self.range
        else:
            return "[%s]" % self.range

class RegexAndOr(Regex):
    def __contains__(self, regex):
        for item in self.content:
            if item == regex:
                return True
        return False

class RegexAnd(RegexAndOr):
    def __init__(self, items):
        self.content = []
        for item in items:
            if item.__class__ == RegexEmpty:
                continue
            if self.content \
            and self.content[-1].__class__ == item.__class__ == RegexString:
                self.content[-1] = RegexString(self.content[-1]._text + item._text)
            else:
                self.content.append(item)
        assert 2 <= len(self.content)

    def _minmaxLength(self, lengths):
        total = 0
        for length in lengths:
            if length is None:
                return None
            total += length
        return total

    def minLength(self):
        """
        >>> regex=((RegexString('a') | RegexString('bcd')) + RegexString('z'))
        >>> regex.minLength()
        2
        """
        return self._minmaxLength( regex.minLength() for regex in self.content )

    def maxLength(self):
        """
        >>> regex=RegexOr((RegexString('a'), RegexString('bcd')))
        >>> RegexAnd((regex, RegexString('z'))).maxLength()
        4
        """
        return self._minmaxLength( regex.maxLength() for regex in self.content )

    def __add__(self, regex):
        """
        >>> a=RegexAnd((RegexString('a'), RegexRange('bc')))
        >>> b=RegexAnd((RegexString('0'), RegexRange('12')))
        >>> a, b
        (<RegexAnd 'a[bc]'>, <RegexAnd '0[12]'>)
        >>> a + b
        <RegexAnd 'a[bc]0[12]'>
        """
        if regex.__class__ == RegexAnd:
            return RegexAnd(self.content + regex.content)
        else:
            return Regex.__add__(self, regex)

    def __str__(self):
        return ''.join( str(item) for item in self.content )

    @classmethod
    def join(cls, regex):
        """
        >>> RegexAnd.join( (RegexString('a'), RegexString('b')) )
        <RegexString 'ab'>
        """
        return _join(operator.__add__, regex)

class RegexOr(RegexAndOr):
    def __init__(self, items):
        self.content = []
        for item in items:
            if item in self:
                continue
            self.content.append(item)
        assert 2 <= len(self.content)

    def _or(self, regex):
        """
        >>> RegexOr((RegexString("a"), RegexString("b"))) | RegexOr((RegexString("c"), RegexString("d")))
        <RegexOr '(a|b|c|d)'>
        >>> RegexOr((RegexString("ab"), RegexRange("c"))) | RegexOr((RegexString("de"), RegexRange("f")))
        <RegexOr '(ab|[cf]|de)'>
        """
        if regex.__class__ == RegexOr:
            total = self
            for item in regex.content:
                total = total | item
            return total
        if regex in self:
            return self
        if regex.__class__ == RegexRange:
            for index, item in enumerate(self.content):
                new_item = item._or(regex)
                if new_item:
                    self.content[index] = new_item
                    return self
        return RegexOr( self.content + [regex] )

    def __str__(self):
        content = '|'.join( str(item) for item in self.content )
        return "(%s)" % content

    def _minmaxLength(self, lengths, func):
        value = None
        for length in lengths:
            if length is None:
                return None
            if value is None:
                value = length
            else:
                value = func(value, length)
        return value

    def minLength(self):
        lengths = ( regex.minLength() for regex in self.content )
        return self._minmaxLength(lengths, min)

    def maxLength(self):
        lengths = ( regex.maxLength() for regex in self.content )
        return self._minmaxLength(lengths, max)

    @classmethod
    def join(cls, regex):
        """
        >>> RegexOr.join( (RegexString('a'), RegexString('b'), RegexString('a')) )
        <RegexOr '(a|b)'>
        """
        return _join(operator.__or__, regex)

if __name__ == "__main__":
    import doctest
    doctest.testmod()

