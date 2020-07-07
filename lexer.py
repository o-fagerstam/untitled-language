import re, sys

class Lexer:
    def __init__(self, debug = False):
        self.debug = debug

    def dbg_print(self, msg):
        if self.debug:
            print(msg)

    def lex(self, code):
        symbols = {";":"END", "(":"OPEN_PAREN", ")":"CLOSE_PAREN", "+":"INFIX", "=":"ASS", "-":"INFIX", "==":"INFIX",\
        "<":"INFIX", ">":"INFIX", ",":"COMMA", "for":"FOR", "{":"OPEN_CLAUSE", "}":"CLOSE_CLAUSE"}
        pattern = "[\w][\w\d]*|[0-9]+|[+-=,;]{1,2}|\(|\)|\"[^\"]*\"|\'[^\']*\'|{|}"
        res = []
        for match in re.finditer(pattern, code):
            token = match.group(0)
            if token in symbols.keys():
                self.dbg_print("Known token " + token)
                if symbols[token] == "STR":
                    res.append((token[1:-1], "STR"))
                else:
                    res.append((token, symbols[token]))
            elif re.match('\d+',token):
                self.dbg_print("Found digits: " + token)
                res.append((token, "NUM"))
            elif re.match('[\w][\w\d]*', token):
                if token == "for":
                    self.dbg_print("Found control token: " + token)
                    res.append(("for", "FOR"))
                elif token in ("int",):
                    self.dbg_print("Found modifier: " + token)
                    res.append((token, "MOD"))
                else:
                    self.dbg_print("Found new name: " + token)
                    symbols[token] = "NAME"
                    res.append((token, "NAME"))
            elif re.match('\"[^\"]*\"|\'[^\']*\'', token):
                self.dbg_print("Found string: " + token)
                symbols[token] = "STR"
                res.append((token[1:-1], "STR"))
            else:
                print("Warning: Unknown token " + token)
                sys.exit(-1)
        return res
