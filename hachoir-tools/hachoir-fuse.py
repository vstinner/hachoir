#!/usr/bin/env python
"""
Proof of concept of Hachoir user interface using FUSE
"""

import errno
import os
import stat
from hachoir.log import log
from hachoir.field import MissingField
from hachoir.tools import makePrintable
from hachoir.stream import FileOutputStream
from hachoir.editor import createEditor
from hachoir_parser import createParser

# some spaghetti to make it usable without fuse-py being installed
for i in True, False:
    try:
        import fuse
        from fuse import Fuse
    except ImportError:
        if i:
            try:
                import _find_fuse_parts
            except ImportError:
                pass
        else:
            raise

if not hasattr(fuse, '__version__'):
    raise RuntimeError, \
        "your fuse-py doesn't know of fuse.__version__, probably it's too old."

# This setting is optional, but it ensures that this class will keep
# working after a future API revision
fuse.fuse_python_api = (0, 2)

class MyStat(fuse.Stat):
    def __init__(self):
        self.st_mode = 0
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 0
        self.st_uid = 0
        self.st_gid = 0
        self.st_size = 0
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0

class HelloFS(Fuse):
    def __init__(self, input_filename, **kw):
        Fuse.__init__(self, **kw)
        log.setFilename("/home/haypo/fuse_log")
        self.hachoir = createParser(input_filename)
        if True:
            self.hachoir = createEditor(self.hachoir)
            self.readonly = False
        else:
            self.readonly = True
        self.fs_charset = "ASCII"

    def getField(self, path):
        try:
            field = self.hachoir
            try:
                for name in path.split("/")[1:]:
                    if not name:
                        break
                    name = name.split("-", 1)
                    if len(name) != 2:
                        return None
                    field = field[name[1]]
                return field
            except MissingField:
                return None
        except Exception, xx:
            log.info("Exception: %s" % str(xx))
            raise

    def fieldValue(self, field):
        return makePrintable(field.display, "ISO-8859-1")+"\n"

    def getattr(self, path):
        st = MyStat()
        if path == '/':
            st.st_mode = stat.S_IFDIR | 0755
            st.st_nlink = 2
            return st
        if path == "/.command":
            st.st_mode = stat.S_IFDIR | 0755
            return st
        if path.startswith("/.command/"):
            name = path.split("/", 3)[2]
            if name in ("writeInto",):
                st.st_mode = stat.S_IFREG | 0444
                return st
            return -errno.ENOENT

        # Get field
        field = self.getField(path)
        if not field:
            return -errno.ENOENT

        # Set size and mode
        if field.is_field_set:
            st.st_mode = stat.S_IFDIR | 0755
        else:
            st.st_mode = stat.S_IFREG | 0444
        st.st_nlink = 1
        if field.hasValue():
            st.st_size = len(self.fieldValue(field))
        else:
            st.st_size = 0
        return st

    def unlink(self, path, *args):
        log.info("unlink(%s)" % path)
        field = self.getField(path)
        log.info("del %s" % field.name)
        if not field:
            return -errno.ENOENT
        if self.readonly:
            return -errno.EACCES
        log.info("del %s" % field.name)
        try:
            del field.parent[field.name]
        except Exception, err:
            log.info("del ERROR %s" % err)
        return 0

    def readCommandDir(self):
        yield fuse.Direntry('writeInto')

    def readdir(self, path, offset):
        log.info("readdir(%s)" % path)
        yield fuse.Direntry('.')
        yield fuse.Direntry('..')
        if path == "/.command":
            for entry in self.readCommandDir():
                yield entry
            return

        # Get field
        fieldset = self.getField(path)
#        if not fieldset:
#            return -errno.ENOENT

        if path == "/":
            entry = fuse.Direntry(".command")
            entry.type = stat.S_IFREG
            yield entry

        # Format file name
        count = len(fieldset)
        if count % 10:
            count += 10 - (count % 10)
        format = "%%0%ud-%%s" % (count//10)

        # Create entries
        for index, field in enumerate(fieldset):
            name = format % (1+index, field.name)
            entry = fuse.Direntry(name)
            if field.is_field_set:
                entry.type = stat.S_IFDIR
            else:
                entry.type = stat.S_IFREG
            yield entry
        log.info("readdir(%s) done" % path)

    def open(self, path, flags):
        log.info("open(%s)" % path)
#        if ...:
#            return -errno.ENOENT
#        accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
#        if (flags & accmode) != os.O_RDONLY:
#            return -errno.EACCES

    def write(self, path, data, offset):
        if path == "/.command/writeInto":
            if self.readonly:
                return -errno.EACCES
            try:
                data = data.strip(" \t\r\n\0")
                filename = unicode(data, self.fs_charset)
            except UnicodeDecodeError:
                log.info("writeInto(): unicode error!")
                return 0
            log.info("writeInto(%s)" % filename)
            stream = FileOutputStream(filename)
            self.hachoir.writeInto(stream)
        return len(data)

    def read(self, path, size, offset):
        try:
            log.info("read(%s, %s, %s)" % (path, size, offset))
            field = self.getField(path)
            if not field:
                log.info("=> ENOENT")
                return -errno.ENOENT
            if not field.hasValue():
                return ''
        except Exception, xx:
            log.info("ERR: %s" % xx)
            raise
        data = self.fieldValue(field)
        slen = len(data)
        if offset >= slen:
            return ''
        if offset + size > slen:
            size = slen - offset
        data = data[offset:offset+size]
        log.info("=> %s" % repr(data))
        return data

    def stop(self):
        log.info("stop()")

    def truncate(self, *args):
        log.info("truncate(): TODO!")

def main():
    usage="""
Userspace hello example

""" + Fuse.fusage
    server = HelloFS(u'/home/haypo/testcase/KDE_Click.wav',
                     version="%prog " + fuse.__version__,
                     usage=usage,
                     dash_s_do='setsingle')

    server.parse(errex=1)
    server.main()
    server.stop()

if __name__ == '__main__':
    main()
