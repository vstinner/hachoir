"""
Character field class: a 8-bit character
"""

from hachoir.field import Bits
from hachoir.core.endian import BIG_ENDIAN
from hachoir.core.tools import makePrintable


class Character(Bits):
    """
    A 8-bit character using ASCII charset for display attribute.
    """
    static_size = 8

    def __init__(self, parent, name, description=None):
        Bits.__init__(self, parent, name, 8, description=description)

    def createValue(self):
        return chr(self._parent.stream.readBits(
            self.absolute_address, 8, BIG_ENDIAN))

    def createRawDisplay(self):
        return str(Bits.createValue(self))

    def createDisplay(self):
        return makePrintable(self.value, "ASCII", quote="'")
