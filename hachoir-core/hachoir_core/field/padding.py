from hachoir_core.field import Bits, Bytes
from hachoir_core.error import info, warning
from hachoir_core.tools import makePrintable, humanFilesize
from hachoir_core import config

class PaddingBits(Bits):
    """
    Padding bits used, for example, to align address (of next field).
    See also NullBits and PaddingBytes types.

    Arguments:
     * nbits: Size of the field in bits

    Optional arguments:
     * pattern (int): Content pattern, eg. 0 if all bits are set to 0
    """
    static_size = staticmethod(lambda *args, **kw: args[1])
    MAX_SIZE = 128

    def __init__(self, parent, name, nbits, description="Padding", pattern=None):
        Bits.__init__(self, parent, name, nbits, description)
        self.pattern = pattern
        self._display_pattern = self.checkPattern()

    def checkPattern(self):
        if not(config.check_padding_pattern):
            return False
        if self.pattern != 0:
            return False

        if self.MAX_SIZE < self._size:
            value = self._parent.stream.readBits(
                self.absolute_address, self.MAX_SIZE, self._parent.endian)
        else:
            value = self.value
        if value != 0:
            warning(
                "Warning: padding %s content doesn't look normal"
                " (invalid pattern)!" % self.path)
            return False
        if self.MAX_SIZE < self._size:
            info("Notice: only check first %u bits of %s" % (self.MAX_SIZE, self.path))
        return True

    def createDisplay(self):
        if self._display_pattern:
            return u"<padding pattern=%s>" % self.pattern
        else:
            return Bits.createDisplay(self)

class PaddingBytes(Bytes):
    """
    Padding bytes used, for example, to align address (of next field).
    See also NullBytes and PaddingBits types.

    Arguments:
     * nbytes: Size of the field in bytes

    Optional arguments:
     * pattern (str): Content pattern, eg. "\0" for nul bytes
    """

    static_size = staticmethod(lambda *args, **kw: args[1]*8)
    MAX_SIZE = 4096

    def __init__(self, parent, name, nbytes,
    description="Padding", pattern=None):
        """ pattern is None or repeated string """
        assert (pattern is None) or (isinstance(pattern, str))
        Bytes.__init__(self, parent, name, nbytes, description)
        self.pattern = pattern
        self._display_pattern = self.checkPattern()

    def checkPattern(self):
        if not(config.check_padding_pattern):
            return False
        if self.pattern is None:
            return False

        if self.MAX_SIZE < self._size/8:
            info("Notice: only check first %s of padding: %s"
                % (humanFilesize(self.MAX_SIZE), self.path))
            content = self._parent.stream.readBytes(
                self.absolute_address, self.MAX_SIZE)
        else:
            content = self.value
        index = 0
        pattern_len = len(self.pattern)
        while index < len(content):
            if content[index:index+pattern_len] != self.pattern:
                warning(
                    "Warning: padding %s content doesn't look normal"
                    " (invalid pattern at byte %u)!"
                    % (self.path, index))
                return False
            index += pattern_len
        return True

    def createDisplay(self):
        if self._display_pattern:
            return u"<padding pattern=%s>" % makePrintable(self.pattern, "ASCII", quote="'")
        else:
            return Bytes.createDisplay(self)

    def createRawDisplay(self):
        return Bytes.createDisplay(self)

class NullBits(PaddingBits):
    """
    Null padding bits used, for example, to align address (of next field).
    See also PaddingBits and NullBytes types.

    Arguments:
     * nbits: Size of the field in bits
    """

    def __init__(self, parent, name, nbits, description=None):
        PaddingBits.__init__(self, parent, name, nbits, description, pattern=0)

    def createDisplay(self):
        if self._display_pattern:
            return "<null>"
        else:
            return Bits.createDisplay(self)

class NullBytes(PaddingBytes):
    """
    Null padding bytes used, for example, to align address (of next field).
    See also PaddingBytes and NullBits types.

    Arguments:
     * nbytes: Size of the field in bytes
    """
    def __init__(self, parent, name, nbytes, description=None):
        PaddingBytes.__init__(self, parent, name, nbytes, description, pattern="\0")

    def createDisplay(self):
        if self._display_pattern:
            return "<null>"
        else:
            return Bytes.createDisplay(self)

