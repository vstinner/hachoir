def getTotalMemory():
    try:
        line = open('/proc/meminfo').readlines()[0].split()
    except IOError:
        return None
    if line[2] != 'kB':
        raise ValueError("Don't support %s memory unit" % line[2])
    return int(line[1]) * 1024

def setMemoryLimit(max_mem):
    """
    Set memory limit using setrlimit(RLIMIT_AS, ...).
    Use value -1 to disable memory limit.

    Return True if limit is set, False on error.
    """
    try:
        from resource import setrlimit, RLIMIT_AS
        try:
            setrlimit(RLIMIT_AS, (max_mem, -1))
        except ValueError:
            return False
    except ImportError:
        return False
    return True

