.. _editor:

++++++++++++++
Hachoir editor
++++++++++++++

Hachoir editor is a Python library based on Hachoir core used to edit binary
files.

Today, only one program uses it: :ref:`hachoir-strip <strip>` (remove "useless"
information to make a file smaller).

Example: gzip, remove filename
==============================

::

    from hachoir_parser import createParser
    from hachoir_editor import createEditor
    from hachoir_core.field import writeIntoFile

    parser = createParser(u"file.gz")
    editor = createEditor(parser)
    del editor["filename"]
    editor["has_filename"].value = False
    writeIntoFile(editor, u"noname.gz")

Example: gzip, add extra
========================

::

    from hachoir_parser import createParser
    from hachoir_editor import createEditor
    from hachoir_core.field import writeIntoFile
    from hachoir_core.editor import EditableInteger, EditableBytes

    parser = createParser(u"file.gz")
    editor = createEditor(parser)
    extra = "abcd"
    editor["has_extra"].value = True
    editor.insertAfter("os",
        EditableInteger(editor, "extra_length", False, 16, len(extra)),
        EditableBytes(editor, "extra", extra))
    writeIntoFile(editor, u"file_extra.gz")

Example: zip, set comment
=========================

::

    from hachoir_parser import createParser
    from hachoir_editor import createEditor
    from hachoir_core.field import writeIntoFile

    parser = createParser(u"file.gz")
    editor = createEditor(parser)
    editor["end_central_directory/comment"].value = "new comment"
    writeIntoFile(editor, u"file_comment.zip")

