"""
Parse string to create Regex object.

TODO:
 - Support \: \001, \x00, \0, \ \[, \(, \{, etc.
 - Support Python extensions: (?:...), (?P<name>...), etc.
 - Support \<, \>, \s, \S, \w, \W, \Z <=> $, \d, \D, \A <=> ^, \b, \B, [[:space:]], etc.
"""

from regex import (RegexString, RegexEmpty, RegexRepeat,
    RegexDot, RegexStart, RegexEnd,
    RegexRange, RegexRangeItem, RegexRangeCharacter)

def parseRange(text, start):
    r"""
    >>> parseRange('[a]b', 1)
    (<RegexRange '[a]'>, 3)
    >>> parseRange('[a-z]b', 1)
    (<RegexRange '[a-z]'>, 5)
    >>> parseRange('[^a-z-]b', 1)
    (<RegexRange '[^a-z-]'>, 7)
    >>> parseRange('[^]-]b', 1)
    (<RegexRange '[^]-]'>, 5)
    """
    index = start
    char_range = []
    exclude = False
    if text[index] == '^':
        exclude = True
        index += 1
    if text[index] == ']':
        char_range.append(RegexRangeCharacter(']'))
        index += 1
    while index < len(text) and text[index] != ']':
        if index+1 < len(text) \
        and text[index] == '-' and text[index+1] == ']':
            break
        if index+3 < len(text) \
        and text[index+1] == '-' \
        and text[index+2] != ']':
            char_range.append(RegexRangeItem(text[index], text[index+2]))
            index += 3
        else:
            char_range.append(RegexRangeCharacter(text[index]))
            index += 1
    if index < len(text) and text[index] == '-':
        char_range.append(RegexRangeCharacter('-'))
        index += 1
    if index == len(text) or text[index] != ']':
        raise SyntaxError('Invalid range: %s' % text[start-1:index])
    return RegexRange(char_range, exclude), index+1

def parseOr(text, start):
    """
    >>> parseOr('(a)', 1)
    (<RegexString 'a'>, 3)
    >>> parseOr('(a|c)', 1)
    (<RegexRange '[ac]'>, 5)
    >>> parseOr(' (a|[bc]|d)', 2)
    (<RegexRange '[a-d]'>, 11)
    """
    index = start
    if text[index] == '?':
        raise NotImplementedError("Doesn't support Python extension (?...)")
    regex = None
    while True:
        new_regex, index = _parse(text, index, "|)")
        if regex:
            regex = regex | new_regex
        else:
            regex = new_regex
        if len(text) <= index:
            raise SyntaxError('Missing closing parenthesis')
        if text[index] == ')':
            break
        index += 1
    index += 1
    if regex is None:
        regex = RegexEmpty()
    return regex, index


CHAR_TO_FUNC = {'[': parseRange, '(': parseOr}
CHAR_TO_CLASS = {'.': RegexDot, '^': RegexStart, '$': RegexEnd}
CHAR_TO_REPEAT = {'*': (0, None), '?': (0, 1), '+': (1, None)}
def _parse(text, start=0, until=None):
    if len(text) == start:
        return RegexEmpty(), 0
    index = start
    regex = RegexEmpty()
    last = None
    done = False
    while index < len(text):
        char = text[index]
        if until and char in until:
            done = True
            break
        if char in '.^$[](){}|+?*\\':
            if start != index:
                subtext = text[start:index]
                if last:
                    regex = regex + last
                last = RegexString(subtext)
            if char in CHAR_TO_FUNC:
                new_regex, index = CHAR_TO_FUNC[char] (text, index+1)
            elif char in CHAR_TO_CLASS:
                new_regex = CHAR_TO_CLASS[char]()
                index += 1
            elif char in CHAR_TO_REPEAT:
                rmin, rmax = CHAR_TO_REPEAT[char]
                new_regex = RegexRepeat(last, rmin, rmax)
                last = None
                index += 1
            else:
                raise NotImplementedError("Operator '%s' is not supported" % char)
            start = index
            if last:
                regex = regex + last
            last = new_regex
        else:
            index += 1
    if start != index:
        subtext = text[start:index]
        if last:
            regex = regex + last
        last = RegexString(subtext)
    if last:
        regex = regex + last
    return regex, index

def parse(text):
    r"""
    >>> parse('')
    <RegexEmpty ''>
    >>> parse('abc')
    <RegexString 'abc'>
    >>> parse('[bc]d')
    <RegexAnd '[b-c]d'>
    >>> parse('a(b|[cd]|(e|f))g')
    <RegexAnd 'a[b-f]g'>
    >>> parse('([a-z]|[b-])')
    <RegexRange '[a-z-]'>
    >>> parse('^^..$$')
    <RegexAnd '^..$'>
    >>> parse('(chien blanc|chat blanc)')
    <RegexAnd 'ch(ien|at) blanc'>
    """
    regex, index = _parse(text)
    assert index == len(text)
    return regex

if __name__ == "__main__":
    import doctest
    doctest.testmod()

