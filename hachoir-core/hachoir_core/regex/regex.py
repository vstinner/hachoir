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
 - Support Unicode regex (avoid mixing str and unicode types)
 - createString("__tax") | parse("__[12]") => group '__'
 - Make sure that all RegexXXX() classes are inmutable
 - Use singleton for dot, start and end

See also CPAN Regexp::Assemble (Perl module):
   http://search.cpan.org/~dland/Regexp-Assemble-0.28/Assemble.pm
"""

from hachoir_core.compatibility import all, any
from hachoir_core.tools import makePrintable
import re
import itertools
import operator

def matchSingleValue(regex):
    """
    Regex only match one exact string.

    >>> matchSingleValue(RegexEmpty())
    True
    >>> matchSingleValue(createString("abc"))
    True
    >>> matchSingleValue(createRange("a", "b"))
    False
    >>> matchSingleValue(createRange("a"))
    True
    >>> matchSingleValue(RegexAnd((RegexStart(), createString("abc"))))
    True
    """
    cls = regex.__class__
    if cls in (RegexEmpty, RegexString, RegexStart, RegexEnd):
        return True
    if cls == RegexAnd:
        return all( matchSingleValue(item) for item in regex )
    if cls == RegexRange:
        return len(regex.ranges) == 1 and len(regex.ranges[0]) == 1
    return False

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

def createString(text):
    """
    >>> createString('')
    <RegexEmpty ''>
    >>> createString('abc')
    <RegexString 'abc'>
    """
    if text:
        return RegexString(text)
    else:
        return RegexEmpty()

def createRange(*text, **kw):
    """
    Create a regex range using character list.

    >>> createRange("a", "d", "b")
    <RegexRange '[abd]'>
    >>> createRange("-", "9", "4", "3", "0")
    <RegexRange '[0349-]'>
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

    def __str__(self, **kw):
        if not hasattr(self, "_str_value"):
            self._str_value = {}
        key = kw.get('python', False)
        if key not in self._str_value:
            self._str_value[key] = self._str(**kw)
        return self._str_value[key]

    def _str(self, **kw):
        raise NotImplementedError()

    def __repr__(self):
        regex = makePrintable(str(self), 'ASCII', to_unicode=True)
        return "<%s '%s'>" % (
            self.__class__.__name__, regex)

    def __contains__(self, item):
        raise NotImplementedError()

    def match(self, regex):
        """
        Guess if self may matchs regex.
        May returns False even if self does match regex.
        """
        if str(self) == str(regex):
            return True
        return self._match(regex)

    def _match(self, regex):
        return False

    def _and(self, regex):
        """
        Create new optimized version of a+b.
        Returns None if there is no interesting optimization.
        """
        return None

    def __and__(self, regex):
        """
        Create new optimized version of a & b.
        Returns None if there is no interesting optimization.

        >>> RegexEmpty() & RegexString('a')
        <RegexString 'a'>
        """
        if regex.__class__ == RegexEmpty:
            return self
        new_regex = self._and(regex)
        if new_regex:
            return new_regex
        else:
            return RegexAnd( (self, regex) )

    def __add__(self, regex):
        return self.__and__(regex)

    def or_(self, regex):
        """
        Create new optimized version of a|b.
        Returns None if there is no interesting optimization.
        """
        # (a|b) where a match b => a
        # eg. ([a-z|[a-b]) => [a-z]
        if self.match(regex):
            return self

        # (b|a) where b match a => a
        if regex.match(self):
            return regex

        # Try to optimize (a|b)
        new_regex = self._or_(regex, False)
        if new_regex:
            return new_regex

        # Try to optimize (b|a)
        new_regex = regex._or_(self, True)
        if new_regex:
            return new_regex
        return None

    def _or_(self, regex, reverse):
        return None

    def __or__(self, regex):
        # Try to optimize (a|b)
        new_regex = self.or_(regex)
        if new_regex:
            return new_regex

        # Else use (a|b)
        return RegexOr( (self, regex) )

    def __eq__(self, regex):
        # TODO: Write better/faster code...
        return str(self) == str(regex)

    def compile(self, **kw):
        return re.compile(self.__str__(**kw))

    def findPrefix(self, regex):
        return None

    def __iter__(self):
        raise NotImplementedError()

class RegexEmpty(Regex):
    def minLength(self):
        return 0

    def _str(self, **kw):
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

    def _str(self, **kw):
        return '^'

class RegexEnd(RegexStart):
    def _and(self, regex):
        if regex.__class__ == RegexEnd:
            return self
        return None

    def _str(self, **kw):
        return '$'

class RegexDot(Regex):
    def minLength(self):
        return 1

    def _str(self, **kw):
        return '.'

    def _match(self, regex):
        if regex.__class__ == RegexRange:
            return True
        if regex.__class__ == RegexString and len(regex._text) == 1:
            return True
        return False

class RegexString(Regex):
    def __init__(self, text=""):
        assert isinstance(text, str)
        self._text = text
        assert 1 <= len(self._text)

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

    def _str(self, **kw):
        return escapeRegex(self._text)

    def findPrefix(self, regex):
        """
        Try to find a common prefix of two string regex, returns:
         - None if there is no common prefix
         - (prefix, regexa, regexb) otherwise => prefix + (regexa|regexb)

        >>> RegexString('color red').findPrefix(RegexString('color blue'))
        (<RegexString 'color '>, <RegexString 'red'>, <RegexString 'blue'>)
        """
        if regex.__class__ != RegexString:
            return None
        texta = self._text
        textb = regex._text

        # '(a|b)' => '[ab]'
        if len(texta) == len(textb) == 1:
            return (createRange(texta, textb),  RegexEmpty(), RegexEmpty())

        # '(text abc|text def)' => 'text (abc|def)'
        common = None
        for length in xrange(1, min(len(texta),len(textb))+1):
            if textb.startswith(texta[:length]):
                common = length
            else:
                break
        if not common:
            return None
        return (RegexString(texta[:common]), createString(texta[common:]), createString(textb[common:]))

    def _or_(self, regex, reverse):
        """
        Remove duplicate:
        >>> RegexString("color") | RegexString("color")
        <RegexString 'color'>

        Group prefix:

        >>> RegexString("color red") | RegexString("color blue")
        <RegexAnd 'color (red|blue)'>
        >>> RegexString("color red") | RegexString("color")
        <RegexAnd 'color( red|)'>

        """

        # Don't know any other optimization for str|other
        if regex.__class__ != RegexString:
            return None

        # Find common prefix
        common = self.findPrefix(regex)
        if common:
            if not reverse:
                regex = common[1] | common[2]
            else:
                regex = common[2] | common[1]
            return common[0] + regex
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

    def __len__(self):
        return (self.cmax - self.cmin + 1)

    def __contains__(self, value):
        assert issubclass(value.__class__, RegexRangeItem)
        return (self.cmin <= value.cmin) and (value.cmax <= self.cmax)

    def __str__(self, **kw):
        cmin = chr(self.cmin)
        if self.cmin != self.cmax:
            cmax = chr(self.cmax)
            if (self.cmin+1) == self.cmax:
                return "%s%s" % (cmin, cmax)
            else:
                return "%s-%s" % (cmin, cmax)
        else:
            return cmin

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
        self.ranges.sort(key=lambda item: item.cmin)
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

    def _match(self, regex):
        """
        >>> createRange("a") | createRange("b")
        <RegexRange '[ab]'>
        >>> createRange("a", "b", exclude=True) | createRange("a", "c", exclude=True)
        <RegexRange '[^a-c]'>
        """
        if not self.exclude and regex.__class__ == RegexString and len(regex._text) == 1:
            branges = (RegexRangeCharacter(regex._text),)
        elif regex.__class__ == RegexRange and self.exclude == regex.exclude:
            branges = regex.ranges
        else:
            return None
        for itemb in branges:
            if not any( itemb in itema for itema in self.ranges ):
                return False
        return True

    def _or_(self, regex, reverse):
        """
        >>> createRange("a") | createRange("b")
        <RegexRange '[ab]'>
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

    def _str(self, **kw):
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

    def _or_(self, regex, reverse):
        if regex.__class__ == RegexString:
            contentb = [regex]
        elif regex.__class__ == RegexAnd:
            contentb = regex.content
        else:
            return None

        contenta = self.content
        if reverse:
            contenta, contentb = contentb, contenta

        # Find common prefix
        # eg. (ab|ac) => a(b|c) and (abc|abd) => ab(c|d)
        index = 0
        last_index = min(len(contenta), len(contentb))
        while index < last_index and contenta[index] == contentb[index]:
            index += 1
        if index:
            regex = RegexAnd.join(contenta[index:]) | RegexAnd.join(contentb[index:])
            return RegexAnd.join(contenta[:index]) + regex

        # Find common prefix: (abc|aef) => a(bc|ef)
        common = contenta[0].findPrefix(contentb[0])
        if common:
            regexa = common[1] & RegexAnd.join( contenta[1:] )
            regexb = common[2] & RegexAnd.join( contentb[1:] )
            regex = (regexa | regexb)
            if matchSingleValue(common[0]) or matchSingleValue(regex):
                return common[0] + regex
        return None

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

    def _str(self, **kw):
        return ''.join( item.__str__(**kw) for item in self.content )

    @classmethod
    def join(cls, regex):
        """
        >>> RegexAnd.join( (RegexString('Big '), RegexString('fish')) )
        <RegexString 'Big fish'>
        """
        return _join(operator.__and__, regex)

    def __iter__(self):
        return iter(self.content)

# TODO: Remove this code or use it
def firstCharacter(regex):
    cls = regex.__class__
    if cls == RegexString:
        return regex._text[0]
    if cls == RegexRange:
        return chr(regex.ranges[0].cmin)
    if cls in (RegexOr, RegexAnd):
        return firstCharacter(regex.content[0])
    x = str(regex)
    if x:
        return x[0]
    else:
        return "\0"

class RegexOr(Regex):
    def __init__(self, items):
        self.content = []
        for item in items:
            if item in self:
                continue
            self.content.append(item)
        assert 2 <= len(self.content)
#        self.content.sort(key=firstCharacter)

    def __contains__(self, regex):
        for item in self.content:
            if item == regex:
                return True
        return False

    def _or_(self, regex, reverse):
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
        for index, item in enumerate(self.content):
            new_item = item.or_(regex)
            if not new_item:
                new_item = regex.or_(item)
            if new_item:
                content = self.content[:index] + [new_item] \
                    + self.content[index+1:]
                return RegexOr.join(content)
        if not reverse:
            content = self.content + [regex]
        else:
            content = [regex] + self.content
        return RegexOr(content)

    def _str(self, **kw):
        content = '|'.join( item.__str__(**kw) for item in self.content )
        if kw.get('python', False):
            return "(?:%s)" % content
        else:
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

    def __iter__(self):
        return iter(self.content)

def optimizeRepeatOr(rmin, rmax, regex):
    # Fix rmin/rmax
    for item in regex:
        cls = item.__class__
        if cls == RegexEmpty:
            # (a|b|){x,y} => (a|b){0,y}
            rmin = 0
        elif cls == RegexRepeat:
            # (a{0,n}|b){x,y} => (a{1,n}|b){0,y}
            if item.min == 0 and rmin == 1:
                rmin = 0

    # Create new (optimized) RegexOr expression
    content = []
    for item in regex:
        cls = item.__class__
        if cls == RegexEmpty:
            # (a|){x,y} => a{0,y}
            continue
        if cls == RegexRepeat:
            if item.min == 0:
                if rmin in (0, 1):
                    if rmax == item.max == None:
                        # (a*|b){x,} => (a|b){x,}
                        item = item.regex
                    else:
                        # (a{0,p}|b){x,} => (a{1,p}|b){x,}
                        item = RegexRepeat(item.regex, 1, item.max)
            elif item.min == 1:
                if rmax == item.max == None:
                    # (a+|b){x,} => (a|b){x,}
                    item = item.regex
            else:
                if rmax == item.max == None:
                    # (a{n,}|b){x,} => (a{n}|b){x,}
                    item = RegexRepeat(item.regex, item.min, item.min)
        content.append(item)
    regex = RegexOr.join(content)
    return (rmin, rmax, regex)

class RegexRepeat(Regex):
    """
    >>> a=createString('a')
    >>> RegexRepeat(a, 0, None)
    <RegexRepeat 'a*'>
    >>> RegexRepeat(a, 1, None)
    <RegexRepeat 'a+'>
    >>> RegexRepeat(a, 0, 1)
    <RegexRepeat 'a?'>
    >>> RegexRepeat(a, 0, 1)
    <RegexRepeat 'a?'>
    >>> RegexRepeat(a, 1, 3)
    <RegexRepeat 'a{1,3}'>
    """

    def __init__(self, regex, rmin, rmax):
        # Optimisations
        cls = regex.__class__
        if cls == RegexRepeat:
            # (a{n,p}){x,y) => a{n*x,p*y}
            rmin *= regex.min
            if regex.max and rmax:
                rmax *= regex.max
            else:
                rmax = None
            regex = regex.regex
        elif cls == RegexOr:
            rmin, rmax, regex = optimizeRepeatOr(rmin, rmax, regex)

        # Store attributes
        self.regex = regex
        self.min = rmin
        self.max = rmax

        # Post-conditions
        assert 0 <= rmin
        if self.max is not None:
            if self.max < self.min:
                raise ValueError("RegexRepeat: minimum (%s) is bigger than maximum (%s)!" % (self.min, self.max))
            if (self.max == 0) \
            or (self.min == self.max == 1):
                raise ValueError("RegexRepeat: invalid values (min=%s, max=%s)!" % (self.min, self.max))

    def minLength(self):
        """
        >>> r=RegexRepeat(createString("abc") | createString("01"), 1, 3)
        >>> r.minLength(), r.maxLength()
        (2, 9)
        >>> r=RegexRepeat(createString("abc") | createString("01"), 4, None)
        >>> r.minLength(), r.maxLength()
        (8, None)
        """
        if self.min is not None:
            return self.regex.minLength() * self.min
        else:
            return None

    def maxLength(self):
        if self.max is not None:
            return self.regex.maxLength() * self.max
        else:
            return None

    def _str(self, **kw):
        text = str(self.regex)
        if self.min == 0 and self.max == 1:
            return "%s?" % text
        if self.min == self.max:
            return "%s{%u}" % (text, self.min)
        if self.max is None:
            if self.min == 0:
                return "%s*" % text
            elif self.min == 1:
                return "%s+" % text
            else:
                return "%s{%u,}" % (text, self.min)
        return "%s{%u,%u}" % (text, self.min, self.max)

if __name__ == "__main__":
    import doctest
    doctest.testmod()

