from regex import RegexAnd, RegexString, RegexRange, RegexEmpty, RegexOr
import re

def parse(text):
    r"""
    >>> parse('')
    <RegexEmpty>
    >>> parse('abc')
    <RegexString 'abc'>
    >>> parse('[bc]d')
    <RegexAnd '[bc]d'>
    >>> parse('a(b|[cd]|(e|f))g')
    <RegexAnd 'a(b|[cd]|e|f)g'>
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
        if char in '[({+?*':
            if start != index:
                subtext = text[start:index]
                regex = regex + RegexString(subtext)
            if char == '(':
                new_regex, index = parseOr(text, index+1)
            elif char == '[':
                new_regex, index = parseRange(text, index+1)
            else:
                raise NotImplementedError("Operator '%s' is not supported" % character)
            start = index
            regex = regex + new_regex
        else:
            index += 1
    if start != index:
        subtext = text[start:index]
        regex = regex + RegexString(subtext)
    return regex, index

# Match: a, a-z, a-z0-9, abc-d9
RANGE_REGEX = r"(?:[^]-]|.-[^]])+"
# Match: a], a-], a-z], a-z-], -]
RANGE_REGEX = r"(%s-?|-)]" % RANGE_REGEX
RANGE_REGEX = re.compile(r"(%s).*" % RANGE_REGEX)
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
        char_range.append(']')
        index += 1
    #match = re.match("^([^]-]+-?)\]", text, index)
    match = RANGE_REGEX.match(text, index)
    if not match:
        raise ValueError("Unable to parse regex range: %r" % text[index:])
    char_range.append( match.group(2) )
    index += len(match.group(1))
    return RegexRange(''.join(char_range), exclude), index

def parseOr(text, start):
    """
    >>> parseOr('(a)', 1)
    (<RegexString 'a'>, 3)
    >>> parseOr('(a|b)', 1)
    (<RegexOr '(a|b)'>, 5)
    >>> parseOr(' (a|[bc]|d)', 2)
    (<RegexOr '(a|[bc]|d)'>, 11)
    """
    index = start
    regex = RegexEmpty()
    while True:
        new_regex, index = _parse(text, index, "|)")
        regex = regex | new_regex
        if text[index] == ')':
            break
        index += 1
    index += 1
    return regex, index

if __name__ == "__main__":
    import doctest
    doctest.testmod()

