from hachoir_core.field import CompressedField

try:
    from zlib import decompressobj, MAX_WBITS

    class DeflateStream:
        def __init__(self, stream):
            self.gzip = decompressobj(-MAX_WBITS)

        def __call__(self, size, data=None):
            if data is None:
                data = self.gzip.unconsumed_tail
            return self.gzip.decompress(data, size)

    def Deflate(field):
        CompressedField(field, DeflateStream)
        return field
except ImportError:
    def Deflate(field):
        return field

