import unittest
from io import BytesIO
from hachoir.core.endian import BIG_ENDIAN
from hachoir.editor import createEditor
from hachoir.field import Parser, Bits
from hachoir.stream import StringInputStream, OutputStream
from hachoir.test import setup_tests


class TestEditor(unittest.TestCase):
    def test_bit_alignment(self):
        data = bytes([255, 255, 255, 254])
        stream = StringInputStream(data)
        parser = TestParser(stream)
        editor = createEditor(parser)

        # Cause a change in a non-byte-aligned field
        editor['flags[2]'].value -= 1

        # Generate output and verify operation
        output_io = BytesIO()
        output_stream = OutputStream(output_io)

        editor.writeInto(output_stream)
        output_bits = "{0:b}".format(int.from_bytes(output_io.getvalue(), 'big'))

        # X is the modified bit
        #                              .....,,,,,,,,,,,,,,,,..X,,,,,,,,
        self.assertEqual(output_bits, "11111111111111111111111011111110")


class TestParser(Parser):
    endian = BIG_ENDIAN

    def createFields(self):
        yield Bits(self, 'flags[]', 5)
        yield Bits(self, 'flags[]', 16)
        yield Bits(self, 'flags[]', 3)
        yield Bits(self, 'flags[]', 8)


if __name__ == "__main__":
    setup_tests()
    unittest.main()
