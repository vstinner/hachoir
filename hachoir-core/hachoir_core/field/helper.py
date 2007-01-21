from hachoir_core.field import (FieldError,
    RawBits, RawBytes,
    PaddingBits, PaddingBytes,
    NullBits, NullBytes,
    GenericString, GenericInteger)
from hachoir_core.stream import FileOutputStream

def createRawField(parent, size, name="raw[]", description=None):
    if size <= 0:
        raise FieldError("Unable to create raw field of %s bits" % size)
    if (size % 8) == 0:
        return RawBytes(parent, name, size/8, description)
    else:
        return RawBits(parent, name, size, description)

def createPaddingField(parent, nbits, name="padding[]", description=None):
    if nbits <= 0:
        raise FieldError("Unable to create padding of %s bits" % nbits)
    if (nbits % 8) == 0:
        return PaddingBytes(parent, name, nbits/8, description)
    else:
        return PaddingBits(parent, name, nbits, description)

def createNullField(parent, nbits, name="padding[]", description=None):
    if nbits <= 0:
        raise FieldError("Unable to create null padding of %s bits" % nbits)
    if (nbits % 8) == 0:
        return NullBytes(parent, name, nbits/8, description)
    else:
        return NullBits(parent, name, nbits, description)

def isString(field):
    return issubclass(field.__class__, GenericString)

def isInteger(field):
    return issubclass(field.__class__, GenericInteger)

def writeIntoFile(fieldset, filename):
    output = FileOutputStream(filename)
    fieldset.writeInto(output)

def hasValue(field):
    return hasattr(field, "createValue")
