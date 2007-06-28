def runProfiler(func, args=tuple(), kw={}, verbose=True, nb_func=25, sort_by=('cumulative', 'calls')):
    import hotshot, hotshot.stats
    from os import unlink
    profile_filename = "/tmp/profiler"
    prof = hotshot.Profile(profile_filename)
    try:
        if verbose:
            print "[+] Run profiler"
        result = prof.runcall(func, *args, **kw)
        prof.close()
        if verbose:
            print "[+] Stop profiler"
            print "[+] Process data..."
        stat = hotshot.stats.load(profile_filename)
        if verbose:
            print "[+] Strip..."
        stat.strip_dirs()
        if verbose:
            print "[+] Sort data..."
        stat.sort_stats(*sort_by)
        if verbose:
            print
            print "[+] Display statistics"
            print
        stat.print_stats(nb_func)
        return result
    finally:
        unlink(profile_filename)

