#!/usr/bin/env python3
import os.path
import subprocess
import sys
import tempfile
import textwrap
import unittest

from hachoir.test import setup_tests

SOURCE_DIR = os.path.dirname(os.path.dirname(__file__))
FILES_DIR = os.path.join(SOURCE_DIR, 'tests', 'files')


def run_hachoir_subfile(filename, directory=None):
    program = os.path.join(SOURCE_DIR, 'hachoir-subfile')
    cmd = [sys.executable, program, filename]
    if directory:
        cmd.append(directory)
    proc = subprocess.run(cmd,
                          text=True,
                          check=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc


class SubfileTests(unittest.TestCase):
    def test_subfile(self):
        filename = os.path.join(FILES_DIR, 'angle-bear-48x48.ani')
        proc = run_hachoir_subfile(filename)
        self.assertEqual(proc.stdout, textwrap.dedent(
            '''
            [+] Start search on 29658 bytes (29.0 KB)

            [+] File at 202 size=7358 (7358 bytes): Microsoft Windows icon: 48x48x0
            [+] File at 7568 size=7358 (7358 bytes): Microsoft Windows icon: 48x48x0
            [+] File at 14934 size=7358 (7358 bytes): Microsoft Windows icon: 48x48x0
            [+] File at 22300 size=7358 (7358 bytes): Microsoft Windows icon: 48x48x0

            [+] End of search -- offset=29658 (29.0 KB)
            '''
        ).strip() + '\n')

    def test_create_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(FILES_DIR, 'angle-bear-48x48.ani')
            run_hachoir_subfile(filename, tmpdir)
            files = sorted(os.listdir(tmpdir))
            expected = [
                'file-0001.ico',
                'file-0002.ico',
                'file-0003.ico',
                'file-0004.ico',
            ]
            self.assertEqual(files, expected)


if __name__ == "__main__":
    setup_tests()
    unittest.main()

