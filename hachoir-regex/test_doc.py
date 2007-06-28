#!/usr/bin/python
import doctest
from sys import exit

def testDoc(filename, name=None):
    print "--- %s: Run tests" % filename
    failure, nb_test = doctest.testfile(
        filename, optionflags=doctest.ELLIPSIS, name=name)
    if failure:
        exit(1)
    print "--- %s: End of tests" % filename

def importModule(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

def testModule(name):
    print "--- Test module %s" % name
    module = importModule(name)
    failure, nb_test = doctest.testmod(module)
    if failure:
        exit(1)
    print "--- End of test"

def main():
    # Test documentation in doc/*.rst files
    testDoc('README')
    testDoc('regex.rst')
    testDoc('regression.rst')

    # Test documentation of some functions/classes
    testModule("hachoir_regex.compatibility")
    testModule("hachoir_regex.tools")
    testModule("hachoir_regex.parser")
    testModule("hachoir_regex.regex")
    testModule("hachoir_regex.pattern")

if __name__ == "__main__":
    main()
