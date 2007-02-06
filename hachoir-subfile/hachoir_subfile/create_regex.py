from hachoir_core.regex import createString, RegexOr, RegexAnd
from hachoir_core.tools import makePrintable

def dumpRegex(regex, indent="", indentmore=" "):
    cls = regex.__class__
    if cls in (RegexOr, ): # RegexAnd):
        print "%s(" % indent
        newindent = " "*len(indent)
        if cls == RegexOr:
            newindent += "|"
        else:
            newindent += "&"
        newindent += indentmore
        for item in regex.content:
            dumpRegex(item, newindent, indentmore)
        print "%s)" % indent
    else:
        text = makePrintable(str(regex), 'ASCII')
        print "%s%s" % (indent, text)

def createRegex(patterns):
    r"""
    Create fast regex to match all strings of 'patterns' list.
    """
#
#    >>> print createRegex(["func(b)"])
#    func\(b\)
#    >>> print createRegex(["a", "b"])
#    [a-b]
#    >>> print createRegex(["aa", "bb"])
#    (?:aa|bb)
#    >>> print createRegex(["name0", "name1"])
#    name[0-1]
#    >>> print createRegex(["name1201", "name1001", "name1202"])
#    name1(?:[20]01|202)
#    >>> print createRegex([".exe", ".ico"])
#    \.(?:exe|ico)
#
    return RegexOr.join( createString(item) for item in patterns )

if __name__ == "__main__":
    import doctest
    doctest.testmod()

