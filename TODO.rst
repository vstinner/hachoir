*********
TODO list
*********

TODO
====

* Fix hachoir-subfile: hachoir.regex only supports Unicode?
* Write more tests:

  - use coverage to check which parsers are never tested
  - write tests for hachoir-subfile

* convert all methods names to PEP8!!!
* test hachoir-gtk


subfile
=======

Disabled Parsers
^^^^^^^^^^^^^^^^

 * MPEG audio is disabled

Parsers without magic string
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

 * PCX: PhotoRec regex:
   "\x0a[\0\2\3\4\5]][[\0\1][\1\4\x08\x18]"
   (magic, version, compression, bits/pixel)
 * TGA
 * MPEG video, proposition:
   regex "\x00\x00\x01[\xB0\xB3\xB5\xBA\xBB" (from PhotoRec) at offset 0
   (0xBA is the most common value)

Compute content size
^^^^^^^^^^^^^^^^^^^^

 * gzip: need to decompress flow (deflate using zlib)
 * bzip2: need to decompress flow
