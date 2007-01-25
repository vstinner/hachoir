from hachoir_core.tools import (humanDatetime,
    timestampUNIX, timestampMac32, timestampWin64)
from hachoir_core.field import Bits

class GenericTimestamp(Bits):
    def __init__(self, parent, name, size, description=None):
        Bits.__init__(self, parent, name, size, description)

    def createDisplay(self):
        return humanDatetime(self.value)

    def createRawDisplay(self):
        value = Bits.createValue(self)
        return unicode(value)

def timestampFactory(cls_name, handler, size):
    class Timestamp(GenericTimestamp):
        def __init__(self, parent, name, description=None):
            GenericTimestamp.__init__(self, parent, name, size, description)

        def createValue(self):
            value = Bits.createValue(self)
            return handler(value)
    cls = Timestamp
    cls.__name__ = cls_name
    return cls

TimestampUnix32 = timestampFactory("TimestampUnix32", timestampUNIX, 32)
TimestampMac32 = timestampFactory("TimestampUnix32", timestampMac32, 32)
TimestampWin64 = timestampFactory("TimestampWin64", timestampWin64, 64)

