"""
Utilities used to convert a field to human classic reprentation of data.
"""

from datetime import datetime, MAXYEAR
from hachoir_core.tools import (
    humanDuration as doHumanDuration,
    humanFilesize as doHumanFilesize,
    humanBitRate as doHumanBitRate,
    timestampUNIX as doTimestampUNIX,
    timestampMac32 as doTimestampMac32,
    durationWin64 as doDurationWin64,
    timestampWin64 as doTimestampWin64,
    humanDatetime,
    alignValue,
)
from types import FunctionType, MethodType
from hachoir_core.i18n import _
from hachoir_core.field import Field

def textHandler(field, handler):
    assert isinstance(handler, (FunctionType, MethodType))
    assert issubclass(field.__class__, Field)
    field.createDisplay = lambda: handler(field)
    return field

def displayHandler(field, handler):
    assert isinstance(handler, (FunctionType, MethodType))
    assert issubclass(field.__class__, Field)
    field.createDisplay = lambda: handler(field.value)
    return field

def timestampWin64(field):
    """
    Convert Windows 64-bit timestamp to string. The timestamp format is
    a 64-bit number which represents number of 100ns since the
    1st January 1601 at 00:00. Result is an unicode string.
    See also durationWin64(). Maximum date is 28 may 60056.

    >>> timestampWin64(type("", (), {"value": 127840491566710000, "size": 64}))
    u'2006-02-10 12:45:56.671000'
    >>> timestampWin64(type("", (), {"value": 0, "size": 64}))
    u'(not set)'
    >>> timestampWin64(type("", (), {"value": (1 << 64)-1, "size": 64}))
    u'invalid date (value=18446744073709551615)'
    """
    assert hasattr(field, "value") and hasattr(field, "size")
    assert field.size == 64
    if field.value == 0:
        return _("(not set)")
    try:
        return humanDatetime(doTimestampWin64(field.value))
    except ValueError:
        return _("invalid date (value=%s)") % field.value

def durationWin64(field):
    """
    Convert Windows 64-bit duration to string. The timestamp format is
    a 64-bit number: number of 100ns. See also timestampWin64().

    >>> durationWin64(type("", (), dict(value=2146280000, size=64)))
    u'3 min 34 sec 628 ms'
    >>> durationWin64(type("", (), dict(value=(1 << 64)-1, size=64)))
    u'58494 years 88 days 5 hours'
    """
    assert hasattr(field, "value") and hasattr(field, "size")
    assert field.size == 64
    delta = doDurationWin64(field.value)
    return doHumanDuration(delta)

def humanFilesize(field):
    """
    Convert a file size to human representation (just call
    hachoir_core.tools.humanFilesize())
    """
    assert hasattr(field, "value") and hasattr(field, "size")
    return doHumanFilesize(field.value)

def humanBitRate(field):
    """
    Convert a bit rate to human representation
    """
    assert hasattr(field, "value") and hasattr(field, "size")
    return doHumanBitRate(field.value)

def timestampUNIX(field):
    """
    Convert an UNIX (32-bit) timestamp to string. The format is the number
    of seconds since the 1st January 1970 at 00:00. Returns unicode string.

    >>> timestampUNIX(type("", (), dict(value=0, size=32)))
    u'1970-01-01 00:00:00'
    >>> timestampUNIX(type("", (), dict(value=1154175644, size=32)))
    u'2006-07-29 12:20:44'
    >>> timestampUNIX(type("", (), dict(value=-1, size=32)))
    u'invalid UNIX timestamp (-1)'
    >>> timestampUNIX(type("", (), dict(value=2147483650, size=32)))
    u'invalid UNIX timestamp (2147483650)'
    """
    assert hasattr(field, "value") and hasattr(field, "size")
    assert field.size == 32
    try:
        timestamp = doTimestampUNIX(field.value)
        return humanDatetime(timestamp)
    except ValueError:
        return u'invalid UNIX timestamp (%s)' % field.value

def timestampMac(field):
    """
    Convert an Mac (32-bit) timestamp to string. The format is the number
    of seconds since the 1st January 1904 (to 2040). Returns unicode string.

    >>> timestampMac(type("", (), dict(value=2843043290, size=32)))
    u'1994-02-02 14:14:50'
    >>> timestampMac(type("", (), dict(value=-1, size=32)))
    u'invalid Mac timestamp (-1)'
    >>> timestampMac(type("", (), dict(value=4294967296, size=32)))
    u'invalid Mac timestamp (4294967296)'
    """
    assert hasattr(field, "value") and hasattr(field, "size")
    assert field.size == 32
    if not(0 <= field.value <= 4294967295):
        return _("invalid Mac timestamp (%s)") % field.value
    return humanDatetime(doTimestampMac32(field.value))

def hexadecimal(field):
    """
    Convert an integer to hexadecimal in lower case. Returns unicode string.

    >>> hexadecimal(type("", (), dict(value=412, size=16)))
    u'0x019c'
    >>> hexadecimal(type("", (), dict(value=0, size=32)))
    u'0x00000000'
    """
    assert hasattr(field, "value") and hasattr(field, "size")
    size = field.size
#    assert 0 < size <= 64 and not size % 8
    padding = alignValue(size, 4) // 4
    pattern = u"0x%%0%ux" % padding
    return pattern % field.value

