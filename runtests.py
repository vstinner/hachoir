#!/usr/bin/env python3
import sys
import os.path
from locale import setlocale, LC_ALL

def main():
    setlocale(LC_ALL, "C")

    # Configure Hachoir for tests
    import hachoir.core.config as config
    config.use_i18n = False

    print("=== hachoir-core: test doc ===")
    import tests.test_doc
    tests.test_doc.main()

    print("=== hachoir-parser: testcase ===")
    import tests.run_testcase
    tests.run_testcase.main()

    print("=== hachoir-metadata: testcase ===")
    import tests.run_testcase_metadata
    tests.run_testcase_metadata.main()

if __name__ == "__main__":
    main()

