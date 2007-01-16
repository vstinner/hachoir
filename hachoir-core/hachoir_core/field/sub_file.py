from hachoir_core.field import Bytes
from hachoir_core.tools import makePrintable, humanFilesize
from hachoir_core.stream import InputIOStream

class SubFile(Bytes):
    """
    File stored in another file
    """
    def __init__(self, parent, name, length, description=None,
    parser=None, filename=None, mime_type=None):
        if filename:
            if not isinstance(filename, unicode):
                filename = makePrintable(filename, "ISO-8859-1")
            if not description:
                description = 'File "%s" (%s)' % (filename, humanFilesize(length))
        Bytes.__init__(self, parent, name, length, description)
        tags = []
        if parser is not None:
            tags.append(parser)
        if mime_type:
            tags.append(( "mime", mime_type ))
        if filename:
            tags.append(( "filename", filename ))
        self._getIStreamTags = lambda: tags

class CompressedStream:
    offset = 0

    def __init__(self, stream, decompressor):
        self.stream = stream
        self.decompressor = decompressor(stream)
        self._buffer = ''

    def read(self, size):
        d = self._buffer
        data = [ d[:size] ]
        size -= len(d)
        if size > 0:
            d = self.decompressor(size)
            data.append(d[:size])
            size -= len(d)
            while size > 0:
                n = 4096
                if self.stream.size:
                    n = min(self.stream.size - self.offset, n)
                    if not n:
                        break
                d = self.stream.read(self.offset, n)[1]
                self.offset += 8 * len(d)
                d = self.decompressor(size, d)
                data.append(d[:size])
                size -= len(d)
        self._buffer = d[size+len(d):]
        return ''.join(data)

def CompressedField(field, decompressor, size=None):
    if field._parent:
        cis = field._createInputStream
    else:
        cis = lambda: field.stream
    def createInputStream(size=size):
        stream = cis()
        input = CompressedStream(stream, decompressor)
        address = field.absolute_address
        source = "Compressed source: '%s' (offset=%s)" % (stream.source, address)
        if callable(size):
            size = size()
        stream = InputIOStream(input, source, size)
        stream.address = address
        return stream
    field._createInputStream = createInputStream
    return field
