from hachoir_core.field import GenericFieldSet

class FieldSet(GenericFieldSet):
    def __init__(self, parent, name, *args, **kw):
        assert issubclass(parent.__class__, GenericFieldSet)
        GenericFieldSet.__init__(self, parent, name, parent.stream, *args, **kw)

