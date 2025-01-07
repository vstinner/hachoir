.. _list:

++++++++++++++++++++
hachoir-list program
++++++++++++++++++++

hachoir-list uses Hachoir to decode a binary file and then
prints out the decoded fields, so that the output can be processed
by other text-oriented tools.

Examples
========

Print all decoded fields::

    $ hachoir-list cd_0008_5C48_1m53s.cda
    signature <FixedString, 4B>: "RIFF"
    filesize <UInt32, 4B>: 36 bytes
    type <FixedString, 4B>: "CDDA"
    cdda <ChunkCDDA, 32B>
      tag <FixedString, 4B>: "fmt "
      size <UInt32, 4B>: 24 bytes
      cda_version <UInt16, 2B>: 1
      track_no <UInt16, 2B>: 4
      disc_serial <UInt32, 4B>: 0008-5C48
      hsg_offset <UInt32, 4B>: 19477
      hsg_length <UInt32, 4B>: 8507
      rb_offset <RedBook, 4B>
        frame <UInt8, 1B>: 52
        second <UInt8, 1B>: 21
        minute <UInt8, 1B>: 4
        notused <PaddingBytes, 1B>: "\0"
      rb_length <RedBook, 4B>
        frame <UInt8, 1B>: 32
        second <UInt8, 1B>: 53
        minute <UInt8, 1B>: 1
        notused <PaddingBytes, 1B>: "\0"

Other options:

* ``--description``: Show description for each field
* ``--indent-width``: Change (or disable) indentation
* ``--hide-value``: Don't display the string value
* ``--hide-size``: Don't display field size
* Get full option list using ``--help``
