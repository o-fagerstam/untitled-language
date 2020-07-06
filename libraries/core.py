#print(msg) -> printf(msg)

def cprint_arg_string(args):
    if len(args) != 1:
        print("ERROR: print() takes one argument")
        quit()
    return args[0]

def cprint(args):
    return "printf(\"" + cprint_arg_string(args) + "\")"

def cprintln(args):
    return "printf(\"" + cprint_arg_string(args) + "\\n\")"

funcs = {"print":cprint, "println":cprintln}
