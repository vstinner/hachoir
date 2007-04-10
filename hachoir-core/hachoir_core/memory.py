import gc

PAGE_SIZE = 4096

def getTotalMemory():
    """
    Get total size of memory (not swap) in bytes.
    Use /proc/meminfo on Linux.

    Returns None on error. May also raise a ValueError.
    """
    try:
        line = open('/proc/meminfo').readline().strip()
        meminfo = line.split()
    except IOError:
        return None
    if meminfo[2] != 'kB':
        raise ValueError("Don't support %s memory unit" % line[2])
    return int(meminfo[1]) * 1024

def _getProcStatm(index):
    try:
        statm = open('/proc/self/statm').readline().split()
    except IOError:
        return None
    return int(statm[index]) * PAGE_SIZE

def getMaxRSS():
    return _getProcStatm(0)

def getRSS():
    return _getProcStatm(1)

def getData():
    return _getProcStatm(5)

def getMemoryLimit():
    return None

def setMemoryLimit(max_mem, hard_limit=None):
    """
    Set memory limit in bytes.
    Use value 'None' to disable memory limit.

    Return True if limit is set, False on error.
    """
    return False

try:
    from resource import (getpagesize, getrusage,
        getrlimit, setrlimit,
        RUSAGE_SELF, RLIMIT_AS)

    PAGE_SIZE = getpagesize()

    def getMemoryLimit():
        try:
            limit = getrlimit(RLIMIT_AS)[0]
            if 0 < limit:
                limit *= PAGE_SIZE
            return limit
        except ValueError:
            return None

    def setMemoryLimit(max_mem, hard_limit=None):
        if max_mem is None:
            max_mem = -1 # getTotalMem() * 2
            hard_limit = -1
        if hard_limit is None:
            hard_limit = -1
        try:
            setrlimit(RLIMIT_AS, (max_mem, hard_limit))
            return True
        except ValueError:
            return False
except ImportError:
    pass

class MemoryLimit:
    def __init__(self, limit):
        self.limit = limit

    def clearCaches(self):
        gc.collect()
        #import re; re.purge()

    def call(self, func, *args, **kw):
        # First step: clear cache to gain memory
        self.clearCaches()

        # Get total program size
        max_rss = getMaxRSS()
        if max_rss is not None:
            # Get old limit and then set our new memory limit
            old_limit = getMemoryLimit()
            limit = max_rss + self.limit
            limited = setMemoryLimit(limit)
        else:
            limited = False

        try:
            # Call function
            return func(*args, **kw)
        finally:
            # and unset our memory limit
            if limited:
                setMemoryLimit(old_limit)

            # After calling the function: clear all caches
            self.clearCaches()

