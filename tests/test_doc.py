#!/usr/bin/env python3
import doctest
import sys
import os
import hachoir.core.i18n   # import it because it does change the locale

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

def testDoc(filename, name=None):
    print("--- %s: Run tests" % filename)
    fullpath = os.path.join('..', 'doc', filename)
    failure, nb_test = doctest.testfile(
        fullpath, optionflags=doctest.ELLIPSIS, name=name)
    if failure:
        sys.exit(1)
    print("--- %s: End of tests" % filename)

def importModule(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

def testModule(name):
    print("--- Test module %s" % name)
    module = importModule(name)
    failure, nb_test = doctest.testmod(module)
    if failure:
        sys.exit(1)
    print("--- End of test")

def main():
    # Test documentation in doc/*.rst files
    testDoc('api.rst')
    testDoc('internals.rst')

    # Test documentation of some functions/classes
    testModule("hachoir.core.bits")
    testModule("hachoir.core.dict")
    testModule("hachoir.core.i18n")
    testModule("hachoir.core.text_handler")
    testModule("hachoir.core.tools")

    # Test documentation of some functions/classes
    testModule("hachoir.metadata.metadata")
    testModule("hachoir.metadata.setter")

if __name__ == "__main__":
    from locale import setlocale, LC_ALL
    setlocale(LC_ALL, "C")

    sys.path.append(ROOT)

    # Configure Hachoir for tests
    import hachoir.core.config as config
    config.use_i18n = False

    main()
