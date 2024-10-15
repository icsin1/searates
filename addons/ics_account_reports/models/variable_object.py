

class VariableObject(dict):

    def __getattr__(self, attr):
        return self.get(attr, False)
