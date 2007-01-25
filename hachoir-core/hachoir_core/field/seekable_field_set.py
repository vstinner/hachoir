from hachoir_core.field import BasicFieldSet, FakeArray
from hachoir_core.tools import lowerBound

class SeekableFieldSet(BasicFieldSet):
    def __init__(self, parent, name, stream, description, size):
        BasicFieldSet.__init__(self, parent, name, stream, description, size)
        self._generator = self.createFields()
        self._current_size = 0
        self._current_max_size = 0
        self._current_length = 0
        self._field_dict = {}
        self._field_array = []

    def _feedOne(self):
        field = self._generator.next()
        self._addField(field)
        return field

    def array(self, key):
        return FakeArray(self, key)

    def seekBit(self, address):
        self.error("%s.seekBit(%s) from %s" % (self.__class__.__name__, address, self._current_size))
        self._current_size = address

    def getFieldByAddress(self, address, feed=True):
        # TODO: Merge with GenericFieldSet.getFieldByAddress()
        if feed and self._generator:
            raise NotImplementedError()
        if address < self._current_size:
            i = lowerBound(self._field_array, lambda x: x.address + x.size <= address)
            if i is not None:
                return self._field_array[i]
        return None

    def _stopFeed(self):
        self._size = self._current_max_size
        self._generator = None
    done = property(lambda self: bool(self._generator))

    def __getitem__(self, key):
        if isinstance(key, (int, long)):
            if key < len(self._field_array):
                return self._field_array[key]
            else:
                raise NotImplementedError()
        if "/" in key:
            parent, children = key.split("/", 1)
            return self[parent][children]
        assert "/" not in key
        if key in self._field_dict:
            return self._field_dict[key]
        try:
            while True:
                field = self._feedOne()
                if field.name == key:
                    return field
        except StopIteration:
            self._stopFeed()
        raise AttributeError("%s has no field '%s'" % (self.path, key))

    def _addField(self, field):
        self._field_dict[field.name] = field
        self._field_array.append(field)
        self._current_length += 1
        self._current_size += field.size
        self._current_max_size = max(self._current_max_size, field.address + field.size)

    def readMoreFields(self, number):
        added = 0
        try:
            for index in xrange(number):
                self._feedOne()
                added += 1
        except StopIteration:
            self._stopFeed()
        return added

    current_length = property(lambda self: self._current_length)

    def __iter__(self):
        raise NotImplementedError()
    def __len__(self):
        raise NotImplementedError()

