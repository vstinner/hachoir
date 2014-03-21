#!/usr/bin/env python3
import doctest
import sys
import os
import hachoir.core.i18n   # import it because it does change the locale
from locale import setlocale, LC_ALL

def testDoc(filename, name=None):
    print("--- %s: Run tests" % filename)
    failure, nb_test = doctest.testfile(
        filename, optionflags=doctest.ELLIPSIS, name=name)
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
    setlocale(LC_ALL, "C")
    hachoir_dir = os.path.dirname(__file__)
    sys.path.append(hachoir_dir)

    # Configure Hachoir for tests
    import hachoir.core.config as config
    config.use_i18n = False

    # Test documentation in doc/*.rst files
    testDoc('doc/api.rst')
    testDoc('doc/internals.rst')

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
    main()
