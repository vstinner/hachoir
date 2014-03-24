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
    for code in range(128)
)

def makePrintable(data, charset, quote=None, smart=True):
    r"""
    Prepare a string to make it printable in the specified charset.
    It escapes control characters. Characters with codes bigger than 127
    are escaped if data type is 'str' or if charset is "ASCII".

    Examples with Unicode:

    >>> aged = "âgé"
    >>> repr(aged)  # text type is 'unicode'
    "'âgé'"
    >>> makePrintable("abc\0", "UTF-8")
    'abc\\0'
    >>> makePrintable(aged, "latin1")
    '\xe2g\xe9'
    >>> makePrintable(aged, "latin1", quote='"')
    '"\xe2g\xe9"'

    Examples with string encoded in latin1:

    >>> aged_latin = "âgé".encode("latin1")
    >>> repr(aged_latin)  # text type is 'str'
    "b'\\xe2g\\xe9'"
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
    >>> print(makePrintable("a\"b", "latin-1", quote='"'))
    "a\"b"
    >>> print(makePrintable("a\"b", "latin-1", quote="'"))
    'a"b'
    >>> print(makePrintable("a'b", "latin-1", quote="'"))
    'a\'b'
    """

    if data:
        if not isinstance(data, str):
            data = str(data, "ISO-8859-1")
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
        data = re.sub(br"\\x0([0-7])(?=[^0-7]|$)", br"\\\1", data)
    return str(data, charset)

