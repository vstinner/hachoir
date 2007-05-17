from sys import platform

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

