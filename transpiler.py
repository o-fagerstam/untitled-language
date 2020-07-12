import ASTNode, intermediates
from libraries import core

class Transpiler:
    def __init__(self, debug = False):
        self.debug = debug
        self.namespace = {}

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
                if tree.id[1] == "CLSDEF":
                    self.dbg_print("transpile(): This is a class definition node")
                    self.namespace[tree.id[0]] = self.transpile_class(tree)
                elif tree.id[1] == "FUNCDEF":
                    self.dbg_print("transpile(): This is a function definition node")
                    self.namespace[tree.id[0]] = self.make_func_object(tree)
                    self.transpile_func_def(tree)
            else:
                line = self.transpile_recursive(self, tree, root = True)
                self.body.append(line)
        with open(outfile, "w", encoding='utf-8') as f:
            # Preamble
            f.write("#include <stdio.h>\n")
            f.write("#include <stdlib.h>\n")
            f.write("#include \"clibraries/core.h\"\n")
            for line in self.preamble:
                f.write(line)
            # Main
            f.write("int main() {\n")
            self.line_depth += 1
            for line in self.body:
                f.write(line)
            f.write("}")

    def transpile_recursive(self, parent, tree, root = False):
        self.dbg_print("transpile_recursive(): Transpiling node " + str(tree.id))
        if root:
            line_start = "  " * self.line_depth
            line_end = ";\n"
        else:
            line_start = ""
            line_end = ""
        if tree.id[1] == "NAME":
            if root:
                # This is a variable declaration
                path = tree.id[0].split(".")
                # Check that we are really in the right parent
                if len(path) > 1:
                    assert path[-2] == parent.name
                # Add name to parent's namespace
                parent.namespace[path[-1]] = tree
            if tree.children:
                modifiers = " ".join(self.transpile_modifiers(tree.children))
                self.dbg_print("Modifiers were" + str(self.get_modifiers(tree)))
                res = modifiers + " " + tree.id[0]
            else:
                res = self.transpile_name_path(tree)
        elif tree.id[1] == "NUM":
            res = tree.id[0]
        elif tree.id[1] == "FUNC":
            self.dbg_print("Transpiling function " + tree.id[0])
            # If function in library
                # Add library call
            self.dbg_print(f"Function " + tree.id[0] + " in core.funcs: " + str(tree.id[0] in core.funcs))
            if tree.id[0] in core.funcs:
                res = core.funcs[tree.id[0]](self.transpile_arguments(tree.children))
            else:
                # Make normal call
                path = tree.id[0].split(".")
                namespaces = []
                namespaces.append(parent.namespace)
                if parent != self:
                    append(self.namespace)
                parent_class = self.get_class(path[0], namespaces)
                # Check if we are calling a class or an instance of a class
                if parent_class.name == path[0]:
                    object_name = ""
                else:
                    object_name = path[0]
                    path[0] = parent_class.name
                self.dbg_print("Found parent class " + parent_class.name)
                # This search isn't necessary, but we keep it to make sure the function exists
                fn = self.namespace_search(path, namespaces)
                self.dbg_print("Namespace search found function: " + fn.name)
                res = "__".join(path) + "(" + ", ".join([object_name] + self.transpile_arguments(tree.children)) + ")"

        elif tree.id[1] == "CLS":
            res = " ".join(self.transpile_modifiers(tree.children)) + " " + tree.id[0]
            line_end = ""
        elif tree.id[1] == "INFIX":
            res = "(" + self.transpile_recursive(self, tree.children[0]) + " " + tree.id[0] + " "\
            + self.transpile_recursive(self, tree.children[1]) + ")"
        elif tree.id[1] == "ASS":
            res = self.transpile_recursive(self, tree.children[0]) + " = " + self.transpile_recursive(self, tree.children[1])
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
                args.append(self.transpile_recursive(self, child))
        return args

    def transpile_modifiers(self, children):
        args = []
        for child in children:
            if child.id[1] == "MOD":
                args.append(child.id[0])
            elif child.id[1] == "NAME":
                args.append(f"struct obj__{child.id[0]}*")
        return args

    def transpile_class(self, tree):
        new_class = intermediates.TranspiledClass(tree.id[0])
        has_make = False
        self.preamble.append(f"struct obj__{tree.id[0]}" + "{\n")
        for child in tree.clause_trees:
            if child.id[1] == "NAME":
                # Attributes are saved for later so we can check against them when manipulating the object.
                new_class.namespace[child.id[0]] = child
                self.dbg_print("Found attribute:")
                child.print_tree()
        self.dbg_print([str(x.id) for x in new_class.namespace.values()])
        for attribute in new_class.namespace.values():
            self.preamble.append(self.transpile_attribute(attribute) + ";\n")
        self.preamble.append("};\n")
        for child in tree.clause_trees:
            if child.id[1] == "FUNCDEF":
                if child.id[0] != "make":
                    # Functions need to be written into the preamble
                    new_class.namespace[child.id[0]] = self.make_func_object(child)
                    # As well as saved so we can access them later
                    self.preamble += self.transpile_func_def(child, tree.id[0])
                else:
                    # The make functions take some special parameters
                    new_class.namespace[child.id[0]] = self.make_func_object(child, make_type = tree.id[0])
                    self.preamble += self.transpile_make_def(child, tree.id[0])

            elif child.id[1] in ("OPEN_CLAUSE", "CLOSE_CLAUSE", "NAME"):
                pass
            else:
                self.error_print(f"transpile_class(): Unexpected tree {str(child.id)} in class {tree.id[0]}")
        return new_class

    def transpile_attribute(self, tree):
        '''Transpiles a single attribute declaration for a class defintion.
        tree = The attribute tree that is to be transpiled.
        return value: String of transpiled attribute.'''
        self.dbg_print("Transpiling attributes of tree: ")
        if self.debug:
            tree.print_tree()
        res = []
        if tree.id[1] != "NAME":
            self.error_print(f"transpile_attribute(): Unknown symbol {tree.id}")
        else:
            for child in tree.children:
                if child.id[1] not in ("MOD", "NAME"):
                    self.error_print(f"transpile_attribute(): Argument {tree.id} has non-modifier child")

                if child.id[1] == "NAME":
                    res.append(f"struct obj__{child.id[0]}*")
                elif child.id[0] in ("int"):
                    res.append(child.id[0])
                else:
                    self.error_print(f"transpile_attribute(): Argument {tree.id} has unknown modifier {child.id[0]}")

        res.append(tree.id[0])

        return " ".join(res)

    def make_func_object(self, tree, make_type = ""):
        '''Makes a TranspiledFunc object out of a function declaration tree.
        tree: The function declaration tree.
        make_type: Optional; gives the name of the parent class if this is a make function'''
        namespace = {}
        args = []
        return_value = None
        for child in tree.children:
            if child.id[1] == "NAME":
                args.append(child)
            elif child.id[1] == "MOD":
                if not make_type:
                    return_value = child
                else:
                    self.error_print("make_func_object(): make() does not take modifiers!")
            else:
                self.error_print(f"make_func_object(): Unknown argument {str(child.id)}")
        for c_tree in tree.clause_trees:
            if c_tree.id[1] == "NAME":
                namespace[c_tree.id[0]] = c_tree
        new_func = intermediates.TranspiledFunc(tree.id[0], args, return_value)
        new_func.namespace = namespace
        return new_func

    def transpile_func_def(self, tree, parent_name = "NOCLS"):
        '''Transpiles a function declaration tree into C code.
        NB: Use transpile_make_def() instead for the make function.
        tree: The function declaration tree.
        parent_name: Name of the parent class.'''
        self.dbg_print(f"transpile_func_def(): Transpiling {tree.id[0]}")
        lines = []
        attributes = [self.transpile_attribute(child) for child in tree.children if child.id[1] != "MOD"]
        modifiers = [child.id[0] for child in tree.children if child.id[1] == "MOD"]
        lines.append(f"{' '.join(modifiers)} {parent_name}__{tree.id[0]}({', '.join([f'struct obj__{parent_name}* __SELF__'] + attributes)})")
        for c_tree in tree.clause_trees:
            lines.append(self.transpile_recursive(self, c_tree, root = True))
        return lines

    def transpile_make_def(self, tree, parent_name):
        '''Transpiles a make function tree into C code.
        tree: The function declaration tree.
        parent_name: Name of the parent tree.'''
        self.dbg_print(f"transpile_make_def(): Transpiling {tree.id[0]}")
        lines = []
        attributes = [self.transpile_attribute(child) for child in tree.children if child.id[1] != "MOD"]
        lines.append(f"struct obj__{parent_name}* {parent_name}__{tree.id[0]}({', '.join(attributes)})")
        clause_tree_len = len(tree.clause_trees)
        for i, c_tree in enumerate(tree.clause_trees):
            if i == 1:
                lines.append(f"struct obj__{parent_name}* __new__ = malloc(sizeof(struct obj__{parent_name}));\n")
                lines.append(f"__CORE__malloc_null_chk(__new__, \"{tree.id[0]}\");\n")
            if i == clause_tree_len-1:
                lines.append(f"return __new__;\n")
            lines.append(self.transpile_recursive(self, c_tree, root = True))
        return lines

    def transpile_name_path(self, tree):
        '''Turns a dot-separated name path into an underscore-separated path.'''
        return tree.id[0].replace(".", "__")

    def namespace_search(self, path, namespaces):
        self.dbg_print("Searching for " + path[0] + " in " + str(namespaces))
        if len(path) == 1:
            for ns in namespaces:
                if path[0] in ns:
                    return ns[path[0]]
            self.error_print(f"{path[0]} not in namespace")
        else:
            for ns in namespaces:
                if path[0] in ns:
                    return self.namespace_search(path[1:], [ns[path[0]].namespace])
            self.error_print(f"{path[0]} not in namespace")

    def get_class(self, name, namespaces):
        self.dbg_print("Getting class of name " + name)
        for ns in namespaces:
            if name in ns:
                if isinstance(ns[name], ASTNode.Node):
                    name_node = ns[name]
                    type = name_node.children[0].id[0]
                    self.dbg_print(f"{name} is an instance of {type}")
                    return self.namespace[type]
                else:
                    return self.namespace[name]
            else:
                self.dbg_print(f"Failed to find class of name {name}.")

    def get_modifiers(self, tree):
        return [child.id[0] for child in tree.children if child in ("MOD", "NAME")]
