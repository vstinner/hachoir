#!/usr/bin/env python3
from hachoir.test import setup_tests
import hashlib
import os.path
import subprocess
import sys
import unittest

DATADIR = os.path.join(os.path.dirname(__file__), "files")
KDE_CLICK = os.path.join(DATADIR, 'kde_click.wav')
PROGRAM = os.path.join(os.path.dirname(__file__), "..", "hachoir-strip")


def checksum(filename):
    hash = hashlib.sha1()
    with open(filename, 'rb') as fp:
        chunk = fp.read(4096)
        hash.update(chunk)
    return hash.hexdigest()


class TestStripCommandLine(unittest.TestCase):

    def test_strip_all(self):
        self.assertEqual(checksum(KDE_CLICK),
                         'dcafdef2048985aa925df5f86053bda5a87eb64b')

        newname = KDE_CLICK + ".new"
        if os.path.exists(newname):
            os.unlink(newname)

        args = [sys.executable, PROGRAM, KDE_CLICK]
        proc = subprocess.Popen(args,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        stdout, _ = proc.communicate()
        stdout = stdout.decode('ascii', 'replace')
        self.assertIn('Save new file', stdout)

        self.assertEqual(checksum(newname),
                         '6456990d3931292a1c96c6e8f035e983cd84d477')

        os.unlink(newname)


if __name__ == "__main__":
    setup_tests()
    unittest.main()
