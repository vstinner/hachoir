from hachoir_core.dict import UniqKeyError
from hachoir_core.field import MissingField, Float32, Float64, FakeArray
from hachoir_core.compatibility import any
from hachoir_core.i18n import _
from hachoir_editor import createEditableField, EditorError
from collections import deque # Python 2.4
import weakref # Python 2.1
import struct

class EditableFieldSet(object):
    MAX_SIZE = (1 << 40) # Arbitrary limit to catch errors
    is_field_set = True

    def __init__(self, parent, fieldset):
        self._parent = parent
        self.input = fieldset  # original FieldSet
        self._fields = {}      # cache of editable fields
        self._deleted = set()  # Names of deleted fields
        self._inserted = {}    # Inserted field (name => list of field,
                               # where name is the name after)

    def array(self, key):
        # FIXME: Use cache?
        return FakeArray(self, key)

    def _getParent(self):
        return self._parent
    parent = property(_getParent)

    def _isAltered(self):
        if self._inserted:
            return True
        if self._deleted:
            return True
        return any(field.is_altered for field in self._fields.itervalues())
    is_altered = property(_isAltered)

    def reset(self):
        """
        Reset the field set and the input field set.
        """
        for key, field in self._fields.iteritems():
            if not field.is_altered:
                del self._fields[key]
        self.input.reset()

    def __len__(self):
        return len(self.input) \
            - len(self._deleted) \
            + sum( len(new) for new in self._inserted.itervalues() )

    def __iter__(self):
        for field in self.input:
            name = field.name
            if name in self._inserted:
                for newfield in self._inserted[name]:
                    yield weakref.proxy(newfield)
            if name not in self._deleted:
                yield self[name]
        if None in self._inserted:
            for newfield in self._inserted[None]:
                yield weakref.proxy(newfield)

    def insertBefore(self, name, *new_fields):
        self._insert(name, new_fields, False)

    def insertAfter(self, name, *new_fields):
        self._insert(name, new_fields, True)

    def insert(self, *new_fields):
        self._insert(None, new_fields, True)

    def _insert(self, key, new_fields, next):
        """
        key is the name of the field before which new_fields
        will be inserted. If next is True, the fields will be inserted
        _after_ this field.
        """
        # Set unique field name
        for field in new_fields:
            if field._name.endswith("[]"):
                self.input.setUniqueFieldName(field)

        # Check that there is no duplicate in inserted fields
        new_names = list(field.name for field in new_fields)
        names_set = set(new_names)
        if len(names_set) != len(new_fields):
            duplicates = (name for name in names_set if 1 < new_names.count(name))
            raise UniqKeyError(_("Duplicates in inserted fields: %s") % ", ".join(duplicates))

        # Check that field names are not in input
        if self.input: # Write special version for NewFieldSet?
            for name in new_names:
                if name in self.input and name not in self._deleted:
                    raise UniqKeyError(_("Field name '%s' already exists") % name)

        # Check that field names are not in inserted fields
        for fields in self._inserted.itervalues():
            for field in fields:
                if field.name in new_names:
                    raise UniqKeyError(_("Field name '%s' already exists") % field.name)

        # Input have already inserted field?
        if key in self._inserted:
            if next:
                self._inserted[key].extend( reversed(new_fields) )
            else:
                self._inserted[key].extendleft( reversed(new_fields) )
            return

        # Whould like to insert in inserted fields?
        if key:
            for fields in self._inserted.itervalues():
                names = [item.name for item in fields]
                try:
                    pos = names.index(key)
                except ValueError:
                    continue
                if 0 <= pos:
                    if next:
                        pos += 1
                    fields.rotate(-pos)
                    fields.extendleft( reversed(new_fields) )
                    fields.rotate(pos)
                    return

            # Get next field. Use None if we are at the end.
            if next:
                index = self.input[key].index + 1
                try:
                    key = self.input[index].name
                except IndexError:
                    key = None

            # Check that field names are not in input
            if key not in self.input:
                raise MissingField(self, key)

        # Insert in original input
        self._inserted[key]= deque(new_fields)

    def _getDescription(self):
        return self.input.description
    description = property(_getDescription)

    def _getStream(self):
        # FIXME: This property is maybe a bad idea since address may be differents
        return self.input.stream
    stream = property(_getStream)

    def _getName(self):
        return self.input.name
    name = property(_getName)

    def _getEndian(self):
        return self.input.endian
    endian = property(_getEndian)

    def _getAddress(self):
        if self._parent:
            return self._parent._getFieldAddress(self.name)
        else:
            return 0
    address = property(_getAddress)

    def _getAbsoluteAddress(self):
        address = self.address
        current = self._parent
        while current:
            address += current.address
            current = current._parent
        return address
    absolute_address = property(_getAbsoluteAddress)

    def hasValue(self):
        return False
#        return self._parent.input[self.name].hasValue()

    def _getSize(self):
        if self.is_altered:
            return sum(field.size for field in self)
        else:
            return self.input.size
    size = property(_getSize)

    def _getPath(self):
        return self.input.path
    path = property(_getPath)

    def _getOriginalField(self, name):
        assert name in self.input
        return self.input[name]

    def _getFieldInputAddress(self, name):
        """
        Absolute address of a field from the input field set.
        """
        assert name in self.input
        return self.input[name].absolute_address

    def _getFieldAddress(self, name):
        """
        Compute relative address of a field. The operation takes care of
        deleted and resized fields.
        """
        #assert name not in self._deleted
        addr = 0
        for field in self:
            if field.name == name:
                return addr
            addr += field.size
        raise MissingField(self, name)

    def _getItemByPath(self, path):
        if not path[0]:
            path = path[1:]
        field = self
        for name in path:
            field = field[name]
        return field

    def __contains__(self, name):
        try:
            field = self[name]
            return (field is not None)
        except MissingField:
            return False

    def __getitem__(self, key):
        """
        Create a weak reference to an editable field (EditableField) for the
        field with specified name. If the field is removed later, using the
        editable field will raise a weakref.ReferenceError exception.

        May raise a MissingField error if the field doesn't exist in original
        field set or it has been deleted.
        """
        if "/" in key:
            return self._getItemByPath(key.split("/"))
        if isinstance(key, (int, long)):
            raise EditorError("Integer index are not supported")

        if (key in self._deleted) or (key not in self.input):
            raise MissingField(self, key)
        if key not in self._fields:
            field = self.input[key]
            if field.is_field_set:
                self._fields[key] = createEditableFieldSet(self, field)
            else:
                self._fields[key] = createEditableField(self, field)
        return weakref.proxy(self._fields[key])

    def __delitem__(self, name):
        """
        Remove a field from the field set. May raise an MissingField exception
        if the field has already been deleted.
        """
        if name in self._deleted:
            raise MissingField(self, name)
        self._deleted.add(name)
        if name in self._fields:
            del self._fields[name]

    def writeInto(self, output):
        """
        Write the content if this field set into the output stream
        (OutputStream).
        """
        if not self.is_altered:
            # Not altered: just copy bits/bytes
            input = self.input
            if input.size % 8:
                output.copyBitsFrom(input.stream,
                    input.absolute_address, input.size, input.endian)
            else:
                output.copyBytesFrom(input.stream,
                    input.absolute_address, input.size//8)
        else:
            # Altered: call writeInto() method of each field
            realaddr = 0
            for field in self:
                field.writeInto(output)
                realaddr += field.size

    def _getValue(self):
        raise EditorError('Field set "%s" has no value' % self.path)
    def _setValue(self, value):
        raise EditorError('Field set "%s" value is read only' % self.path)
    value = property(_getValue, _setValue, "Value of field")

class EditableFloat(EditableFieldSet):
    _value = None

    def _isAltered(self):
        return (self._value is not None)
    is_altered = property(_isAltered)

    def writeInto(self, output):
        if self._value is not None:
            self._write(output)
        else:
            EditableFieldSet.writeInto(self, output)

    def _write(self, output):
        format = self.input.struct_format
        raw = struct.pack(format, self._value)
        output.writeBytes(raw)

    def _setValue(self, value):
        self.parent._is_altered = True
        self._value = value
    value = property(EditableFieldSet._getValue, _setValue)

def createEditableFieldSet(parent, field):
    cls = field.__class__
    # FIXME: Support Float80
    if cls in (Float32, Float64):
        return EditableFloat(parent, field)
    else:
        return EditableFieldSet(parent, field)

class NewFieldSet(EditableFieldSet):
    def __init__(self, parent, name):
        EditableFieldSet.__init__(self, parent, None)
        self._name = name
        self._endian = parent.endian

    def __iter__(self):
        if None in self._inserted:
            return iter(self._inserted[None])
        else:
            raise StopIteration()

    def _getName(self):
        return self._name
    name = property(_getName)

    def _getEndian(self):
        return self._endian
    endian = property(_getEndian)

    is_altered = property(lambda self: True)

def createEditor(fieldset):
    return EditableFieldSet(None, fieldset)

