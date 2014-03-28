"""
Functions to display an error (error, warning or information) message.
"""

from hachoir.core.log import log
from hachoir.core.tools import makePrintable
import sys, traceback

def getBacktrace(empty="Empty backtrace."):
    """
    Try to get backtrace as string.
    Returns "Error while trying to get backtrace" on failure.
    """
    try:
        info = sys.exc_info()
        trace = traceback.format_exception(*info)
        if trace[0] != "None\n":
            return "".join(trace)
    except:
        # No i18n here (imagine if i18n function calls error...)
        return "Error while trying to get backtrace"
    return empty


# Error classes which may be raised by Hachoir core
# FIXME: Add EnvironmentError (IOError or OSError) and AssertionError?
# FIXME: Remove ArithmeticError and RuntimeError?
HACHOIR_ERRORS = (LookupError, NameError, AttributeError,
    TypeError, ValueError, ArithmeticError, RuntimeError)

info    = log.info
warning = log.warning
error   = log.error
