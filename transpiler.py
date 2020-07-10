import ASTNode, intermediates
from libraries import core

class Transpiler:
    def __init__(self, debug = False):
        self.debug = debug
        self.classes = {"NOCLS":{}}

    def dbg_print(self, msg):
        if self.debug:
            print(msg)

    def error_print(self, msg):
        print("ERROR: " + msg)
        quit()

    def transpile(self, trees, outfile):
        self.line_depth = 0
        self.preamble = []
        self.body = []
        for tree in trees:
            if self.debug:
                print("Transpiling tree:")
                tree.print_tree()
            if isinstance(tree, ASTNode.ClauseNode) and tree.id[1] == "CLSDEF":
                self.dbg_print("transpile(): This is a clause node")
                newclass = self.transpile_class(tree)
            else:
                line = self.transpile_recursive(tree, root = True)
                self.body.append(line)
        with open(outfile, "w", encoding='utf-8') as f:
            # Preamble
            f.write("#include <stdio.h>\n")
            f.write("#include \"clibraries/objects.h\"\n")
            for line in self.preamble:
                f.write(line)
                f.write("\n")
            # Main
            f.write("int main() {\n")
            self.line_depth += 1
            for line in self.body:
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
            self.dbg_print(f"Function " + tree.id[0] + " in core.funcs: " + str(tree.id[0] in core.funcs))
            if tree.id[0] in core.funcs:
                res = core.funcs[tree.id[0]](self.transpile_arguments(tree.children))
            else:
                # Make normal call
                res = " ".join(self.transpile_modifiers(tree.children)) + " " +  tree.id[0] + "(" +\
                    ", ".join(self.transpile_arguments(tree.children)) + ")"
        elif tree.id[1] == "CLS":
            res = " ".join(self.transpile_modifiers(tree.children)) + " " + tree.id[0]
            line_end = ""
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
            if child.id[1] != "MOD":
                self.dbg_print("transpile_arguments(): found arg " + str(child.id))
                args.append(self.transpile_recursive(child))
        return args

    def transpile_modifiers(self, children):
        args = []
        for child in children:
            if child.id[1] == "MOD":
                args.append(child.id[0])
        return args

    def transpile_class(self, tree):
        attributes = []
        functions = {}
        for child in tree.clause_trees:
            if child.id[1] == "NAME":
                # Attributes are saved for later so we can check against them when manipulating the object.
                # TODO: Add attributes to preamble as a struct
                attributes.append(child)
                self.dbg_print("Found attribute:")
                child.print_tree()
                self.preamble.append(f"struct obj__{tree.id[0]}" + "{")
                for attribute in attributes:
                    self.preamble.append(self.transpile_attribute(child) + ";")
                self.preamble.append("};")
        for child in tree.clause_trees:
            if child.id[1] == "FUNCDEF":
                # Functions need to be written into the preamble
                functions[child.id[0]] = self.make_func_object(child)
                # As well as saved so we can access them later
                self.preamble += self.transpile_func_def(child, tree.id[0])
                #TODO: Define functions here!
                pass
            elif child.id[1] in ("OPEN_CLAUSE", "CLOSE_CLAUSE", "NAME"):
                pass
            else:
                self.error_print(f"transpile_class(): Unexpected tree {str(child.id)} in class {tree.id[0]}")
        return intermediates.TranspiledClass(attributes, functions)

    def transpile_attribute(self, tree):
        res = []
        if tree.id[1] != "NAME":
            self.error_print(f"transpile_attributes(): Unknown symbol {tree.id}")
        else:
            for child in tree.children:
                if child.id[1] != "MOD":
                    self.error_print(f"transpile_argument(): Argument {tree.id} has non-modifier child")

                if child.id[0] in ("int"):
                    res.append(child.id[0])
                else:
                    self.error_print(f"transpile_argument(): Argument {tree.id} has unknown modifier {child.id[0]}")

        res.append(tree.id[0])

        return " ".join(res)

    def make_func_object(self, tree):
        args = []
        return_value = []
        for child in tree.children:
            if child.id[1] == "NAME":
                args.append(child)
            elif child.id[1] == "MOD":
                return_value.append(child)
        return intermediates.TranspiledFunc(args, return_value)

    def transpile_func_def(self, tree, parent_name):
        self.dbg_print(f"transpile_func_def(): Transpiling {tree.id}")
        lines = []
        attributes = [self.transpile_attribute(child) for child in tree.children if child.id[1] != "MOD"]
        modifiers = [child.id[0] for child in tree.children if child.id[1] == "MOD"]
        lines.append(f"{' '.join(modifiers)} {parent_name}__{tree.id[0]}({', '.join(attributes)})")
        for c_tree in tree.clause_trees:
            lines.append(self.transpile_recursive(c_tree, root = True))
        return lines
