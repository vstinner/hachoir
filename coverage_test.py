"""
Run the maximum of tests to have good coverage test.
"""

import os
import imp

def main():
    directory = os.getenv("TESTCASE")
    if not directory:
        home = os.getenv("HOME")
        assert home
        directory = os.path.join(home, "testcase")

    parser = imp.load_source("parser", "hachoir-parser/tests/run_testcase.py")
    parser.testRandom()
    parser.testFiles(directory)

    metadata = imp.load_source("metadata", "hachoir-metadata/run_testcase.py")
    metadata.testFiles(directory)

#    core_doc = imp.load_source("parser", "hachoir-core/test_doc.py")
#    print "CORE=================================="
#    core_doc.testDoc("doc/hachoir-api.rst")
#    core_doc.testModule("hachoir_core.bits")
#    core_doc.testModule("hachoir_core.compatibility")
#    core_doc.testModule("hachoir_core.text_handler")
#    core_doc.importModule("hachoir_core.tools")
#    print "END CORE=================================="

if __name__ == "__main__":
    main()

