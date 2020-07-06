import ASTNode

class Transpiler:
    def transpile(self, trees, outfile):
        outcode = []
        for tree in trees:
            res = self.transpile_recursive(tree) + ";\n"
            outcode.append(res)
        with open(outfile, "w") as f:
            for line in outcode:
                f.write(line)

    def transpile_recursive(self, tree):
        if tree.id[1] == "NAME":
            return tree.id[0]
        elif tree.id[1] == "NUM":
            return tree.id[0]
        elif tree.id[1] == "FUNC":
            return tree.id[0] + "(" + self.transpile_arguments(tree.children) + ")"
        elif tree.id[1] == "INFIX":
            return "(" + self.transpile_recursive(tree.children[0]) + " " + tree.id[0] + " " + self.transpile_recursive(tree.children[1]) + ")"
        elif tree.id[1] == "ASS":
            return self.transpile_recursive(tree.children[0]) + " = " + self.transpile_recursive(tree.children[1])

    def transpile_arguments(self, children):
        args = []
        first = True
        for child in children:
            args.append(self.transpile_recursive(child))
        return ", ".join(args)
