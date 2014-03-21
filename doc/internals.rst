Hachoir internals
=================

When is a field really created?
-------------------------------

A field is created when someone ask to access it, or when another field is
asked and the field is before it. So if you use a field in your field set
constructor, one or more fields will be created. Example:

>>> from hachoir_core.field import Parser, Int8
>>> from hachoir_core.endian import BIG_ENDIAN
>>> class Point(Parser):
...     endian = BIG_ENDIAN
...     def __init__(self, stream):
...         Parser.__init__(self, stream)
...         if self["color"].value == -1:
...             self._description += " (no color)"
...
...     def createFields(self):
...         yield Int8(self, "color", "Point color (-1 for none)")
...         yield Int8(self, "use_3d", "Does it use Z axis?")
...         yield Int8(self, "x", "X axis value")
...         yield Int8(self, "y", "Y axis value")
...         if self["use_3d"] == 1:
...             yield Int8(self, "z", "Z axis value")
...

In the constructor, the field "color" is asked. So the field list will
contains one field (color):

>>> from hachoir_core.stream import StringInputStream
>>> stream = StringInputStream("\x2A\x00\x04\x05")
>>> p = Point(stream)
>>> p.current_length
1

If you access another field, the field list will grow up until the requested
field is reached:

>>> x = p["x"].value
>>> p.current_length
3

Some field set methods which create new fields:

* ``__getitem__()``: feed field list until requested field is reached
  (or raise MissingField exception) ;
* ``__len__()``: create all fields ;
* ``__iter__()``: begin to iterate in existing fields, and the iterate in new
  fields until all fields are created ;
* ``__contains__()``: feed field list until requested field is reached, may
  create all fields if the field doesn't exist ;
* ``readFirstFields()`` ;
* ``readMoreFields()``.

When is the size really computed?
---------------------------------

The size attribute also interact with field list creation, but it's mechanism
is little bit more complex. By default, the whole field list have to be built
before size value can be read. But you can specify field list size:

* if field list is not dynamic (e.g. doesn't depend on flag), use class
  attribute ``static_size`` ;
* otherwise you can set _size instance attribute in the constructor.

Two examples:

>>> from hachoir_core.field import Parser
>>> class FourBytes(Parser):
...     endian = BIG_ENDIAN
...     static_size = 32
...     def createFields(self):
...         yield Integer(self, "four", "uint32")
...
>>> class DynamicSize(Parser):
...     endian = BIG_ENDIAN
...     def __init__(self, stream, nb_items):
...         Parser.__init__(self, stream)
...         assert 0 < nb_items
...         self.nb_items = nb_items
...         self._size = nb_items * 32   # 32 is the size of one item
...
...     def createFields(self):
...         for index in range(self.nb_items):
...             yield Integer(self, "item[]", "uint32")
...
>>> a = FourBytes(stream)
>>> b = DynamicSize(stream, 1)
>>> a.size, b.size
(32, 32)
>>> # Check that nothing is really read from stream
... a.current_length, b.current_length
(0, 0)

When the value of a field is read?
----------------------------------

When a field is created, the value of the field doesn't exist (equals to
None). The value is really read when you read the field value using 'value'
or 'display' field attributes. The value is then stored in the field.

Details about field name
------------------------

The name of a field have to be unique in a field set because it is used as
key in the field list. The argument 'name' of the Field constructor can be
changed in the constructor, but should not (and cannot) be changed after
that.

For arrays, you can use the 'magic' suffix « [] » (e.g. "item[]") which will
be replaced by « [index] » where the number index is a counter starting a
zero.

Endian
------

The "endian" is the way in which ''bytes'' are stored. There are two important
orders:

* « Big endian » in which *most* significant byte (*big* number) are
  written first (PowerPC / Motorola CPUs). It's also the network byte order ;
* « Little endian » in which *least* significant byte (*little* number)
  are written first (Intel x86 CPUs).

The number 0x1020 is stored "0x10 0x20" in big endian and "0x20 0x10" in little
endian.

The endian is global to a FieldSet and is a class attribute. Allowed values:

* BIG_ENDIAN ;
* NETWORK_ENDIAN (alias of BIG_ENDIAN) ;
* LITTLE_ENDIAN.

Example to set endian:

>>> from hachoir_core.endian import LITTLE_ENDIAN
>>> class UseLittleEndian(Parser):
...     endian = LITTLE_ENDIAN
...

For sub-field sets, if endian is not specified, parent endian will be used.

Explore a field set using it's path
-----------------------------------

Fields are stored in a tree. To explore the tree you have different tools:

* attribute *root* of a field which go to tree root ;
* attribute *parent* go to field parent (is None for tree root) ;
* and you can specify a path in *__getitem__()* argument.

There are different valid syntaxes for a path:

* path to a child of current node: ``field["content"]`` ;
* path to a child of the parent: ``field["../brother"]`` ;
* path from the root: ``field["/header/key"]``.

