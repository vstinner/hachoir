"""
Run the maximum of tests to have good coverage test.
"""

import os
import imp

def main():
    import doctest, pdb
    if doctest._OutputRedirectingPdb.set_trace == pdb.Pdb.set_trace:
        raise ImportError("Your doctest version is too old")

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

    core_doc = imp.load_source("parser", "hachoir-core/test_doc.py")
    core_doc.main()

    metadata_doc = imp.load_source("parser", "hachoir-metadata/test_doc.py")
    metadata_doc.main()

if __name__ == "__main__":
    main()

