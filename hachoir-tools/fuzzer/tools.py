from ConfigParser import RawConfigParser
from sys import platform
from errno import EEXIST
from os import mkdir, unlink, listdir, path

class ConfigParser(RawConfigParser):
    def get(self, section, option):
        value = RawConfigParser.get(self, section, option)
        return value.strip()

if platform == 'win32':
    from win32process import (GetCurrentProcess, SetPriorityClass,
        BELOW_NORMAL_PRIORITY_CLASS)

    def beNice():
        process = GetCurrentProcess()
        # FIXME: Not supported on Windows 95/98/Me/NT: ignore error?
        # which error?
        SetPriorityClass(process, BELOW_NORMAL_PRIORITY_CLASS)

    OS_ERRORS = (OSError, WindowsError)
else:
    from os import nice

    def beNice():
        nice(19)

    OS_ERRORS = OSError

try:
    import sha
    def generateUniqueID(data):
        return sha.new(data).hexdigest()
except ImportError:
    def generateUniqueID(data):
        generateUniqueID.sequence += 1
        return generateUniqueID.sequence
    generateUniqueID.sequence = 0

def getFilesize(file):
    file.seek(0, 2)
    size = file.tell()
    file.seek(0, 0)
    return size

def safeMkdir(dirname):
    try:
        mkdir(dirname)
    except OS_ERRORS, err:
        if err.errno == EEXIST:
            return
        else:
            raise

def cleanupDir(dirname):
    try:
        files = listdir(dirname)
    except OSError:
        return
    for file in files:
        filename = path.join(dirname, file)
        unlink(filename)

