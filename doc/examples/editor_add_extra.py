from hachoir.parser import createParser
from hachoir.editor import createEditor
from hachoir.field import writeIntoFile
from hachoir.editor import EditableInteger, EditableBytes

parser = createParser("file.gz")
with parser:
    editor = createEditor(parser)
    extra = "abcd"
    editor["has_extra"].value = True
    editor.insertAfter("os",
                       EditableInteger(editor, "extra_length", False,
                                       16, len(extra)),
                       EditableBytes(editor, "extra", extra))
    writeIntoFile(editor, "file_extra.gz")
