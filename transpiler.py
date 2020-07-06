import ASTNode
from libraries import core

class Transpiler:
    def __init__(self):
        self.line_depth = 0

    def transpile(self, trees, outfile):
        outcode = []
        for tree in trees:
            res = self.transpile_recursive(tree) + ";\n"
            outcode.append(res)
        with open(outfile, "w") as f:
            f.write("#include <stdio.h>\n")
            f.write("int main() {\n")
            self.line_depth += 1
            for line in outcode:
                f.write("  " * self.line_depth)
                f.write(line)
            f.write("}")

    def transpile_recursive(self, tree):
        if tree.id[1] == "NAME":
            return tree.id[0]
        elif tree.id[1] == "NUM":
            return tree.id[0]
        elif tree.id[1] == "FUNC":
            # If function in library
                # Add library call
            if tree.id[0] in core.funcs:
                return core.funcs[tree.id[0]](self.transpile_arguments(tree.children))
            # Else
                # Make normal call
            return tree.id[0] + "(" + self.transpile_arguments(tree.children) + ")"
        elif tree.id[1] == "INFIX":
            return "(" + self.transpile_recursive(tree.children[0]) + " " + tree.id[0] + " " + self.transpile_recursive(tree.children[1]) + ")"
        elif tree.id[1] == "ASS":
            return self.transpile_recursive(tree.children[0]) + " = " + self.transpile_recursive(tree.children[1])
        elif tree.id[1] == "STR":
            return tree.id[0]

    def transpile_arguments(self, children):
        args = []
        first = True
        for child in children:
            print("transpile_arguments(): found arg " + str(child.id))
            args.append(self.transpile_recursive(child))
        return args
