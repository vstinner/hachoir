from hachoir.parser import createParser
from hachoir.editor import createEditor
from hachoir.field import writeIntoFile

parser = createParser("file.gz")
with parser:
    editor = createEditor(parser)
    del editor["filename"]
    editor["has_filename"].value = False
    writeIntoFile(editor, "noname.gz")
