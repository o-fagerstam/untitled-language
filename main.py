import sys, getopt, re

DEBUG = False

def debug_print(msg):
    if DEBUG:
        print(msg)

class Master:
    def __init__(self):
        inputfile = ''
        self.scriptlines = ''
        try:
            opts, args = getopt.getopt(sys.argv[1:], "di:",["ifile=","debug"])
        except getopt.GetoptError:
            print(f"usage: {sys.argv[0]} -i <inputfile>")
            sys.exit()
        for opt, arg in opts:
            if opt == "-d":
                global DEBUG
                DEBUG = True
            elif opt in ("-i", "--ifile"):
                self.scriptlines = [line.rstrip() for line in open(arg)]
        self.current_msgs = []
        self.next_msgs = []
        self.allobjects = {}
        self.parse()

    def parse(self):
        for line in self.scriptlines:
            if line == "":
                pass
            debug_print(line)
            if line[:3] == "cls":


class IntClass:
    def __init__(self):
        self._values = {}
        self._methods = {}

    def add_value(self, name, value='')
        self._values[name] = value

    def add_method(self, name, args)
        self._methods[name] = [name] + args

class RealObject:
    def __init__(self):
        self._values = {}

    def message(self, to, content):
        master.add_message(self, to, content)


class Message:
    def __init__(self, sender, to, content):
        self.sender = sender
        self.to = to
        self.content = content

master = Master()
