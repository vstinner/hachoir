from random import randint, choice as random_choice
from array import array

MAX_MIX = 20
MIN_MIX = -MAX_MIX
MIN_COUNT = 15
MAX_COUNT = 2500
MAX_INC = 32
MIN_INC = -MAX_INC

SPECIAL_VALUES_NOENDIAN = (
    "\x00",
    "\x00\x00",
    "\x7f",
    "\x7f\xff",
    "\x7f\xff\xff\xff",
    "\x80",
    "\x80\x00",
    "\x80\x00\x00\x00",
    "\xfe",
    "\xfe\xff",
    "\xfe\xff\xff\xff",
    "\xff",
    "\xff\xff",
    "\xff\xff\xff\xff",
)

SPECIAL_VALUES = []
for item in SPECIAL_VALUES_NOENDIAN:
    SPECIAL_VALUES.append(item)
    itemb = item[::-1]
    if item != itemb:
        SPECIAL_VALUES.append(itemb)

def mangle_replace(data, offset):
    data[offset] = randint(0, 255)

def mangle_increment(data, offset):
    value = data[offset] + randint(MIN_INC, MAX_INC)
    data[offset] = max(min(value, 255), 0)

def mangle_bit(data, offset):
    bit = randint(0, 7)
    if randint(0, 1) == 1:
        value = data[offset] | (1 << bit)
    else:
        value = data[offset] & (~(1 << bit) & 0xFF)
    data[offset] = value

def mangle_special_value(data, offset):
    tlen = len(data) - offset
    text = random_choice(SPECIAL_VALUES)[:tlen]
    data[offset:offset+len(text)] = array("B", text)


def mangle_mix(data, ofs1):
    ofs2 = ofs1 + randint(MIN_MIX, MAX_MIX)
    ofs2 = max(min(ofs2, len(data)-1), 0)
    data[ofs1], data[ofs2] = data[ofs2], data[ofs1]

MANGLE_OPERATIONS = (
    mangle_replace,
    mangle_increment,
    mangle_bit,
    mangle_special_value,
    mangle_mix,
)

def mangle(data, percent, min_count=MIN_COUNT, max_count=MAX_COUNT):
    """
    Mangle data: add few random bytes in input byte array.

    This function is based on an idea of Ilja van Sprundel (file mangle.c).
    """
    hsize = len(data)-1
    max_percent = max(min(percent, 1.0), 0.0001)
    count = int( float(len(data)) * max_percent )
    count = max(count, min_count)
    count = min(count, max_count)
    count = randint(1, count)
    for index in xrange(count):
        operation = random_choice(MANGLE_OPERATIONS)
        offset = randint(0, hsize)
        operation(data, offset)
    return count

