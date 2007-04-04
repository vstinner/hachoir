from hachoir_core.error import HACHOIR_ERRORS, warning, error

def fault_tolerant(func, *args):
    def safe_func(*args, **kw):
        try:
            func(*args, **kw)
        except HACHOIR_ERRORS, err:
            error("Error when calling %s: %s" % (func.__name__, err))
    return safe_func

def getValue(fieldset, key):
    try:
        field = fieldset[key]
        if field.hasValue():
            return field.value
    except HACHOIR_ERRORS:
        warning("Unable to get value of field: %s/%s" % (fieldset.path, key))
    return None

