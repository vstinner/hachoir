"""
Parent of all (field) classes in Hachoir: Field.
"""

from hachoir_core.compatibility import reversed
from hachoir_core.stream import InputFieldStream
from hachoir_core.error import HachoirError, HACHOIR_ERRORS, error
from hachoir_core.tools import makePrintable
from weakref import ref as weakref_ref

class FieldError(HachoirError):
    """
    Error raised by a L{Field}.

    @see: L{HachoirError}
    """
    pass

def joinPath(path, name):
    if path != "/":
        return "/".join((path, name))
    else:
        return "/%s" % name

class MissingField(KeyError, FieldError):
    def __init__(self, field, key):
        KeyError.__init__(self)
        self.field = field
        self.key = key

    def __str__(self):
        return 'Can\'t get field "%s" from %s' % (self.key, self.field.path)

    def __unicode__(self):
        return u'Can\'t get field "%s" from %s' % (self.key, self.field.path)

class Field(object):
    # static size can have two differents value: None (no static size), an
    # integer (number of bits), or a function which returns an integer.
    #
    # This function receives exactly the same arguments than the constructor
    # except the first one (one). Example of function:
    #    static_size = staticmethod(lambda *args, **kw: args[1])
    static_size = None

    # Indicate if this field contains other fields (is a field set) or not
    is_field_set = False

    _value = None

    def __init__(self, parent, name, size=None, description=None):
        """
        Set default class attributes, set right address if None address is
        given.

        @param parent: Parent field of this field
        @type parent: L{Field}|None
        @param name: Name of the field, have to be unique in parent. If it ends
            with "[]", end will be replaced with "[new_id]" (eg. "raw[]"
            becomes "raw[0]", next will be "raw[1]", and then "raw[2]", etc.)
        @type name: str
        @param size: Size of the field in bit (can be None, so it
            will be computed later)
        @type size: int|None
        @param address: Address in bit relative to the parent absolute address
        @type address: int|None
        @param description: Optional string description
        @type description: str|None
        """
        assert issubclass(parent.__class__, Field)
        assert (size is None) or (0 <= size)
        self._parent = parent
        self._name = name
        self._address = parent._current_size
        self._size = size
        self._description = description

    def createDescription(self):
        return ""
    def _getDescription(self):
        if self._description is None:
            try:
                self._description = self.createDescription()
                if isinstance(self._description, str):
                    self._description = makePrintable(
                        self._description, "ISO-8859-1", to_unicode=True)
            except HACHOIR_ERRORS, err:
                error("Error getting description of %s: %s"
                    % (self.path, unicode(err)))
                self._description = ""
        return self._description
    description = property(_getDescription,
    doc="Description of the field (string)")

    def __str__(self):
        return self.display
    def __unicode__(self):
        return self.display
    def __repr__(self):
        return self.raw_display

    def hasValue(self):
        return hasattr(self, "createValue")
    def _getValue(self):
        if self._value is None:
            if not hasattr(self, "createValue"):
                raise AttributeError("Field %s has no attribute 'value'" % self.path)
            self._value = self.createValue()
        return self._value
    value = property(_getValue, "Value of field")

    def _getParent(self):
        return self._parent
    parent = property(_getParent, doc="Parent of this field")

    def createDisplay(self):
        return unicode(self.value)
    display = property(lambda self: self.createDisplay(),
    doc="Short (unicode) string which represents field content")

    def createRawDisplay(self):
        value = self.value
        if isinstance(value, str):
            return makePrintable(value, "ISO-8859-1", to_unicode=True)
        else:
            return unicode(value)
    raw_display = property(lambda self: self.createRawDisplay(),
    doc="(Unicode) string which represents raw field content")

    def _getName(self):
        return self._name
    name = property(_getName,
    doc="Field name (unique in its parent field set list)")

    def _getIndex(self):
        if not self._parent:
            return None
        return self._parent._fields.index(self._name)
    index = property(_getIndex)

    def _getPath(self):
        names = []
        field = self
        while field:
            names.append(field._name)
            field = field._parent
        names[-1] = ''
        return '/'.join(reversed(names))
    path = property(_getPath,
    doc="Full path of the field starting at root field")

    def _getAddress(self):
        return self._address
    address = property(_getAddress,
    doc="Relative address in bit to parent address")

    def _getAbsoluteAddress(self):
        address = self._address
        current = self._parent
        while current:
            address += current._address
            current = current._parent
        return address
    absolute_address = property(_getAbsoluteAddress,
    doc="Absolute address (from stream beginning) in bit")

    def _getSize(self):
        return self._size
    size = property(_getSize, doc="Content size in bit")

    def _getField(self, name, const):
        if name.strip("."):
            return None
        field = self
        for index in xrange(1, len(name)):
            field = field._parent
            if field is None:
                break
        return field

    def getField(self, key, const=True):
        if key:
            if key[0] == "/":
                if self._parent:
                    current = self._parent.root
                else:
                    current = self
                if len(key) == 1:
                    return current
                key = key[1:]
            else:
                current = self
            for part in key.split("/"):
                field = current._getField(part, const)
                if field is None:
                    raise MissingField(current, part)
                current = field
            return current
        raise KeyError("Key must not be an empty string!")

    def __getitem__(self, key):
        return self.getField(key, False)

    def __contains__(self, key):
        try:
            return self.getField(key, False) is not None
        except FieldError:
            return False

    def _createInputStream(self, **args):
        assert self._parent
        return InputFieldStream(self, **args)
    def getSubIStream(self):
        stream = None
        if hasattr(self, "_sub_istream"):
            stream = self._sub_istream()
        if stream is None:
            stream = self._createInputStream()
            self._sub_istream = weakref_ref(stream)
        return stream
    def setSubIStream(self, createInputStream):
        cis = self._createInputStream
        self._createInputStream = lambda **args: createInputStream(cis, **args)

    def __nonzero__(self):
        """
        Method called by code like "if field: (...)".
        Always returns True
        """
        return True

