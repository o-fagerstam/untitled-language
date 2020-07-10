
import lexer, ASTNode

PRIORITIES = {"ASS":0, "INFIX":1, "NAME":2, "FOR":2, "MOD":1000, "CLS":1000, "DEF":1000, "NUM":1000,\
"STR":1000, "COMMA":1001, "OPEN_CLAUSE":1001, "CLOSE_CLAUSE":1001, "DOT":1001 }


class Parser:
    def __init__(self, debug = False):
        self.trees = []
        self.DEBUG = debug
        self.current_line = None

    def dbg_print(self, msg):
        if self.DEBUG:
            print(msg)

    def line_error_print(self, line_ID, message):
        self.dbg_print(f"Error on line {line_ID}: {message}")

    def parse_file(self, filename):
        with open(filename, "r") as f:
            code = f.read()
        return self.parse_code(code)

    def parse_code(self, code):
        l = lexer.Lexer(debug = self.DEBUG)
        symbols = l.lex(code)
        self.dbg_print("symbols: " + str(symbols))
        trees = self.parse_symbols(symbols)
        return trees

    def parse_symbols(self, symbols):
        def add_newline(line, trees):
            newtree = self.create_tree(line)
            trees.append(newtree)
            if self.DEBUG:
                newtree.print_tree()
            line.clear()
            self.current_line += 1
        def add_sameline(line, trees):
            newtree = self.create_tree(line)
            trees.append(newtree)
            if self.DEBUG:
                newtree.print_tree()
            line.clear()
        def add_clausetree(newtree, trees):
            trees.append(newtree)
            if self.DEBUG:
                newtree.print_tree()
            line.clear()

        trees = []
        line = []
        self.current_line = 1
        i = 0
        while i < len(symbols):
            symbol = symbols[i]
            if symbol[1] == "END":
                add_newline(line, trees)
            elif symbol[1] == "OPEN_CLAUSE":
                if line:
                    add_sameline(line, trees)
                line.append(symbol)
                add_newline(line, trees)
            elif symbol[1] == "CLOSE_CLAUSE":
                if line:
                    self.line_error_print(self.current_line, "Expected ; at end of line")
                    quit()
                line.append(symbol)
                add_newline(line, trees)
            elif symbol[1] in ("CLS", "DEF"):
                self.dbg_print("Clause symbol is " + symbol[1])
                clause_open = False
                clause_depth = 0
                while not (clause_open and clause_depth == 0):
                    i += 1
                    search_symbol = symbols[i]
                    line.append(search_symbol)
                    if search_symbol[1] == "OPEN_CLAUSE":
                        clause_open = True
                        clause_depth += 1
                    elif search_symbol[1] == "CLOSE_CLAUSE":
                        clause_depth -= 1
                self.dbg_print("Clause tree line is: " + str(line))
                if symbol[1] == "CLS":
                    class_tree = self.create_clause_tree(line, "CLSDEF")
                    add_clausetree(class_tree, trees)
                elif symbol[1] == "DEF":
                    func_tree = self.create_clause_tree(line, "FUNCDEF")
                    add_clausetree(func_tree, trees)
            else:
                line.append(symbol)
            i += 1

        return trees

    def get_parenthesis_before(self, line):
        self.dbg_print("get_parenthesis_before(): " + str(line))
        if line[-1][1] != "CLOSE_PAREN":
            return line
        else:
            paren_level = 1
            for pos in range(len(line)-2, -1, -1):
                if line[pos][1] == "CLOSE_PAREN":
                    paren_level += 1
                elif line[pos][1] == "OPEN_PAREN":
                    paren_level -= 1

                if paren_level == 0:
                    if pos != 0 and line[pos-1][1] == "NAME":
                        # If there is a name before the beginning of the parenthesis, this was a function call.
                        # So we send the whole line back
                        return line
                    # Else it was a "true" parenthesis.
                    ret = line[pos+1:-1]
                    self.dbg_print("get_parenthesis_before(): Returning " + str(ret))
                    return ret

    def get_parenthesis_after(self, line):
        self.dbg_print("get_parenthesis_after(): " + str(line))
        if line[0][1] != "OPEN_PAREN":
            return line
        else:
            paren_level = 1
            for pos in range(1, len(line)):
                if line[pos][1] == "OPEN_PAREN":
                    paren_level += 1
                elif line[pos][1] == "CLOSE_PAREN":
                    paren_level -= 1

                if paren_level == 0:
                    ret = line[1:pos]
                    self.dbg_print("get_parenthesis_before(): Returning " + str(ret))
                    return ret

    def get_weighted_priority(self, symbol, paren_level):
        return PRIORITIES[symbol[1]] + paren_level * 5

    def make_args(self, line):
        self.dbg_print("make_args():" + str(line))
        paren_level = 0

        for i, symbol in enumerate(line):
            if symbol[1] == "OPEN_PAREN":
                paren_level += 1
            elif symbol[1] == "CLOSE_PAREN":
                paren_level -= 1
            if paren_level == 0 :
                func_end_pos = i
                break

        if i == 1:
            # If i==1 we have an empty parenthesis ()
            return []

        # Then we make a list of arguments
        args = []
        current_arg = []
        arg_start = 0
        self.dbg_print("make_args(): Finding args in " + str(line[1:func_end_pos]))
        for i, symbol in enumerate(line[1:func_end_pos]):
            if symbol[1] == "COMMA":
                args.append(current_arg)
                current_arg = []
            else:
                current_arg.append(symbol)
        args.append(current_arg)
        return args


    def create_tree(self, line):
        self.dbg_print("create_tree():" + str(line))
        top = None
        paren_level = 0

        # Find highest priority symbol
        highest_priority_pos = None
        highest_priority_value = None
        for pos, symbol in enumerate(line):

            if symbol[1] == "OPEN_PAREN":
                paren_level += 1

            elif symbol[1] == "CLOSE_PAREN":
                paren_level -= 1

            else:
                if highest_priority_pos == None:
                    highest_priority_pos = pos
                    highest_priority_value = self.get_weighted_priority(symbol, paren_level)
                else:
                    if self.get_weighted_priority(symbol, paren_level) <= highest_priority_value:
                        highest_priority_pos = pos
                        highest_priority_value = self.get_weighted_priority(symbol, paren_level)

        dot_search_end = False
        last_was_dot = False
        while line[highest_priority_pos][1] in ("NAME", "DOT") and highest_priority_pos > 0 and (not dot_search_end):
            self.dbg_print("Looking at " + str(line[highest_priority_pos-1]))
            if line[highest_priority_pos-1][1] == "DOT":
                last_was_dot = True
                highest_priority_pos -= 1
            else:
                if last_was_dot:
                    highest_priority_pos -= 1
                else:
                    dot_search_end = True
                last_was_dot = False

        # Recursively build tree
        self.dbg_print("create_tree(): Highest priority is " + str(line[highest_priority_pos]) + " pos " + str(highest_priority_pos))
        top = ASTNode.Node(line[highest_priority_pos])
        if top.id[1] == "NUM":
            pass
        elif top.id[1] == "NAME":
            # Check for modifiers first
            modifiers = []
            if highest_priority_pos != 0:
                for i in range(highest_priority_pos-1, -1, -1):
                    if line[i][1] == "MOD":
                        modifiers.append(line[i])
                    else:
                        break
                for i in range(len(modifiers)-1, -1, -1):
                    top.add_child(self.create_tree([modifiers[i]]))

            if highest_priority_pos > 0 and "CLS" in (x[1] for x in line[:highest_priority_pos]):
                # If there is a CLS label before, this is a class
                top.id = (top.id[0], "CLS")
                for arg in self.make_args(line[highest_priority_pos+1:]):
                    top.add_child(self.create_tree(arg))

            elif highest_priority_pos+1 <= len(line)-1 and line[highest_priority_pos+1][1] == "OPEN_PAREN":
                # Else if there is an opening parenthesis after, this is a function.
                top.id = (top.id[0], "FUNC")
                for arg in self.make_args(line[highest_priority_pos+1:]):
                    top.add_child(self.create_tree(arg))

            elif highest_priority_pos+1 <= len(line)-1 and line[highest_priority_pos+1][1] == "DOT":
                # Else if there is a dot following, this is an object/class attribute path
                self.dbg_print("GOT HERE ")
                self.dbg_print("Dot searching children from " + str(line[highest_priority_pos]))
                self.dbg_print("In line " + str(line))
                end_pos = highest_priority_pos + 2
                last_was_dot = True
                current_paren_level = 0
                while end_pos < len(line) and (last_was_dot or current_paren_level != 0 or line[end_pos][1] in ("OPEN_PAREN", "DOT")):
                    self.dbg_print("Looking at" + str(line[end_pos]))
                    if line[end_pos][1] == "OPEN_PAREN":
                        current_paren_level += 1
                    elif line[end_pos][1] == "CLOSE_PAREN":
                        current_paren_level -= 1
                    if line[end_pos][1] == "DOT":
                        last_was_dot = True
                    else:
                        last_was_dot = False
                    end_pos += 1
                top.add_child(self.create_tree(line[highest_priority_pos+2:end_pos+1]))


            else:
                # Else, it is a variable
                pass

        elif top.id[1] == "MOD":
            pass

        elif top.id[1] == "INFIX":
            top.add_child(self.create_tree(self.get_parenthesis_before(line[:highest_priority_pos])))
            top.add_child(self.create_tree(self.get_parenthesis_after(line[highest_priority_pos+1:])))

        elif top.id[1] == "ASS":
            top.add_child(self.create_tree(self.get_parenthesis_before(line[:highest_priority_pos])))
            top.add_child(self.create_tree(line[highest_priority_pos+1:]))

        elif top.id[1] == "OPEN_CLAUSE":
            pass

        elif top.id[1] == "CLOSE_CLAUSE":
            pass

        elif top.id[1] == "STR":
            pass

        elif top.id[1] == "FOR":
            if highest_priority_pos + 1 >= len(line) or line[highest_priority_pos+1][1] != "OPEN_PAREN":
                self.line_error_print(self.current_line, "Expected parenthesis after for statement")
                quit()
            current_paren_level = 1
            commas = [highest_priority_pos+1]
            for i, symbol in enumerate(line[highest_priority_pos+2:]):
                if symbol[1] == "COMMA" and current_paren_level == 1:
                    commas.append(i + highest_priority_pos + 2)
                elif symbol[1] == "OPEN_PAREN":
                    current_paren_level += 1
                elif symbol[1] == "CLOSE_PAREN":
                    current_paren_level -= 1
                    if current_paren_level == 0:
                        commas.append(i + highest_priority_pos + 2)
                        break
            else:
                # If no break, we didn't find a closing parenthesis
                self.line_error_print(self.current_line, "No closing parenthesis on for statement")
            if len(commas) != 4:
                self.line_error_print(self.current_line, "For loop expects 3 arguments (<init state>, <break condition>, <increment>)")

            top.add_child(self.create_tree(line[commas[0]+1:commas[1]]))
            top.add_child(self.create_tree(line[commas[1]+1:commas[2]]))
            top.add_child(self.create_tree(line[commas[2]+1:commas[3]]))

        else:
            self.line_error_print(self.current_line, "Parser did not recognize symbol " + str(symbol))
            quit()

        return top

    def create_clause_tree(self, line, type):
        for i, symbol in enumerate(line):
            if symbol[1] == "NAME":
                self.dbg_print("Clause tree top is " + str(symbol))
                top = ASTNode.ClauseNode((symbol[0], type))
                name_def_pos = i
                break
        for symbol in line[:name_def_pos]:
            top.children.append(self.create_tree([symbol]))
        offset = 1
        if line[name_def_pos + offset][1] == "OPEN_PAREN":
            paren_depth = 1
            while paren_depth != 0:
                offset += 1
                if line[name_def_pos + offset][1] == "OPEN_PAREN":
                    paren_depth += 1
                elif line[name_def_pos + offset][1] == "CLOSE_PAREN":
                    paren_depth -= 1
            args = self.make_args(line[name_def_pos+1:name_def_pos+offset+1])
            top.children += [self.create_tree(arg) for arg in args]
        top.clause_trees = self.parse_symbols(line[name_def_pos+offset+1:])
        return top
