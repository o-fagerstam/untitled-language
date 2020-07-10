class Node:
    def __init__(self, id):
        self.children = []
        self.id = id

    def add_child(self, new_child):
        self.children.append(new_child)

    def __str__(self):
        print_tree(self, 0)

    def print_tree(self):
        self.print_tree_recursive(0)

    def print_tree_recursive(self, depth):
        print("\t"*depth + str(self.id))
        for child in self.children:
            child.print_tree_recursive(depth+1)

class ClauseNode(Node):
    def __init__(self, id):
        super().__init__(id)
        self.clause_trees = []

    def add_clause_tree(self, new_tree):
        self.clause_trees.append(new_tree)

    def print_tree(self):
        super().print_tree()
        print("Clause tree children: {{{")
        for tree in self.clause_trees:
            tree.print_tree()
        print("}}}")
