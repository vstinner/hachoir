from hachoir_core.field import FieldSet, Bits, Enum
from hachoir_core.text_handler import textHandler, hexadecimal
from hachoir_core.bits import str2hex
from hachoir_parser.network.ouid import REGISTERED_OUID

class OrganizationallyUniqueIdentifier(Bits):
    """
    IEEE 24-bit Organizationally unique identifier
    """
    static_size = 24

    def __init__(self, parent, name, description=None):
        Bits.__init__(self, parent, name, 24, description=None)

    def createValue(self):
        value = Bits.createValue(self)
        a = value & 0xFF
        b = (value >> 8) & 0xFF
        c = value >> 16
        return "%02X-%02X-%02X" % (a, b, c)

    def createDisplay(self, human=True):
        if human:
            key = Bits.createValue(self)
            if key in REGISTERED_OUID:
                return REGISTERED_OUID[key]
            else:
                return self.value
        else:
            return self.value

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

    def createDisplay(self):
        return "%s [%s]" % (self["organization"].display, self["nic"].display)

