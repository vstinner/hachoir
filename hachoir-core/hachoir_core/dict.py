"""
Dictionnary classes which store values order.
"""

from hachoir_core.error import HachoirError
from hachoir_core.i18n import _

class UniqKeyError(HachoirError):
    """
    Error raised when a value is set whereas the key already exist in a
    dictionnary.
    """
    pass

class Dict(object):
    """
    This class works like classic Python dict() but has an important method:
    __iter__() which allow to iterate into the dictionnary _values_ (and not
    keys like Python's dict does).
    """
    def __init__(self):
        self._index = {}        # key => index
        self._value_list = []   # index => value

    def _getValues(self):
        return self._value_list
    values = property(_getValues)

    def index(self, key):
        """
        Search a value by its key and returns its index
        """
        return self._index.get(key, None)

    def __getitem__(self, key):
        """
        Get item with specified key.
        To get a value by it's index, use mydict.values[index]
        """
        return self._value_list[self._index[key]]

    def __setitem__(self, key, value):
        self._value_list[self._index[key]] = value

    def append(self, key, value):
        """
        Append new value
        """
        if key in self._index:
            raise UniqKeyError(_("Key '%s' already exists") % key)
        self._index[key] = len(self._value_list)
        self._value_list.append(value)

    def __len__(self):
        return len(self._value_list)

    def __contains__(self, key):
        return key in self._index

    def __iter__(self):
        return iter(self._value_list)

    def replace(self, oldkey, newkey, new_value):
        """
        Replace an existing value with another one
        """
        index = self._index[oldkey]
        self._value_list[index] = new_value
        if oldkey != newkey:
            del self._index[oldkey]
            self._index[newkey] = index

    def __delitem__(self, index):
        """
        Delete item at position index. May raise IndexError.
        """
        if index < 0:
            index += len(self._value_list)
        if not (0 <= index < len(self._value_list)):
            raise IndexError(_("list assignment index out of range (%s/%s)")
                % (index, len(self._value_list)))
        del self._value_list[index]
        for k, i in self._index.items():
            if i > index:
                self._index[k] -= 1
            elif i == index:
                del self._index[k]

    def insert(self, index, key, value):
        if key in self:
            raise UniqKeyError(_("Insert error: key '%s' ready exists") % key)
        _index = index
        if index < 0:
            index += len(self._value_list)
        if not(0 <= index <= len(self._value_list)):
            raise IndexError(_("Insert error: index '%s' is invalid") % _index)
        for k, i in self._index.items():
            if i >= index:
                self._index[k] += 1
        self._index[key] = index
        self._value_list.insert(index, value)
