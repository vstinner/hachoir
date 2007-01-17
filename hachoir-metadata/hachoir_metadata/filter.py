class Filter:
    def __init__(self, valid_types, min=None, max=None):
        self.types = valid_types
        self.min = min
        self.max = max

    def __call__(self, value):
        if not isinstance(value, self.types):
            return True
        if self.min is not None and value < self.min:
            return False
        if self.max is not None and self.max < value:
            return False
        return True

class NumberFilter(Filter):
    def __init__(self, min=None, max=None):
        Filter.__init__(self, (int, long, float), min, max)

