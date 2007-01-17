"""
Functions to display an error (error, warning or information) message.
"""

import hachoir_core.config as config
from hachoir_core.log import log
from hachoir_core.tools import makePrintable
import sys
import traceback

def getBacktrace():
    """
    Try to get backtrace as string.
    Returns "Error while trying to get backtrace" on failure.
    """
    try:
        info = sys.exc_info()
        trace = traceback.format_exception(*info)
        sys.exc_clear()
        if trace[0] != "None\n":
            return "".join(trace)
        else:
            # No i18n here (imagine if i18n function calls error...)
            return "Empty backtrace."
    except:
        # No i18n here (imagine if i18n function calls error...)
        return "Error while trying to get backtrace"

class HachoirError(Exception):
    """
    Parent of all errors in Hachoir library
    """
    def __init__(self, message):
        if not isinstance(message, unicode):
            message = makePrintable(message, "ISO-8859-1", to_unicode=True)
        self.message = message

    def __str__(self):
        return makePrintable(self.message, "ASCII")

    def __unicode__(self):
        return self.message

# Error classes which may be raised by Hachoir core
# FIXME: Add EnvironmentError (IOError or OSError) and AssertionError?
# FIXME: Remove ArithmeticError and RuntimeError?
HACHOIR_ERRORS = (HachoirError, LookupError, NameError, AttributeError,
    TypeError, ValueError, ArithmeticError, RuntimeError)

def info(message):
    """
    Display information message. Skip it in config.quiet is set.
    """
    if config.quiet:
        return
    if config.verbose:
        log.info(message)

def warning(message):
    """
    Display warning message. Skip it in config.quiet is set.
    """
    if config.quiet:
        return
    if config.debug:
        message += "\n\n" + getBacktrace()
    log.warning(message)

def error(message):
    """
    Display error message. If config.quiet or config.set is set, add
    backtrace to the message
    """
    if config.verbose or config.debug:
        message += "\n\n" + getBacktrace()
    log.error(message)

