class TranspiledClass:
    def __init__(self, attributes, functions):
        self.attributes = attributes
        self.functions = functions

class TranspiledFunc:
    def __init__(self, arguments, return_type):
        self.arguments = arguments
        self.return_type = return_type
