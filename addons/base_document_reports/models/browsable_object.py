
class BrowsableObject(object):
    def __init__(self, dict):
        self.dict = dict

    def __getattr__(self, attr):
        return attr in self.dict and self.dict.__getitem__(attr) or ''
