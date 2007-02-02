from hachoir_core.field import (
    RawBits, Bit, Bits, PaddingBits,
    RawBytes, Bytes, PaddingBytes,
    GenericString, Character,
    isInteger, isString)
from hachoir_editor import FakeField

class EditableField(FakeField):
    """
    Pure virtual class used to write editable field class.
    """

    _is_altered = False
    def __init__(self, parent, name, value=None):
        FakeField.__init__(self, parent, name)
        self._value = value

    def _isAltered(self):
        return self._is_altered
    is_altered = property(_isAltered)

    def hasValue(self):
        return True

    def _computeSize(self):
        raise NotImplementedError()
    def _getValue(self):
        return self._value
    def _setValue(self, value):
        self._value = value

    def _propGetValue(self):
        if self._value is not None:
            return self._getValue()
        else:
            return FakeField._getValue(self)
    def _propSetValue(self, value):
        self._setValue(value)
        self._is_altered = True
    value = property(_propGetValue, _propSetValue)

    def _getSize(self):
        if self._value is not None:
            return self._computeSize()
        else:
            return FakeField._getSize(self)
    size = property(_getSize)

    def _write(self, output):
        raise NotImplementedError()

    def writeInto(self, output):
        if self._is_altered:
            self._write(output)
        else:
            return FakeField.writeInto(self, output)

class EditableFixedField(EditableField):
    """
    Editable field with fixed size.
    """

    def __init__(self, parent, name, value=None, size=None):
        EditableField.__init__(self, parent, name, value)
        if size is not None:
            self._size = size
        else:
            self._size = self._parent._getOriginalField(self._name).size

    def _getSize(self):
        return self._size
    size = property(_getSize)

class EditableBits(EditableFixedField):
    def __init__(self, parent, name, *args):
        if args:
            if len(args) != 2:
                raise TypeError(
                    "Wrong argument count, EditableBits constructor prototype is: "
                    "(parent, name, [size, value])")
            size = args[0]
            value = args[1]
            assert isinstance(value, (int, long))
        else:
            size = None
            value = None
        EditableFixedField.__init__(self, parent, name, value, size)
        if args:
            self._setValue(args[1])
            self._is_altered = True

    def _setValue(self, value):
        if not(0 <= value < (1 << self._size)):
            raise ValueError("Invalid value, must be in range %s..%s"
                % (0, (1 << self._size) - 1))
        self._value = value

    def _write(self, output):
        output.writeBits(self._size, self._value, self._parent.endian)

class EditableBytes(EditableField):
    def _setValue(self, value):
        if not value: raise ValueError(
            "Unable to set empty string to a EditableBytes field")
        self._value = value

    def _computeSize(self):
        return len(self._value) * 8

    def _write(self, output):
        output.writeBytes(self._value)

class EditableString(EditableField):
    MAX_SIZE = {
        "Pascal8": (1 << 8)-1,
        "Pascal16": (1 << 16)-1,
        "Pascal32": (1 << 32)-1,
    }

    def __init__(self, parent, name, *args, **kw):
        if len(args) == 2:
            value = args[1]
            assert isinstance(value, str)  # TODO: support Unicode
        elif not args:
            value = None
        else:
            raise TypeError(
                "Wrong argument count, EditableString constructor prototype is:"
                "(parent, name, [format, value])")
        EditableField.__init__(self, parent, name, value)
        if len(args) == 2:
            self._charset = kw.get('charset', None)
            self._format = args[0]
            if self._format in GenericString.PASCAL_FORMATS:
                self._prefix_size = GenericString.PASCAL_FORMATS[self._format]
            else:
                self._prefix_size = 0
            self._suffix_str = GenericString.staticSuffixStr(
                self._format, self._charset, self._parent.endian)
            self._is_altered = True
        else:
            orig = self._parent._getOriginalField(name)
            self._charset = orig.charset
            self._format = orig.format
            self._prefix_size = orig.content_offset
            self._suffix_str = orig.suffix_str

    def _setValue(self, value):
        size = len(value)
        if self._format in self.MAX_SIZE and self.MAX_SIZE[self._format] < size:
            raise ValueError("String is too big")
        self._value = value

    def _computeSize(self):
        return (self._prefix_size + len(self._value) + len(self._suffix_str))*8

    def _write(self, output):
        if self._format in GenericString.SUFFIX_FORMAT:
            output.writeBytes(self._value)
            output.writeBytes(self._suffix_str)
        elif self._format == "fixed":
            output.writeBytes(self._value)
        else:
            assert self._format in GenericString.PASCAL_FORMATS
            size = GenericString.PASCAL_FORMATS[self._format]
            output.writeInteger(len(self._value), False, size, self._parent.endian)
            output.writeBytes(self._value)

class EditableCharacter(EditableFixedField):
    def __init__(self, parent, name, *args):
        if args:
            if len(args) != 3:
                raise TypeError(
                    "Wrong argument count, EditableCharacter "
                    "constructor prototype is: (parent, name, [value])")
            value = args[0]
            if not isinstance(value, str) or len(value) != 1:
                raise TypeError("EditableCharacter needs a character")
        else:
            value = None
        EditableFixedField.__init__(self, parent, name, value, 8)
        if args:
            self._is_altered = True

    def _setValue(self, value):
        if not isinstance(value, str) or len(value) != 1:
            raise TypeError("EditableCharacter needs a character")
        self._value = value

    def _write(self, output):
        output.writeBytes(self._value)

class EditableInteger(EditableFixedField):
    VALID_VALUE_SIGNED = {
        8: (-(1 << 8), (1 << 8)-1),
        16: (-(1 << 15), (1 << 15)-1),
        32: (-(1 << 31), (1 << 31)-1),
    }
    VALID_VALUE_UNSIGNED = {
        8: (0, (1 << 8)-1),
        16: (0, (1 << 16)-1),
        32: (0, (1 << 32)-1)
    }

    def __init__(self, parent, name, *args):
        if args:
            if len(args) != 3:
                raise TypeError(
                    "Wrong argument count, EditableInteger constructor prototype is: "
                    "(parent, name, [signed, size, value])")
            size = args[1]
            value = args[2]
            assert isinstance(value, (int, long))
        else:
            size = None
            value = None
        EditableFixedField.__init__(self, parent, name, value, size)
        if args:
            self._signed = args[0]
            self._is_altered = True
        else:
            self._signed = self._parent._getOriginalField(self._name).signed

    def _setValue(self, value):
        if self._signed:
            valid = self.VALID_VALUE_SIGNED
        else:
            valid = self.VALID_VALUE_UNSIGNED
        minval, maxval = valid[self._size]
        if not(minval <= value <= maxval):
            raise ValueError("Invalid value, must be in range %s..%s"
                % (minval, maxval))
        self._value = value

    def _write(self, output):
        output.writeInteger(
            self.value, self._signed, self._size//8, self._parent.endian)

def createEditableField(fieldset, field):
    if isInteger(field):
        cls = EditableInteger
    elif isString(field):
        cls = EditableString
    elif field.__class__ in (RawBytes, Bytes, PaddingBytes):
        cls = EditableBytes
    elif field.__class__ in (RawBits, Bits, Bit, PaddingBits):
        cls = EditableBits
    elif field.__class__ == Character:
        cls = EditableCharacter
    else:
        cls = FakeField
    return cls(fieldset, field.name)

