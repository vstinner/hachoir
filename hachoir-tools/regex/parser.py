"""
Parse string to create Regex object.

TODO:
 - Support ^ and $
 - Support \: \001, \x00, \0, \ \[, \(, \{, etc.
 - Support Python extensions: (?:...), (?P<name>...), etc.
 - Support \<, \>, \s, \S, \w, \W, \Z <=> $, \d, \D, \A <=> ^, \b, \B, [[:space:]], etc.
"""

from regex import (RegexString, RegexEmpty, RegexDot,
    RegexRange, RegexRangeItem, RegexRangeCharacter)

def parse(text):
    r"""
    >>> parse('')
    <RegexEmpty>
    >>> parse('abc')
    <RegexString 'abc'>
    >>> parse('[bc]d')
    <RegexAnd '[b-c]d'>
    >>> parse('a(b|[cd]|(e|f))g')
    <RegexAnd 'a[b-f]g'>
    >>> parse('.')
    <RegexDot '.'>
    >>> parse('([a-z]|[b-])')
    <RegexRange '[a-z-]'>
    """
    regex, index = _parse(text)
    assert index == len(text)
    return regex

def _parse(text, start=0, until=None):
    if len(text) == start:
        return RegexEmpty(), 0
    index = start
    regex = RegexEmpty()
    done = False
    while index < len(text):
        char = text[index]
        if until and char in until:
            done = True
            break
        if char in '.^$[](){}|+?*\\':
            if start != index:
                subtext = text[start:index]
                regex = regex + RegexString(subtext)
            if char == '(':
                new_regex, index = parseOr(text, index+1)
            elif char == '[':
                new_regex, index = parseRange(text, index+1)
            elif char == '.':
                new_regex = RegexDot()
                index += 1
            else:
                raise NotImplementedError("Operator '%s' is not supported" % char)
            start = index
            regex = regex + new_regex
        else:
            index += 1
    if start != index:
        subtext = text[start:index]
        regex = regex + RegexString(subtext)
    return regex, index

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

if __name__ == "__main__":
    import doctest
    doctest.testmod()

