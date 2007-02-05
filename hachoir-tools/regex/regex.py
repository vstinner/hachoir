"""
Object to manage regular expressions, try to optimize the result:
 - '(a|b)' => '[ab]'
 - '(color red|color blue)' => 'color (red|blue)'
 - '(red color|blue color)' => '(red|blue) color'
 - '([ab]|c)' => '[abc]'
 - 'ab' + 'cd' => 'abcd' (one long string)
 - [a-z]|[b] => [a-z]
 - [a-c]|[a-e] => [a-z]
 - [a-c]|[d] => [a-d]
 - [a-c]|[d-f] => [a-f]

Operation:
 - str(): convert to string
 - repr(): debug string
 - a & b: concatenation, eg. "big " & "car" => "big car"
 - a + b: alias to a & b
 - a | b: a or b, eg. "dog" | "cat" => "dog|cat"
 - minLength(): minimum length of matching pattern, "(cat|horse)".minLength() => 3
 - maxLength(): maximum length of matching pattern, "(cat|horse)".maxLength() => 5

TODO:
 - Repeat: a? a+ a* a{n} a{n,p}
 - Support Unicode regex (avoid mixing str and unicode types)

Complex TODO:
 - (chien.|chat[0]) => ch(ien.|at[0])
"""

import re
import itertools
import operator

def escapeRegex(text):
    # Escape >> ^.+*?{}[]|()\$ <<, prefix them with >> \ <<
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

def createRange(*text, **kw):
    """
    Create a regex range using character list.

    >>> createRange("a", "d", "b")
    <RegexRange '[a-bd]'>
    >>> createRange("-", "9", "4", "3", "0")
    <RegexRange '[93-40-]'>
    """
    ranges = ( RegexRangeCharacter(item) for item in text )
    return RegexRange(ranges, kw.get('exclude', False))

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

    def _and(self, regex):
        """
        Create new optimized version of a+b.
        Returns None if there is no interesting optimization.
        """
        if self.__class__ == RegexEmpty:
            return regex
        return None

    def __and__(self, regex):
        """
        Create new optimized version of a & b.
        Returns None if there is no interesting optimization.

        >>> RegexEmpty() & RegexString('a')
        <RegexString 'a'>
        """
        new_regex = self._and(regex)
        if new_regex:
            return new_regex
        else:
            return RegexAnd( (self, regex) )

    def __add__(self, regex):
        return self.__and__(regex)

    def _or(self, regex):
        """
        Create new optimized version of a|b.
        Returns None if there is no interesting optimization.
        """
        if self == regex:
            return self
        return None

    def __or__(self, regex):
        new_regex = self._or(regex)
        if new_regex:
            return new_regex
        else:
            return RegexOr( (self, regex) )

    def __eq__(self, regex):
        # TODO: Write better/faster code...
        return str(self) == str(regex)

    def compile(self):
        return re.compile(str(self))

class RegexEmpty(Regex):
    def minLength(self):
        return 0

    def __str__(self):
        return ''

    def _and(self, regex):
        return regex

class RegexStart(Regex):
    def minLength(self):
        return 0

    def _and(self, regex):
        if regex.__class__ == RegexStart:
            return self
        return None

    def __str__(self):
        return '^'

class RegexEnd(RegexStart):
    def _and(self, regex):
        if regex.__class__ == RegexEnd:
            return self
        return None

    def __str__(self):
        return '$'

class RegexDot(Regex):
    def minLength(self):
        return 1

    def __str__(self):
        return '.'

class RegexString(Regex):
    def __init__(self, text=""):
        assert isinstance(text, str)
        self._text = text

    def minLength(self):
        return len(self._text)

    def _and(self, regex):
        """
        >>> RegexString('a') + RegexString('b')
        <RegexString 'ab'>
        """
        if regex.__class__ == RegexString:
            return RegexString(self._text + regex._text)
        return None

    def __str__(self):
        return escapeRegex(self._text)

    def _or(self, regex):
        """
        Remove duplicate:
        >>> RegexString("color") | RegexString("color")
        <RegexString 'color'>

        Group prefix:

        >>> RegexString("moot") | RegexString("boot")
        <RegexAnd '[mb]oot'>
        >>> RegexString("color red") | RegexString("color blue")
        <RegexAnd 'color (red|blue)'>
        >>> RegexString("color red") | RegexString("color")
        <RegexAnd 'color( red|)'>

        Group suffix:

        >>> RegexString("good thing") | RegexString("blue thing")
        <RegexAnd '(good|blue) thing'>
        """
        # (a|[b-c]) => [a-c]
        if regex.__class__ == RegexRange and len(self._text) == 1:
            return createRange(self._text) | regex

        # Don't know any other optimization for str|other
        if regex.__class__ != RegexString:
            return None

        # text|text => text
        texta = self._text
        textb = regex._text
        if texta == textb:
            return self

        # (a|b) => [ab]
        if len(texta) == len(textb) == 1:
            ranges = (RegexRangeCharacter(texta), RegexRangeCharacter(textb))
            return RegexRange(ranges)

        # Find common prefix
        common = None
        for length in xrange(1, min(len(texta),len(textb))+1):
            if textb.startswith(texta[:length]):
                common = length
            else:
                break
        if common:
            return RegexString(texta[:common]) + (RegexString(texta[common:]) | RegexString(textb[common:]))

        # Find common suffix
        common = None
        for length in xrange(1, min(len(texta),len(textb))+1):
            if textb.endswith(texta[-length:]):
                common = length
            else:
                break
        if common:
            return ((RegexString(texta[:-common]) | RegexString(textb[:-common]))) + RegexString(texta[-common:])
        return None

class RegexRangeItem:
    def __init__(self, cmin, cmax):
        try:
            self.cmin = ord(cmin)
            if cmax is not None:
                self.cmax = ord(cmax)
            else:
                self.cmax = cmin
        except TypeError:
            raise TypeError("RegexRangeItem: two characters expected (%s, %s) found" % (type(cmin), type(cmax)))
        if self.cmax < self.cmin:
            raise TypeError("RegexRangeItem: minimum (%u) is bigger than maximum (%u)" %
                (self.cmin, self.cmax))

    def __contains__(self, value):
        return (self.cmin <= value.cmin) and (value.cmax <= self.cmax)

    def __str__(self):
        if self.cmin != self.cmax:
            return "%c-%c" % (self.cmin, self.cmax)
        else:
            return chr(self.cmin)

    def __repr__(self):
        return "<RegexRangeItem %u-%u>" % (self.cmin, self.cmax)

class RegexRangeCharacter(RegexRangeItem):
    def __init__(self, char):
        RegexRangeItem.__init__(self, char, char)

class RegexRange(Regex):
    def __init__(self, ranges, exclude=False):
        self.ranges = []
        for item in ranges:
            RegexRange.rangeAdd(self.ranges, item)
        self.exclude = exclude

    @staticmethod
    def rangeAdd(ranges, itemb):
        """
        Add a value in a RegexRangeItem() list:
        remove duplicates and merge ranges when it's possible.
        """
        for index, itema in enumerate(ranges):
            if itema in itemb:
                ranges[index] = itemb
                return
            elif itemb in itema:
                return
            elif (itemb.cmax+1) == itema.cmin:
                ranges[index] = RegexRangeItem(chr(itemb.cmin),chr(itema.cmax))
                return
            elif (itema.cmax+1) == itemb.cmin:
                ranges[index] = RegexRangeItem(chr(itema.cmin),chr(itemb.cmax))
                return
        ranges.append(itemb)

    def minLength(self):
        return 1

    def _or(self, regex):
        """
        >>> createRange("a") | createRange("b")
        <RegexRange '[a-b]'>
        >>> createRange("a", "b", exclude=True) | createRange("a", "c", exclude=True)
        <RegexRange '[^a-c]'>
        """
        if not self.exclude and regex.__class__ == RegexString and len(regex._text) == 1:
            branges = (RegexRangeCharacter(regex._text),)
        elif regex.__class__ == RegexRange and self.exclude == regex.exclude:
            branges = regex.ranges
        else:
            return None
        ranges = list(self.ranges)
        for itemb in branges:
            RegexRange.rangeAdd(ranges, itemb)
        return RegexRange(ranges, self.exclude)

    def __str__(self):
        content = [str(item) for item in self.ranges]
        if "-" in content:
            content.remove("-")
            suffix = "-"
        else:
            suffix = ""
        if "]" in content:
            content.remove("]")
            prefix = "]"
        else:
            prefix = ""
        text = prefix + (''.join(content)) + suffix
        if self.exclude:
            return "[^%s]" % text
        else:
            return "[%s]" % text

class RegexAnd(Regex):
    def __init__(self, items):
        self.content = list(items)
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

    def _and(self, regex):
        """
        >>> RegexDot() + RegexDot()
        <RegexAnd '..'>
        >>> RegexDot() + RegexString('a') + RegexString('b')
        <RegexAnd '.ab'>
        """

        if regex.__class__ == RegexAnd:
            total = self
            for item in regex.content:
                total = total + item
            return total
        new_item = self.content[-1]._and(regex)
        if new_item:
            self.content[-1] = new_item
            return self
        return RegexAnd( self.content + [regex] )

    def __str__(self):
        return ''.join( str(item) for item in self.content )

    @classmethod
    def join(cls, regex):
        """
        >>> RegexAnd.join( (RegexString('Big '), RegexString('fish')) )
        <RegexString 'Big fish'>
        """
        return _join(operator.__and__, regex)

class RegexOr(Regex):
    def __init__(self, items):
        self.content = []
        for item in items:
            if item in self:
                continue
            self.content.append(item)
        assert 2 <= len(self.content)

    def __contains__(self, regex):
        for item in self.content:
            if item == regex:
                return True
        return False

    def _or(self, regex):
        """
        >>> (RegexString("abc") | RegexString("123")) | (RegexString("plop") | RegexString("456"))
        <RegexOr '(abc|123|plop|456)'>
        >>> RegexString("mouse") | createRange('a') | RegexString("2006") | createRange('z')
        <RegexOr '(mouse|[az]|2006)'>
        """
        if regex.__class__ == RegexOr:
            total = self
            for item in regex.content:
                total = total | item
            return total
        if regex in self:
            return self
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
        >>> RegexOr.join( (RegexString('a'), RegexString('b'), RegexString('c')) )
        <RegexRange '[a-c]'>
        """
        return _join(operator.__or__, regex)

if __name__ == "__main__":
    import doctest
    doctest.testmod()

