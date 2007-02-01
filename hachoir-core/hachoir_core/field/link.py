from hachoir_core.field import Field, FieldSet, Bytes, MissingField
from hachoir_core.stream import FragmentedStream

class Link(Field):
    def __init__(self, parent, name, *args, **kw):
        Field.__init__(self, parent, name, 0, *args, **kw)

    def hasValue(self):
        return True

    def createValue(self):
        return self._parent[self.display]

    def createDisplay(self):
        return self.value.path

    def _getField(self, name, const):
        target = self.value
        assert self != target
        return target._getField(name, const)

class Fragment(FieldSet):
    _first = None

    def __init__(self, *args, **kw):
        FieldSet.__init__(self, *args, **kw)
        self._field_generator = self._createFields(self._field_generator)
        if self.__class__.createFields == Fragment.createFields:
            self._getData = lambda: self

    def getData(self):
        try:
            return self._getData()
        except MissingField, e:
            self.error(str(e))
        return None

    def setLinks(self, first, next=None):
        self._first = first or self
        self._next = next
        self._feedLinks = lambda: self
        return self

    def _feedLinks(self):
        while self._first is None and self.readMoreFields(1):
            pass
        if self._first is None:
            raise ParseError()
        return self
    first = property(lambda self: self._feedLinks()._first)

    def _getNext(self):
        next = self._feedLinks()._next
        if callable(next):
            self._next = next = next()
        return next
    next  = property(_getNext)

    def _createInputStream(self, **args):
        first = self.first
        if first is self and hasattr(first, "_getData"):
            return FragmentedStream(first, **args)
        return FieldSet._createInputStream(self, **args)

    def _createFields(self, field_generator):
        if self._first is None:
            for field in field_generator:
                if self._first is not None:
                    break
                yield field
            else:
                raise ParserError()
        else:
            field = None
        if self._first is not self:
            link = Link(self, "first", None)
            link._getValue = lambda: self._first
            yield link
        next = self.next
        if next:
            link = Link(self, "next", None)
            link._getValue = lambda: next
            yield link
        if field:
            yield field
        for field in field_generator:
            yield field

    def createFields(self):
        if self._size is None:
            self._size = self._getSize()
        yield Bytes(self, "data", self._size/8)

