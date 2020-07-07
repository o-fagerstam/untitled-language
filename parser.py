import lexer, ASTNode

PRIORITIES = {"ASS":0, "INFIX":1, "NAME":2, "FOR":2, "MOD":1000, "NUM":1000,\
"STR":1000, "COMMA":1001, "OPEN_CLAUSE":1001, "CLOSE_CLAUSE":1001 }


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
        return self.parse(code)

    def parse(self, code):
        def add_newline(line, trees):
            newtree = self.create_tree(line)
            trees.append(newtree)
            line.clear()
            self.current_line += 1
        def add_sameline(line, trees):
            newtree = self.create_tree(line)
            trees.append(newtree)
            line.clear()

        l = lexer.Lexer(debug = self.DEBUG)
        symbols = l.lex(code)
        self.dbg_print("symbols: " + str(symbols))
        trees = []
        line = []
        self.current_line = 1
        for symbol in symbols:
            if symbol[1] == "END":
                add_newline(line, trees)
            elif symbol[1] == "OPEN_CLAUSE":
                print("GOT HERE")
                add_sameline(line, trees)
                line.append(symbol)
                add_newline(line, trees)
            elif symbol[1] == "CLOSE_CLAUSE":
                line.append(symbol)
                add_newline(line, trees)
            else:
                line.append(symbol)

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

        # Recursively build tree
        self.dbg_print("create_tree(): Highest priority is " + str(line[highest_priority_pos]) + " pos " + str(highest_priority_pos))
        top = ASTNode.Node(line[highest_priority_pos])
        if top.id[1] == "NUM":
            pass
        elif top.id[1] == "NAME":
            if highest_priority_pos+1 <= len(line)-1 and line[highest_priority_pos+1]:
                # If there is an opening parenthesis after, this is a function.
                top.id = (top.id[0], "FUNC")
                # First we find the end of the function parenthesis
                open_paren_level = paren_level
                current_paren_level = open_paren_level
                self.dbg_print("Paren line is: " + str(line[highest_priority_pos+1:]))
                for i, symbol in enumerate(line[highest_priority_pos+1:]):
                    if symbol[1] == "OPEN_PAREN":
                        current_paren_level += 1
                    elif symbol[1] == "CLOSE_PAREN":
                        current_paren_level -= 1
                    if current_paren_level == open_paren_level:
                        func_start_pos = highest_priority_pos+2
                        func_end_pos = highest_priority_pos+i+1

                # Then we make a list of arguments
                args = []
                current_arg = []
                arg_start = 0
                self.dbg_print("create_tree(): Finding args in " + str(line[func_start_pos:func_end_pos]))
                for i, symbol in enumerate(line[func_start_pos:func_end_pos]):
                    if symbol[1] == "COMMA":
                        args.append(current_arg)
                        current_arg = []
                    else:
                        current_arg.append(symbol)
                args.append(current_arg)
                # Then add the arguments as children
                for arg in args:
                    top.add_child(self.create_tree(arg))

            else:
                # Else, it is a variable
                # Maybe there are modifiers before
                modifiers = []
                if highest_priority_pos != 0:
                    for i in range(highest_priority_pos-1, -1, -1):
                        if line[i][1] == "MOD":
                            modifiers.append(line[i])
                        else:
                            break
                    for i in range(len(modifiers)-1, -1, -1):
                        top.add_child(self.create_tree([modifiers[i]]))

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
