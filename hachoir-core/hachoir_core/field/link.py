from hachoir_core.field import Field, FieldSet, Bytes, MissingField
from hachoir_core.stream import FragmentedStream

class Link(Field):
    def __init__(self, parent, name, *args):
        Field.__init__(self, parent, name, 0, *args)

    def createValue(self):
        return self._parent[self.display]

    def createDisplay(self):
        return self.value.path

    def _getField(self, name, const):
        target = self.value
        assert self != target
        return target._getField(name, const)

class Fragment(FieldSet):
    def __init__(self, parent, name, description=None, size=None, first=None):
        FieldSet.__init__(self, parent, name, description, size)
        self._field_generator = self._createFields(self._field_generator)
        if first is None:
            self.first = self
        else:
            self.first = first
        if self.__class__.createFields == Fragment.createFields:
            self._getData = lambda: self

    def getData(self):
        try:
            return self._getData()
        except MissingField, e:
            self.error(str(e))
        return None

    def _createInputStream(self, **args):
        if self.first is self and hasattr(self.first, "_getData"):
            return FragmentedStream(self.first, **args)
        return FieldSet._createInputStream(self, **args)

    def _createNext(self):
        return None
    def _getNext(self):
        if callable(self._createNext):
            self._createNext = self._createNext()
            assert self._createNext is not self
        return self._createNext
    next = property(_getNext)

    def _createFields(self, field_generator):
        if self.first != self:
            link = Link(self, "first", None)
            link._value = self.first
            yield link
        next = self.next
        if next:
            link = Link(self, "next", None)
            link._value = next
            yield link
        for field in field_generator:
            yield field

    def createFields(self):
        if self._size is None:
            self._size = self._getSize()
        yield Bytes(self, "data", self._size/8)

