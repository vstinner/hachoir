from hachoir_core.error import HachoirError
from hachoir_core.field import joinPath, MissingField

class EditorError(HachoirError):
    pass

class FakeField(object):
    """
    This class have API looks similar to Field API, but objects don't contain
    any value: all values are _computed_ by parent methods.

    Example: FakeField(editor, "abc").size calls editor._getFieldSize("abc").
    """
    is_field_set = False

    def __init__(self, parent, name):
        self._parent = parent
        self._name = name

    def _getPath(self):
        return joinPath(self._parent.path, self._name)
    path = property(_getPath)

    def _getName(self):
        return self._name
    name = property(_getName)

    def _getAddress(self):
        return self._parent._getFieldAddress(self._name)
    address = property(_getAddress)

    def _getSize(self):
        return self._parent.input[self._name].size
    size = property(_getSize)

    def _getValue(self):
        return self._parent.input[self._name].value
    value = property(_getValue)

    def createDisplay(self):
        # TODO: Returns new value if field is altered
        return self._parent.input[self._name].display
    display = property(createDisplay)

    def _getParent(self):
        return self._parent
    parent = property(_getParent)

    def hasValue(self):
        return self._parent.input[self._name].hasValue()

    def __getitem__(self, key):
        # TODO: Implement this function!
        raise MissingField(self, key)

    def _isAltered(self):
        return False
    is_altered = property(_isAltered)

    def writeInto(self, output):
        size = self.size
        addr = self._parent._getFieldInputAddress(self._name)
        input = self._parent.input
        stream = input.stream
        if size % 8:
            output.copyBitsFrom(stream, addr, size, input.endian)
        else:
            output.copyBytesFrom(stream, addr, size//8)

