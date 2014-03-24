#!/usr/bin/env python3
import sys
import os.path
from locale import setlocale, LC_ALL

TESTCASE = 'testcase'

def main():
    setlocale(LC_ALL, "C")

    # Configure Hachoir for tests
    import hachoir.core.config as config
    config.use_i18n = False

    print("=== hachoir-core: test doc ===")
    import tests.test_doc
    tests.test_doc.main()

    print("=== download and check testcase ===")
    import tests.download_testcase
    tests.download_testcase.main(TESTCASE)

    print("=== hachoir-parser: testcase ===")
    import tests.run_testcase
    tests.run_testcase.main(TESTCASE)

    print("=== hachoir-metadata: testcase ===")
    import tests.run_testcase_metadata
    tests.run_testcase_metadata.main(TESTCASE)

    #print("=== hachoir-regex: tests ===")
    #$PYTHON $ROOT/hachoir-regex/test_doc.py

if __name__ == "__main__":
    main()

