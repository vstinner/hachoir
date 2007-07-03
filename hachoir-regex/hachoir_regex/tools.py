# -*- coding: UTF-8 -*-
import re

regex_control_code = re.compile("([\x00-\x1f\x7f])")
controlchars = tuple({
        # Don't use "\0", because "\0"+"0"+"1" = "\001" = "\1" (1 character)
        # Same rease to not use octal syntax ("\1")
        ord("\n"): r"\n",
        ord("\r"): r"\r",
        ord("\t"): r"\t",
        ord("\a"): r"\a",
        ord("\b"): r"\b",
    }.get(code, '\\x%02x' % code)
    for code in xrange(128)
)

def makePrintable(data, charset, quote=None, to_unicode=False, smart=True):
    r"""
    Prepare a string to make it printable in the specified charset.
    It escapes control characters. Characters with codes bigger than 127
    are escaped if data type is 'str' or if charset is "ASCII".

    Examples with Unicode:
    >>> aged = unicode("âgé", "UTF-8")
    >>> repr(aged)  # text type is 'unicode'
    "u'\\xe2g\\xe9'"
    >>> makePrintable("abc\0", "UTF-8")
    'abc\\0'
    >>> makePrintable(aged, "latin1")
    '\xe2g\xe9'
    >>> makePrintable(aged, "latin1", quote='"')
    '"\xe2g\xe9"'

    Examples with string encoded in latin1:
    >>> aged_latin = unicode("âgé", "UTF-8").encode("latin1")
    >>> repr(aged_latin)  # text type is 'str'
    "'\\xe2g\\xe9'"
    >>> makePrintable(aged_latin, "latin1")
    '\\xe2g\\xe9'
    >>> makePrintable("", "latin1")
    ''
    >>> makePrintable("a", "latin1", quote='"')
    '"a"'
    >>> makePrintable("", "latin1", quote='"')
    '(empty)'
    >>> makePrintable("abc", "latin1", quote="'")
    "'abc'"

    Control codes:
    >>> makePrintable("\0\x03\x0a\x10 \x7f", "latin1")
    '\\0\\3\\n\\x10 \\x7f'

    Quote character may also be escaped (only ' and "):
    >>> print makePrintable("a\"b", "latin-1", quote='"')
    "a\"b"
    >>> print makePrintable("a\"b", "latin-1", quote="'")
    'a"b'
    >>> print makePrintable("a'b", "latin-1", quote="'")
    'a\'b'
    """

    if data:
        if not isinstance(data, unicode):
            data = unicode(data, "ISO-8859-1")
            charset = "ASCII"
        data = regex_control_code.sub(
            lambda regs: controlchars[ord(regs.group(1))], data)
        if quote:
            if quote in "\"'":
                data = data.replace(quote, '\\' + quote)
            data = ''.join((quote, data, quote))
    elif quote:
        data = "(empty)"
    data = data.encode(charset, "backslashreplace")
    if smart:
        # Replace \x00\x01 by \0\1
        data = re.sub(r"\\x0([0-7])(?=[^0-7]|$)", r"\\\1", data)
    if to_unicode:
        data = unicode(data, charset)
    return data

