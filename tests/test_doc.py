#!/usr/bin/env python3
import doctest
import hachoir.core.i18n   # import it because it does change the locale
import os
import sys
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

def importModule(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

class TestDoc(unittest.TestCase):
    def check_doc(self, filename, subdir=None, name=None, verbose=False):
        if verbose:
            print("--- %s: Run tests" % filename)
        if not subdir:
            fullpath = os.path.join('..', 'doc', filename)
        else:
            fullpath = os.path.join(subdir, filename)
        failure, nb_test = doctest.testfile(
            fullpath, optionflags=doctest.ELLIPSIS, name=name)
        if failure:
            self.fail("error")
        if verbose:
            print("--- %s: End of tests" % filename)

    def check_module(self, name, verbose=False):
        if verbose:
            print("--- Test module %s" % name)
        module = importModule(name)
        failure, nb_test = doctest.testmod(module)
        if failure:
            self.fail("error")
        if verbose:
            print("--- End of test")

    def test_doc_directory(self):
        self.check_doc('api.rst')
        self.check_doc('internals.rst')
        self.check_doc('regex_api.rst')

    def test_tests_directory(self):
        self.check_doc('regex_regression.rst', subdir='.')

    def test_modules(self):
        self.check_module("hachoir.core.bits")
        self.check_module("hachoir.core.dict")
        self.check_module("hachoir.core.i18n")
        self.check_module("hachoir.core.text_handler")
        self.check_module("hachoir.core.tools")

        self.check_module("hachoir.metadata.metadata")
        self.check_module("hachoir.metadata.setter")

        self.check_module("hachoir.regex.parser")
        self.check_module("hachoir.regex.regex")
        self.check_module("hachoir.regex.pattern")

if __name__ == "__main__":
    from locale import setlocale, LC_ALL
    setlocale(LC_ALL, "C")

    sys.path.append(ROOT)

    # Configure Hachoir for tests
    import hachoir.core.config as config
    config.use_i18n = False

    unittest.main()
