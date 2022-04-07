#!/usr/bin/env python3
"""
Test the ability for parsers to extract or transform inputs.
"""

import hashlib
import os
import sys
import unittest
from io import BytesIO

from hachoir.parser import createParser, guessParser
from hachoir.test import setup_tests

DATADIR = os.path.join(os.path.dirname(__file__), "files")


@unittest.skipUnless(os.environ.get("SLOW_TESTS") == "1", "skipping slow tests")
class TestParserDecompression(unittest.TestCase):
    verbose = False

    def parse(self, filename):
        if self.verbose:
            print("[+] Test %s:" % filename)
            sys.stdout.write("  - Create parser: ")
            sys.stdout.flush()

        fullname = os.path.join(DATADIR, filename)
        parser = createParser(fullname)
        if not parser:
            self.fail("unable to create parser")
        self.addCleanup(parser.close)

        if self.verbose:
            sys.stdout.write("ok\n")
        return parser

    def checkCabExtract(self, cab, expected):
        # request substream to force generation of uncompressed_data
        cab["folder_data[0]"].getSubIStream()
        folder_data = BytesIO(cab["folder_data[0]"].uncompressed_data)
        cab_filenames = {file["filename"].value for file in cab.array("file")}
        self.assertEqual(cab_filenames, set(expected))

        for file in cab.array("file"):
            data = folder_data.read(file["filesize"].value)
            data_hash = hashlib.sha256(data).hexdigest()
            self.assertEqual(data_hash, expected[file["filename"].value])

    def test_cab_extract(self):
        parser = self.parse("georgia.cab")
        self.checkCabExtract(
            parser,
            {
                "Georgia.TTF": "7d0bb20c632bb59e81a0885f573bd2173f71f73204de9058feb68ce032227072",
                "Georgiab.TTF": "82d2fbadb88a8632d7f2e8ad50420c9fd2e7d3cbc0e90b04890213a711b34b93",
                "Georgiai.TTF": "1523f19bda6acca42c47c50da719a12dd34f85cc2606e6a5af15a7728b377b60",
                "Georgiaz.TTF": "c983e037d8e4e694dd0fb0ba2e625bca317d67a41da2dc81e46a374e53d0ec8a",
                "fontinst.exe": "4d9becb13049c035613353b1a08b35a1f0d3ca7bf552ca143039d16227b5b148",
                "fontinst.inf": "9771af4d96baa10f97ea4a322c6e827df13f45452db6e5ef1c83128a64c53646",
            },
        )

    def test_exe_extract(self):
        exe = self.parse("verdan32.exe")
        rsrc = exe["section_rsrc"]

        for content in rsrc.array("raw_res"):
            # get directory[][][] and corresponding name
            # this is a bit hacky, ideally API would provide this linkage directly
            directory = content.entry.inode.parent
            name_field = directory.name.replace("directory", "name")
            if name_field in rsrc and rsrc[name_field].value == "CABINET":
                break
        else:
            self.fail("No CABINET raw_res found")

        cabdata = content.getSubIStream()
        cab = guessParser(cabdata)
        self.checkCabExtract(
            cab,
            {
                "Verdana.TTF": "96ed14949ca4b7392cff235b9c41d55c125382abbe0c0d3c2b9dd66897cae0cb",
                "Verdanab.TTF": "c8f5065ba91680f596af3b0378e2c3e713b95a523be3d56ae185ca2b8f5f0b23",
                "Verdanai.TTF": "91b59186656f52972531a11433c866fd56e62ec4e61e2621a2dba70c8f19a828",
                "Verdanaz.TTF": "698e220f48f4a40e77af7eb34958c8fd02f1e18c3ba3f365d93bfa2ed4474c80",
                "fontinst.exe": "4d9becb13049c035613353b1a08b35a1f0d3ca7bf552ca143039d16227b5b148",
                "fontinst.inf": "632da3565f2d72071100aa6400b254db851659ec0d46c79b8ee19fb19dc99284",
            },
        )


if __name__ == "__main__":
    setup_tests()
    unittest.main()
