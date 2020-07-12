class Transpilable:
    def __init__(self, name):
        self.name = name
        self.namespace = {}

class TranspiledClass(Transpilable):
    pass

class TranspiledFunc(Transpilable):
    def __init__(self, name, args, return_type):
        super().__init__(name)
        self.args = args
        self.return_type = return_type
