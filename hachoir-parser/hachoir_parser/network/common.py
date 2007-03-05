from hachoir_core.field import FieldSet, Bits
from hachoir_core.text_handler import textHandler, hexadecimal
from hachoir_core.bits import str2hex

class OrganizationallyUniqueIdentifier(Bits):
    """
    IEEE 24-bit Organizationally unique identifier
    """
    static_size = 24

    def __init__(self, parent, name, description=None):
        Bits.__init__(self, parent, name, 24, description=None)

    def createDisplay(self):
        value = self.value
        a = value & 0xFF
        b = (value >> 8) & 0xFF
        c = value >> 16
        return "%02X-%02X-%02X" % (a, b, c)

class MAC48_Address(FieldSet):
    """
    IEEE 802 48-bit MAC address
    """
    static_size = 48
    def createFields(self):
        yield OrganizationallyUniqueIdentifier(self, "organization")
        yield textHandler(Bits(self, "nic", 24), hexadecimal)

    def hasValue(self):
        return True

    def createValue(self):
        bytes = self.stream.readBytes(self.absolute_address, 6)
        return str2hex(bytes, format="%02x:")[:-1]

