from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from sys import argv, stderr, exit

if len(argv) != 2:
    print("usage: %s filename" % argv[0], file=stderr)
    exit(1)
filename = argv[1]
parser = createParser(filename)
if not parser:
    print("Unable to parse file", file=stderr)
    exit(1)

with parser:
    try:
        metadata = extractMetadata(parser)
    except Exception as err:
        print("Metadata extraction error: %s" % err)
        metadata = None
if not metadata:
    print("Unable to extract metadata")
    exit(1)

for line in metadata.exportPlaintext():
    print(line)
