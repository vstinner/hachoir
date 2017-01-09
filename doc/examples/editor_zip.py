from hachoir.parser import createParser
from hachoir.editor import createEditor
from hachoir.field import writeIntoFile

parser = createParser("file.zip")
with parser:
    editor = createEditor(parser)
    editor["end_central_directory/comment"].value = "new comment"
    writeIntoFile(editor, "file_comment.zip")
