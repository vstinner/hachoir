from functools import lru_cache


class FileCache(object):
    CHUNKSIZE = 4096

    def __init__(self, file):
        self.file = file

        self.update_file_size()

    def update_file_size(self):
        pos = self.file.tell()
        self.file.seek(0, 2)
        self.filesize = self.file.tell()
        self.file.seek(pos)

    @lru_cache(maxsize=100)
    def get_chunk(self, cstart):
        pos = self.file.tell()
        self.file.seek(cstart)
        chunk = self.file.read(self.CHUNKSIZE)
        self.file.seek(pos)
        return chunk

    def hint(self, s, e):
        '''Hint that the range [s, e) may be needed soon'''

        sc = s // self.CHUNKSIZE
        ec = (e + self.CHUNKSIZE - 1) // self.CHUNKSIZE
        for c in range(sc, ec):
            self.get_chunk(c * self.CHUNKSIZE)

    def get(self, s, e):
        '''Obtain the file contents in the range [s, e)'''
        soff = s % self.CHUNKSIZE
        eoff = e % self.CHUNKSIZE
        sc = s // self.CHUNKSIZE
        ec = (e + self.CHUNKSIZE - 1) // self.CHUNKSIZE

        out = []
        for c in range(sc, ec):
            out.append(self.get_chunk(c * self.CHUNKSIZE))

        if eoff:
            out[-1] = out[-1][:eoff]
        if soff:
            out[0] = out[0][soff:]
        return b''.join(out)


def test():
    from io import BytesIO

    for blocksize in [8, 1024]:
        instr = bytes(range(256))
        sf = BytesIO(instr)
        fc = FileCache(sf)
        fc.CHUNKSIZE = blocksize

        import random
        random.seed(1)
        for iter in range(256):
            s = random.randrange(0, fc.filesize + 10)
            e = random.randrange(s, fc.filesize + 10)
            print("testing", s, e)
            got = fc.get(s, e)
            expected = instr[s:e]
            assert got == expected, "Failed to get %d, %d: got %r, expected %r" % (s, e, got, expected)


if __name__ == '__main__':
    test()
