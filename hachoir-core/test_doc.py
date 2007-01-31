#!/usr/bin/env python2.4
import doctest
import sys
import os
import re
from stat import S_ISREG, ST_MODE
import hachoir_core.i18n   # import it because it does change the locale
from locale import setlocale, LC_ALL

regex_doc_filename = re.compile("^[a-z0-9_-]+\.txt$")

def testDoc(filename, name=None):
    print "--- %s: Run tests" % filename
    failure, nb_test = doctest.testfile(
        filename, optionflags=doctest.ELLIPSIS, name=name)
    if failure:
        sys.exit(1)
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
        sys.exit(1)
    print "--- End of test"

def main():
    setlocale(LC_ALL, "C")
    hachoir_dir = os.path.dirname(__file__)
    sys.path.append(hachoir_dir)

    # Configure Hachoir for tests
    import hachoir_core.config as config
    config.use_i18n = False

    # Test documentation in "doc/" subdirectory
    doc_dir = 'doc'
    documents = os.listdir(doc_dir)
    documents.sort()
    for doc in documents:
        filename = os.path.join(doc_dir, doc)
        if S_ISREG(os.stat(filename)[ST_MODE]) \
        and regex_doc_filename.match(doc) != None:
            testDoc(filename)

    # Test documentation of some functions/classes
    testModule("hachoir_core.bits")
    testModule("hachoir_core.compatibility")
    testModule("hachoir_core.dict")
    testModule("hachoir_core.text_handler")
    testModule("hachoir_core.tools")

if __name__ == "__main__":
    main()
