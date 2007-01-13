#!/usr/bin/env python
import sys

# TODO: decorator
# TODO: reversed

def checkBoolean():
    try:
        x = True
        x = False
    except:
        return "Don't support boolean (True, False)"
    return "ok"

def checkImportParenthesis():
    try:
        code = compile("from sys import (version, hexversion)", "", "exec")
    except SyntaxError:
        return "Import doesn't support parenthesis"
    return "ok"

def checkListGenerator():
    try:
        if eval("[ x*2 for x in range(3) ]") != [0, 2, 4]:
            return 0
    except SyntaxError:
        return "List generator doesn't work: [ x*2 for x in range(3) ]"
    return "ok"

def checkGenerator():
    try:
        if eval("list( (x*2 for x in range(3)) )") != [0, 2, 4]:
            return 0
    except SyntaxError:
        return "Creation of generator doesn't work: ( x*2 for x in range(3) )"
    return "ok"

def checkStruct():
    try:
        import struct
    except ImportError:
        return "Module struct is missing"

    try:
        # Copy/paste from hachoir_core.float
        assert struct.calcsize("f") == 4
        assert struct.calcsize("d") == 8
    except (AssertionError, struct.error):
        return "Wrong struct format size (SEND US A BUG REPORT PLEASE!)"

    try:
        # Copy/paste from hachoir_core.float
        assert struct.unpack("<d", "\x1f\x85\xebQ\xb8\x1e\t@")[0] == 3.14
        assert struct.unpack(">d", "\xc0\0\0\0\0\0\0\0")[0] == -2.0
    except (AssertionError, OverflowError):
        return "struct.unpack() error"
    return "ok"

def checkYield():
    try:
        eval(compile("""
from __future__ import generators

def gen():
    yield 0
    yield 2
    yield 4

if list(gen()) != [0, 2, 4]:
    raise KeyError("42")
""", "<string>", "exec"))
    except (KeyError, SyntaxError):
        return "Use yield in a function doesn't work"
    return "ok"

def checkUnicode():
    tests = (
        ('a', 'ASCII', 1),
        ('\xe9', 'ISO-8859-1', 1),
        ('\xc2\xae', 'UTF-8', 1),
        ('\xe9\x00', 'UTF-16-LE', 1),
        ('\x00\xe9', 'UTF-16-BE', 1),
    )
    for test in tests:
        data, charset, size = test
        try:
            if eval("len(unicode(data, charset))") != size:
                return 0
        except (SyntaxError, NameError):
            return "Unicode support is missing"
        except LookupError:
            return "Charset '%s' is not supported" % charset
        return "ok"

def checkCallFunctionArgs():
    try:
        eval(compile("""
def foo(*bar):
    return bar

if foo(0, 2, 4) != (0, 2, 4):
    raise KeyError("42")
""", "<string>", "exec"))
    except (KeyError, SyntaxError):
        return "Calling a function with foo(*bar) doesn't work"
    return "ok"

def checkIntLong():
    try:
        x = sys.maxint
        x = x * 8
    except OverflowError:
        return "Switch from int type to long is not automatic (sys.maxint*8)"
    return "ok"

def checkAddEqual():
    try:
        eval(compile("x=4; x += 1", "<string>", "exec"))
    except SyntaxError:
        return "Syntax x += y is not supported"
    return "ok"

def checkAll(verbose=0):
    """
    Check all Python features needed by Hachoir.
    Returns a list of error as string. If the list is empty, you're able to
    use Hachoir :-)
    """
    msg = []
    tests = (
        ("Types", (checkBoolean, checkUnicode, checkIntLong)),
        ("Syntax", (checkImportParenthesis, checkAddEqual, checkCallFunctionArgs)),
        ("Language feature", (checkListGenerator, checkYield, checkGenerator)),
        ("Modules", (checkStruct,)),
    )

    for group in tests:
        print "=== %s ===" % group[0]
        for test in group[1]:
            sys.stdout.write("%s(): " % test.__name__)
            sys.stdout.flush()
            result = test()
            print result
            if result != "ok":
                msg.append(result)
        print
    return msg

def main():
    print "Run tests."
    print
    result = checkAll(1)
    print "=== Results ==="
    for error in result:
        print "ERROR: %s" % error
    if not result:
        print "=> Ok, your Python interpreter can run Hachoir."
        sys.exit(0)
    else:
        print "=> You're NOT ABLE to run Hachoir!"
        sys.exit(1)

if __name__ == "__main__":
    main()

