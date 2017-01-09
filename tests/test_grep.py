#!/usr/bin/env python3
from hachoir.grep import Grep
from hachoir.parser import createParser
from hachoir.test import setup_tests
import os.path
import subprocess
import sys
import unittest

DATADIR = os.path.join(os.path.dirname(__file__), "files")
GEORGIA_CAB = os.path.join(DATADIR, 'georgia.cab')
PROGRAM = os.path.join(os.path.dirname(__file__), "..", "hachoir-grep")


class TestGrepClass(unittest.TestCase):

    def test_grep(self):
        fields = []

        class TestGrep(Grep):

            def onMatch(self, field):
                fields.append(field)

        parser = createParser(GEORGIA_CAB)
        with parser:
            grep = TestGrep()
            grep.grep(parser)
        fields = [(field.absolute_address, field.path, field.value)
                  for field in fields]
        self.assertEqual(fields,
                         [(0, '/magic', 'MSCF'),
                          (480, '/file[0]/filename', 'fontinst.inf'),
                             (712, '/file[1]/filename', 'Georgiaz.TTF'),
                             (944, '/file[2]/filename', 'Georgiab.TTF'),
                             (1176, '/file[3]/filename', 'Georgiai.TTF'),
                             (1408, '/file[4]/filename', 'Georgia.TTF'),
                             (1632, '/file[5]/filename', 'fontinst.exe')])


class TestGrepCommandLine(unittest.TestCase):

    def test_grep(self):
        args = [sys.executable, PROGRAM, "--all", "--path", GEORGIA_CAB]
        proc = subprocess.Popen(args,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        stdout, _ = proc.communicate()
        stdout = stdout.decode('ascii', 'replace')
        self.assertEqual(stdout, """
0:/magic:MSCF
60:/file[0]/filename:fontinst.inf
89:/file[1]/filename:Georgiaz.TTF
118:/file[2]/filename:Georgiab.TTF
147:/file[3]/filename:Georgiai.TTF
176:/file[4]/filename:Georgia.TTF
204:/file[5]/filename:fontinst.exe
""".lstrip())


if __name__ == "__main__":
    setup_tests()
    unittest.main()
