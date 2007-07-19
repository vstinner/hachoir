#!/usr/bin/env python2.4
import doctest
import sys

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
    # Configure Hachoir for tests
    import hachoir_core.config as config
    config.use_i18n = False

    # Test documentation of some functions/classes
    testModule("hachoir_metadata.metadata")
    testModule("hachoir_metadata.setter")

if __name__ == "__main__":
    main()
