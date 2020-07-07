import ASTNode
from libraries import core

class Transpiler:
    def __init__(self, debug = False):
        self.debug = debug

    def dbg_print(self, msg):
        if self.debug:
            print(msg)

    def transpile(self, trees, outfile):
        self.line_depth = 0
        with open(outfile, "w", encoding='utf-8') as f:
            f.write("#include <stdio.h>\n")
            f.write("int main() {\n")
            self.line_depth += 1
            for tree in trees:
                if self.debug:
                    print("Transpiling tree:")
                    tree.print_tree()
                line = self.transpile_recursive(tree, root = True)
                f.write(line)
            f.write("}")

    def transpile_recursive(self, tree, root = False):
        if root:
            line_start = "  " * self.line_depth
            line_end = ";\n"
        else:
            line_start = ""
            line_end = ""
        if tree.id[1] == "NAME":
            if tree.children:
                res = " ".join(self.transpile_modifiers(tree.children)) + " " + tree.id[0]
            else:
                res = tree.id[0]
        elif tree.id[1] == "NUM":
            res = tree.id[0]
        elif tree.id[1] == "FUNC":
            # If function in library
                # Add library call
            self.dbg_print(f"Function" + tree.id[0] + " in core.funcs: " + str(tree.id[0] in core.funcs))
            if tree.id[0] in core.funcs:
                res = core.funcs[tree.id[0]](self.transpile_arguments(tree.children))
            else:
                # Make normal call
                res = tree.id[0] + "(" + ", ".join(self.transpile_arguments(tree.children)) + ")"
        elif tree.id[1] == "INFIX":
            res = "(" + self.transpile_recursive(tree.children[0]) + " " + tree.id[0] + " "\
            + self.transpile_recursive(tree.children[1]) + ")"
        elif tree.id[1] == "ASS":
            res = self.transpile_recursive(tree.children[0]) + " = " + self.transpile_recursive(tree.children[1])
        elif tree.id[1] == "STR":
            res = tree.id[0]
        elif tree.id[1] == "FOR":
            res = "for(" + "; ".join(self.transpile_arguments(tree.children)) + ") "
            line_end = ""
        elif tree.id[1] == "OPEN_CLAUSE":
            self.line_depth += 1
            line_start = ""
            res = "{"
            line_end = "\n"
        elif tree.id[1] == "CLOSE_CLAUSE":
            self.line_depth -= 1
            res = "}"
            line_end = "\n"

        return line_start + res + line_end

    def transpile_arguments(self, children):
        args = []
        first = True
        for child in children:
            self.dbg_print("transpile_arguments(): found arg " + str(child.id))
            args.append(self.transpile_recursive(child))
        return args

    def transpile_modifiers(self, children):
        args = []
        for child in children:
            args.append(child.id[0])
        return args
