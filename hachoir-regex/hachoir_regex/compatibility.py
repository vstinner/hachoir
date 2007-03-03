"""
Compatibility functions for old version of Python.

any() function
==============

any() returns True if at least one items is True, or False otherwise.

>>> any([False, True])
True
>>> any([True, True])
True
>>> any([False, False])
False


all() function
==============

all() returns True if all items are True, or False otherwise.
This function is just apply binary and operator (&) on all values.

>>> all([True, True])
True
>>> all([False, True])
False
>>> all([False, False])
False
"""
import operator

# --- any() from Python 2.5 ---
try:
    from __builtin__ import any
except ImportError:
    def any(items):
        for item in items:
            if item:
                return True
        return False

# ---all() from Python 2.5 ---
try:
    from __builtin__ import all
except ImportError:
    def all(items):
        return reduce(operator.__and__, items)

__all__ = ("any", "all")

