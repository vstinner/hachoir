from hachoir_core.field import Field, FieldError
from hachoir_core.stream import InputStream
from hachoir_core.endian import BIG_ENDIAN, LITTLE_ENDIAN

class ParserError(FieldError):
    """
    Error raised by a field set.

    @see: L{FieldError}
    """
    pass

class MatchError(FieldError):
    """
    Error raised by a field set when the stream content doesn't
    match to file format.

    @see: L{FieldError}
    """
    pass

class BasicFieldSet(Field):
    is_field_set = True
    endian = None

    def __init__(self, parent, name, stream, description, size):
        # Sanity checks (preconditions)
        assert not parent or issubclass(parent.__class__, BasicFieldSet)
        assert issubclass(stream.__class__, InputStream)

        # Set field set size
        if self.static_size:
            assert isinstance(self.static_size, (int, long))
            size = self.static_size

        # Set Field attributes
        self._parent = parent
        self._name = name
        self._size = size
        self._description = description
        self.stream = stream

        # Set endian
        if not self.endian:
            assert parent and parent.endian
            self.endian = parent.endian

        if parent:
            # This field set is one of the root leafs
            self._address = parent._current_size
            self.root = parent.root
            assert id(self.stream) == id(parent.stream)
        else:
            # This field set is the root
            self._address = 0
            self.root = self

        # Sanity checks (post-conditions)
        assert self.endian in (BIG_ENDIAN, LITTLE_ENDIAN)
        assert (self._size is None) or (0 < self._size)

    def createFields(self):
        raise NotImplementedError()
    def __iter__(self):
        raise NotImplementedError()
    def __len__(self):
        raise NotImplementedError()

