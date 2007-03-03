#!/usr/bin/env python
import doctest
import sys

def testmod(modname):
    print "--- test module %s ---" % modname
    mod = __import__(modname)
    failure, nb_test = doctest.testmod(mod)
    if failure:
        sys.exit(1)

def testdoc(filename):
    print "--- test documentation %s ---" % filename
    failure, nb_test = doctest.testfile(
        filename, optionflags=doctest.ELLIPSIS)
    if failure:
        sys.exit(1)

def main():
    testmod("regex")
    testmod("parser")
    testdoc("doc.rst")

if __name__ == "__main__":
    main()

