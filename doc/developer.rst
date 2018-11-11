++++++++++++++++++++++
Hachoir for developers
++++++++++++++++++++++

Download code and run tests
===========================

To clone Git repository, type::

    git clone https://github.com/vstinner/hachoir

Enter hachoir directory::

    cd hachoir

To run tests, type tox::

    tox

If tox is not already installed, install tox::

    python3 -m pip install tox

See also `Hachoir on the Travis CI <https://travis-ci.org/vstinner/hachoir>`_.


Why using Hachoir parsers?
==========================

Why using slow Python code instead of fast hardcoded C code? Hachoir has many
interesting features:

* Autofix: Hachoir is able to open invalid / truncated files
* Lazy: Open a file is very fast since no information is read from file,
  data are read and/or computed when the user ask for it
* Types: Hachoir has many predefined field types (integer, bit, string, etc.)
  and supports string with charset (ISO-8859-1, UTF-8, UTF-16, ...)
* Addresses and sizes are stored in bit, so flags are stored as classic fields
* Endian: You have to set endian once, and then number are converted in the
  right endian
* Editor: Using Hachoir representation of data, you can edit, insert, remove
  data and then save in a new file.


Hachoir Metadata Example
========================

:ref:`hachoir-metadata <metadata>` example:

.. literalinclude:: examples/metadata.py


hachoir.stream: Stream manipulation
===================================

To split data we first need is to get data :-) So this section presents the
"hachoir.stream" API.

In most cases we work on files using the FileInputStream function. This function
takes one argument: a Unicode filename. But for practical reasons
we will use StringInputStream function in this documentation::

   >>> data = b"point\0\3\0\2\0"
   >>> from hachoir.stream import StringInputStream, LITTLE_ENDIAN
   >>> stream = StringInputStream(data)
   >>> stream.source
   '<string>'
   >>> len(data), stream.size
   (10, 80)
   >>> data[1:6], stream.readBytes(8, 5)
   (b'oint\x00', b'oint\x00')
   >>> data[6:8], stream.readBits(6*8, 16, LITTLE_ENDIAN)
   (b'\x03\x00', 3)
   >>> data[8:10], stream.readBits(8*8, 16, LITTLE_ENDIAN)
   (b'\x02\x00', 2)

First big difference between a string and a Hachoir stream is that sizes
and addresses are written in bits and not bytes. The difference is a factor
of eight, that's why we write "6*8" to get the sixth byte for example. You
don't need to know anything else to use Hachoir, so let's play with fields!

hachoir.field: Field manipulation
=================================

Basic parser
------------

We will parse the data used in the last section::

   >>> from hachoir.field import Parser, CString, UInt16
   >>> class Point(Parser):
   ...     endian = LITTLE_ENDIAN
   ...     def createFields(self):
   ...         yield CString(self, "name", "Point name")
   ...         yield UInt16(self, "x", "X coordinate")
   ...         yield UInt16(self, "y", "Y coordinate")
   ...
   >>> point = Point(stream)
   >>> for field in point:
   ...     print("%s) %s=%s" % (field.address, field.name, field.display))
   ...
   0) name="point"
   48) x=3
   64) y=2

`point` is a the root of our field tree. This tree is really simple, it just
has one level and three fields: name, x and y. Hachoir stores a lot of
information in each field. In this example we just show the address, name and
display attributes. But a field has more attributes::

   >>> x = point["x"]
   >>> "%s = %s" % (x.path, x.value)
   '/x = 3'
   >>> x.parent == point
   True
   >>> x.description
   'X coordinate'
   >>> x.index
   1
   >>> x.address, x.absolute_address
   (48, 48)

The index is not the index of a field in a parent field list, '1' means that it's
the second since the index starts at zero.

Parser with sub-field sets
--------------------------

After learning basic API, let's see a more complex parser: parser with
sub-field sets::

   >>> from hachoir.field import FieldSet, UInt8, Character, String
   >>> class Entry(FieldSet):
   ...     def createFields(self):
   ...         yield Character(self, "letter")
   ...         yield UInt8(self, "code")
   ...
   >>> class MyFormat(Parser):
   ...     endian = LITTLE_ENDIAN
   ...     def createFields(self):
   ...         yield String(self, "signature", 3, charset="ASCII")
   ...         yield UInt8(self, "count")
   ...         for index in range(self["count"].value):
   ...             yield Entry(self, "point[]")
   ...
   >>> data = b"MYF\3a\0b\2c\0"
   >>> stream = StringInputStream(data)
   >>> root = MyFormat(stream)

This example presents many interesting features of Hachoir. First of all, you
can see that you can have two or more levels of fields. Here we have a tree
with two levels::

   >>> def displayTree(parent):
   ...     for field in parent:
   ...         print(field.path)
   ...         if field.is_field_set: displayTree(field)
   ...
   >>> displayTree(root)
   /signature
   /count
   /point[0]
   /point[0]/letter
   /point[0]/code
   /point[1]
   /point[1]/letter
   /point[1]/code
   /point[2]
   /point[2]/letter
   /point[2]/code

A field set is also a field, so it has the same attributes than another field
(name, address, size, path, etc.) but has some new attributes like stream or
root.

Lazy feature
------------

Hachoir is written in Python so it should be slow and eat a lot of CPU and
memory, and it does. But in most cases, you don't need to explore an entire
field set and read all values; you just need to read some values of some
specific fields. Hachoir is really lazy: no field is parsed before you ask for
it, no value is read from stream before you read a value, etc. To inspect this
behaviour, you can watch "current_length" (number of read fields) and
"current_size" (current size in bits of a field set)::

   >>> root = MyFormat(stream)  # Rebuild our parser
   >>> (root.current_length, root.current_size)
   (0, 0)
   >>> print(root["signature"].display)
   "MYF"
   >>> (root.current_length, root.current_size, root["signature"].size)
   (1, 24, 24)

Just after its creation, a parser is empty (0 fields). When we read the first
field, its size becomes the size of the first field. Some operations requires
to read more fields::

   >>> print(root["point[0]/letter"].display)
   'a'
   >>> (root.current_length, root.current_size)
   (3, 48)

Reading point[0] needs to read field "count". So root now contains three
fields.

List of field types
===================

Number:

* Bit: one bit (True/False) ;
* Bits: unsigned number with a size in bits ;
* Bytes: vector of know bytes (e.g. file signature) ;
* UInt8, UInt16, UInt24, UInt32, UInt64: unsigned number (size: 8, 16, ... bits) ;
* Int8, Int16, Int24, Int32, Int64: signed number (size: 8, 16, ... bits) ;
* Float32, Float64, Float80: IEEE 754 floating point number (32, 64, 80 bits) ;

Text:

* Character: 8 bits ASCII character ;
* String: fixed length string ;
* CString: string ending with nul byte ("\\0") ;
* UnixLine: string ending with new line character ("\\n") ;
* PascalString8, PascalString16 and PascalString32: string prefixed with
  length in a unsigned 8 / 16 / 32 bits integer (use parent endian) ;

Timestamp (date and time):

* TimestampUnix32, TimestampUnix64: 32/64 bits UNIX, number of seconds since
  the January 1st 1970 ;
* TimestampMac32: 32-bit Mac, number of seconds since the January 1st 1904 ;
* TimestampWin64: 64-bit Windows, number of 1/10 microseconds since
  the January 1st 1600 ;
* DateTimeMSDOS32 and TimeDateMSDOS32: 32-bit MS-DOS structure,
  since the January 1st 1980.

Timedelta (duration):

 * TimedeltaWin64: 64-bit Windows, number of 1/10 microseconds

Padding and raw bytes:

* PaddingBits/PaddingBytes: padding with a size in bits/bytes ;
* NullBits/NullBytes: null padding with a size in bits/bytes ;
* RawBits/RawBytes: unknown content with a size in bits/bytes.
* SubFile: a file contained in the stream ;

To create your own type, you can use:

* GenericInteger: integer ;
* GenericString: string ;
* FieldSet: Set of other fields ;
* Parser: The main class to parse a stream.


Field class
===========

.. autoclass:: hachoir.field.field.Field
   :members:

Field set class
===============

Read only attributes:

* endian: value is BIG_ENDIAN or LITTLE_ENDIAN, the way the bits are written
  in input stream <~~ can be replaced
* stream (InputStream): input stream
* root (FieldSet): root of all fields
* eof (bool): End Of File: are we at the end of the input stream?
* done (bool): The parser is done or not?

Read only and lazy attributes:

* current_size (long): Current size in bits
* current_length (long): Current number of children

Methods:

* connectEvent(event, handler, local=True): connect an handler to an event
* raiseEvent(event, \*args): raise an event
* reset(): clear all caches but keep its size if we know it
* setUniqueFieldName(): for field with name ending with "[]",
  replaces "[]" with an unique identifier like, "item[]" => "item[0]".
* seekBit(address, ...): create a field to seek to specified address or
  returns None if we are already there
* seekByte(address, ...): create a field to seek to specified address or
  returns None if we are already there
* replaceField(name, fields): replace a field with
  one or more fields <~~~ I don't like this method :-(
* getFieldByAddress(address, feed=True): get the field at the
  specified address
* writeFieldsIn(old, address, new): helper for replaceField() <~~~ can be an helper?
* getFieldType(): get the field type as a short string. The type may contains
  extra informations like the string charset.

Lazy methods:

* array(): create a FakeArray to easily get a field by its index
  (see FakeArray API to get more details)
* __len__(): number of children in the field set
* readFirstFields(number): read first 'number' fields,
  returns number of new fields
* readMoreFields(number): read more 'number' fields,
  returns number of new fields
* __iter__(): iterate over children
* createFields(): main function of the parser, create the fields. Don't call
  this function directly.

Log
===

Change Hachoir verbosity, make Hachoir quiet::

   from hachoir.core import config
   config.quiet = True

