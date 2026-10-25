import argparse

class Compiler():
    def __init__(self, src):
        self.source_file = src

    def get_full_source(self):
        with open(self.source_file, "r") as src:
            return [line for line in src]

    def Compile(self, optim):
        lex = Lexer(self.source_file)
        if not lex.lineLen:
            return ".intel_syntax noprefix\n.global _start\n_start:\nmov rax, 60\nxor rdi, rdi\nsyscall\n"
        lex = lex.Tokenize()
        #print(f"///{lex}///")
        parser = Parser(lex).Parse()
        #print(f"///{parser}///")
        semantic = SemanticAnalyzer(parser).Analyze()
        #print(f"///{semantic}///")
        generator = CodeGenerator(semantic).Generate() + ["push 0\ncall exit\n"]
        return Optimizer(generator).Optimize() if optim else generator


class Lexer():
    def __init__(self, src, isFile=True):
        self.source_file = src
        self.isFile = isFile
        self.gen = self.__iter__()
        self.eol = False
        self.next_line()
        if not self.line:
            return
        self.lineLen = len(self.line)
        self.tokens = []
        self.x = 0
        self.y = 0

        self.comparators = {
            "=": [TokenCategory.SETTER, TokenType.EQUALS[1]],
            "==": [TokenCategory.OPERATOR, TokenType.EQUALS_EQUALS[1]],
            "!=": [TokenCategory.OPERATOR, TokenType.NOT_EQUALS[1]],
            "!": [TokenCategory.OPERATOR, TokenType.NOT_EQUALS[1]],
            "<": [TokenCategory.OPERATOR, TokenType.LESS_THAN[1]],
            ">": [TokenCategory.OPERATOR, TokenType.GREATER_THAN[1]],
            "<=": [TokenCategory.OPERATOR, TokenType.LESS_EQUALS[1]],
            ">=": [TokenCategory.OPERATOR, TokenType.GREATER_EQUALS[1]],
            "=<": [TokenCategory.OPERATOR, TokenType.LESS_EQUALS[1]],
            "=>": [TokenCategory.OPERATOR, TokenType.GREATER_EQUALS[1]],
            "->": [TokenCategory.OPERATOR, TokenType.GREATER_THAN[1]],
            "-": None
        }
        self.operations = {
            "=": [TokenCategory.SETTER, TokenType.EQUALS[1]],
            "+": [TokenCategory.OPERATOR, TokenType.PLUS[1]],
            "-": [TokenCategory.OPERATOR, TokenType.MINUS[1]],
            "%": [TokenCategory.OPERATOR, TokenType.MODULOS[1]],
            "*": [TokenCategory.OPERATOR, TokenType.SNOWFLAKE[1]],
            "/": [TokenCategory.OPERATOR, TokenType.DIVISION[1]],
            "//": [TokenCategory.OPERATOR, TokenType.INT_DIV[1]],
            "^": [TokenCategory.OPERATOR, TokenType.EXPONENT[1]],
            "(": [TokenCategory.OPERATOR, TokenType.P_OPEN[1]],
            ")": [TokenCategory.OPERATOR, TokenType.P_CLOSE[1]],
            "[": [TokenCategory.OPERATOR, TokenType.B_OPEN[1]],
            "]": [TokenCategory.OPERATOR, TokenType.B_CLOSE[1]],
            ":": [TokenCategory.OPERATOR, TokenType.COLON[1]]
        }

    # iterates over the whole file
    def __iter__(self):
        if self.isFile:
            with open(self.source_file, "r") as src:
                for line in src:
                    yield line.strip()
        else:
            yield self.source_file

    # easy access to next line
    def next_line(self):
        while True:
            self.line = next(self.gen, None)
            if self.line is None:
                break
            if self.line != "":
                break
        self.lineLen = len(self.line if self.line else "")
    

    # returns current char of line
    def glance(self, plus=0):
        return self.line[self.x+plus] if self.line else ""


    def advance(self):
        new_line = False
        if self.x + 1 >= self.lineLen:
            new_line = True
            self.eol = True
            self.x = 0
            self.y += 1
            self.next_line()
        else:
            self.x += 1
        return new_line

    # advances until no more whitespace
    def skip_whitespace(self):
        while self.glance() == " ":
            self.advance()
        return

    def read_number(self):
        built = ""
        glanced = self.glance()
        isDigit = glanced.isdigit()
        while isDigit or glanced == " ":  # while current char is a number, keep reading
            if glanced == " ":
                self.skip_whitespace()
                #glanced = self.glance()
            if isDigit:
                built += glanced
                nl = self.advance()

            if not self.line or nl:   # if no more line left then break
                break
        
            glanced = self.glance()
            isDigit = glanced.isdigit()
        if glanced == ".":
            return self.read_generic(TokenType.FLOAT, f"_START_{built}", r"$%isfloat")
        return Token(TokenType.INT[0], TokenType.INT[1], int(built))

    def read_generic(self, token_return_type, *args):
        def get_applicable():               # loops through all input functions as an or, if any are true then continue
            for func in list(args):
                if func[0:7] == "_START_":
                    continue
                call = None
                test = glanced
                if func[0] == "$":                      # if $ then test against built + glanced (whole string)
                    test = built + glanced
                    if func[1] == "%":                  # if % then find method in self and pass test into it
                        call = getattr(self, func[2:])
                    else:
                        call = getattr(test, func[1:], None)
                elif func[0] == "%":                    # if just % then find method in self and pass test into it
                    call = getattr(self, func[1:])
                else:
                    call = getattr(test, func, None)
                if callable(call):                      # if a function then return results
                    try:
                        x = call()
                        return x
                    except:
                        x = call(test)
                        return x
                else:                                   # if not a function then return if test == func
                    if func[0] == "$":
                        return test == func[1:]
                    else:
                        return test == func
            return False
        
        built = ""
        if list(args) and list(args)[0][0:7] == "_START_":
            built = list(args)[0][7:]
        glanced = self.glance()
        isApplicable = get_applicable()
        while isApplicable:
            built += glanced
            nl = self.advance()

            if not self.line or nl:     # if no more lines then break
                break

            glanced = self.glance()
            isApplicable = get_applicable()
        upper = built.upper()
        isInTable = False
        if upper in TokenType.parse_for or built in TokenType.parse_for:
            isInTable = True
            if upper in TokenType.parse_for:
                upper = TokenType.parse_for[upper]
            else:
                upper = TokenType.parse_for[built]
        token_return_type = getattr(TokenType, upper) if isInTable else token_return_type
        if token_return_type == TokenType.IDENTIFIER:
            if not built in SemanticAnalyzer(ProgramNode([])).baked_functions:
                built = "_var_" + built
        #token_return_type = getattr(TokenType, token_return_type[1]) if token_return_type[1] in TokenType.parse_for else token_return_type
        return Token(token_return_type[0], token_return_type[1], built)

    # reads a sequence of special characters like "=" or "=="
    def read_special_sequence(self):
        built = ""
        glanced = self.glance()
        while (built + glanced) in self.comparators or (built + glanced) in self.operations:
            built += glanced
            nl = self.advance()
            if not self.line or nl:
                break
            glanced = self.glance()
        if built == "=<" or built == "=>":
            built = built[::-1]
        result = self.comparators.get(built) or self.operations.get(built)
        return Token(result[0], result[1], built)

    def read_string(self, isFormatted=False):
        if not isFormatted:
            built = ""
            glanced = self.glance()
            start = glanced
            self.advance()
            glanced = self.glance()
            y = self.y
            while glanced != start:
                if self.isEOF():
                    raise SyntaxError(f"Unfinished string at ({self.x}, {y})")
                built += glanced
                nl = self.advance()
                if nl:
                    built += "\n"
                glanced = self.glance()
            self.advance()
            return Token(TokenType.STRING[0], TokenType.STRING[1], built)
        else:
            built = ""
            start = self.glance()
            self.advance()
            glanced = self.glance()
            calls = []
            y = self.y
            while glanced != start:
                if self.isEOF():
                    raise SyntaxError(f"Unfinished string at ({self.x}, {y})")
                if glanced == "{" and not (self.glance(-1) and self.glance(-1) == "\\"):
                    self.advance()
                    inside = ""
                    count = 0
                    while self.glance() != "}" and not (self.glance(-1) and self.glance(-1) == "\\") or count > 0:
                        if self.isEOF():
                            raise SyntaxError(f"Unfinished string at ({self.x}, {y})")
                        if self.glance() == "{":
                            count += 1
                        elif self.glance() == "}":
                            count -= 1
                        inside += self.glance()
                        nl = self.advance()
                        if nl:
                            inside += "\n"
                    inside = Lexer(inside, False).Tokenize()
                    calls.append([
                        Token(TokenType.IDENTIFIER[0], TokenType.IDENTIFIER[1], "strcon"),
                        Token(TokenType.P_OPEN[0], TokenType.P_OPEN[1], "("),
                        Token(TokenType.STRING[0], TokenType.STRING[1], built),
                        Token(TokenType.COMMA[0], TokenType.COMMA[1], ",")
                    ] + inside + [
                        Token(TokenType.P_CLOSE[0], TokenType.P_CLOSE[1], ")")
                    ])
                    built = ""
                    glanced = ""
                built += glanced
                nl = self.advance()
                if nl:
                    built += "\n"
                glanced = self.glance()
            
            if built:
                calls.append([Token(TokenType.STRING[0], TokenType.STRING[1], built)])
            while len(calls) > 1:
                new = []
                for i in range(0, len(calls)-1, 2):
                    new.append([
                        Token(TokenType.IDENTIFIER[0], TokenType.IDENTIFIER[1], "strcon"),
                        Token(TokenType.P_OPEN[0], TokenType.P_OPEN[1], "(")
                    ] + calls[i] + [
                        Token(TokenType.COMMA[0], TokenType.COMMA[1], ",")
                    ] + calls[i+1] + [
                        Token(TokenType.P_CLOSE[0], TokenType.P_CLOSE[1], ")")
                    ])
                if i+2 == len(calls)-1:
                    first = new.pop()
                    new.append([
                        Token(TokenType.IDENTIFIER[0], TokenType.IDENTIFIER[1], "strcon"),
                        Token(TokenType.P_OPEN[0], TokenType.P_OPEN[1], "(")
                    ] + first + [
                        Token(TokenType.COMMA[0], TokenType.COMMA[1], ",")
                    ] + calls[i+2] + [
                        Token(TokenType.P_CLOSE[0], TokenType.P_CLOSE[1], ")")
                    ])
                calls = new
            if len(calls) == 1:
                calls = calls[0]
            else:
                calls = [Token(TokenType.STRING[0], TokenType.STRING[1], "")]
            self.tokens += calls
            self.advance()

    def isfloat(self, x):
        try:
            float(x)
            return True
        except:
            return False

    def isint(self, x):
        try:
            int(x)
            return True
        except:
            return False


    # if no line at all then return true
    def isEOF(self):
        return self.line is None

    def isEOL(self):
        if self.eol:
            self.eol = False
            return True
        return False


    # tokenize its source file
    def Tokenize(self):
        self.tokens = []
        while not self.isEOF():
            glanced = self.glance()
            if glanced == "~":
                nl = self.advance()
                while self.glance() != "~" and not nl:
                    nl = self.advance()
                if not nl:
                    self.advance()
                self.tokens.append(Token(TokenType.EOL[0], TokenType.EOL[1], "EOL"))
                continue

            if glanced == ",":
                token = Token(TokenType.COMMA[0], TokenType.COMMA[1], ",")
                self.advance()
            elif (glanced.upper() == "F" and (self.glance(1) == '"' or self.glance(1) == "'")) or (glanced == '"' or glanced == "'"):
                if glanced.upper() == "F":
                    self.advance()
                token = self.read_string(self.glance(-1).upper() == "F")
            elif glanced.isidentifier():
                token = self.read_generic(TokenType.IDENTIFIER, "$isidentifier")
                if token.isType(TokenType.ELSE):
                    self.tokens.append(token)
                    self.tokens.append(Token(TokenType.EOL[0], TokenType.EOL[1], "EOL", self.x, self.y))
                    #self.advance()
                    continue
            elif glanced.isdigit():
                token = self.read_number()
            elif glanced in self.comparators or glanced in self.operations:
                token = self.read_special_sequence()
            elif glanced.isspace():
                if self.line:
                    self.skip_whitespace()
                token = None
            elif glanced != ".":
                raise SyntaxError(f'Unknown symbol: "{glanced}"')
            if glanced == ".":
                raise SyntaxError('Out of place symbol: "."')
            
            if token:
                token.x = self.x
                token.y = self.y
                self.tokens.append(token)
            if self.isEOL() and not self.isEOF() and not self.tokens[-2].isType(TokenType.EOL):
                self.tokens.append(Token(TokenType.EOL[0], TokenType.EOL[1], "EOL", self.x, self.y))
        return self.tokens



class Token():
    def __init__(self, category, type, value=None, x=None, y=None):
        self.category = category
        self.type = type
        self.value = value
        self.x = x
        self.y = y

    def isChildOf(self, type: TokenType):
        parent = getattr(TokenType, self.type, None)
        if not parent or len(parent) <= 2:
            return False
        parent = parent[2]
        while parent[1] != type[1]:
            if len(parent) <= 2:
                return False
            parent = parent[2]
        return True

    def isType(self, type: TokenType):
        attr = getattr(TokenType, self.type, None)
        if attr:
            return attr[1] == type[1]
        return False

    def getAsNode(self):
        if self.isType(TokenType.INT):
            return INTNode
        if self.isType(TokenType.FLOAT):
            return FLOATNode
        if self.isType(TokenType.BOOL):
            return BOOLNode
        if self.isType(TokenType.STRING):
            return STRINGNode
        if self.isType(TokenType.ARRAY):
            return ARRAYNode
        if self.isType(TokenType.NONE):
            return NONENode

    def getAsStr(self):
        if self.isType(TokenType.INT) or self.isType(TokenType.FLOAT) or self.isType(TokenType.BOOL):
            return "native"
        elif self.isType(TokenType.NONE):
            return "none"
        elif self.isType(TokenType.ARRAY):
            return "objectarray"
        else:
            return "object"

    def __str__(self):
        return f"Token:[{self.category}, {self.type}, {self.value}] at ({self.x}, {self.y})\n"
    def __repr__(self):
        return self.__str__()

class TokenCategory():
    OBJECT = "OBJECT"
    OPERATOR = "OPERATOR"
    SETTER = "SETTER"
    STATEMENT = "STATEMENT"
    LABEL = "LABEL"

class TokenType():
    TYPE_OBJECT = [TokenCategory.OBJECT, "TYPE_OBJECT"]
    CONSTANT = [TokenCategory.OBJECT, "CONSTANT", TYPE_OBJECT]
    NUMBER = [TokenCategory.OBJECT, "NUMBER", CONSTANT]
    BOOL = [TokenCategory.OBJECT, "BOOL", CONSTANT]
    STRING = [TokenCategory.OBJECT, "STRING", CONSTANT]

    TRUE = [TokenCategory.OBJECT, "TRUE", BOOL]
    FALSE = [TokenCategory.OBJECT, "FALSE", BOOL]

    ARRAY = [TokenCategory.OBJECT, "ARRAY", TYPE_OBJECT]

    NONE = [TokenCategory.OBJECT, "NONE", CONSTANT]

    TYPE_OPERATOR = [TokenCategory.OPERATOR, "TYPE_OPERATOR"]
    SETTER = [TokenCategory.SETTER, "SETTER", TYPE_OPERATOR]
    REGULAR = [TokenCategory.OPERATOR, "REGULAR", TYPE_OPERATOR]
    COMPARATOR = [TokenCategory.OPERATOR, "COMPARATOR", TYPE_OPERATOR]

    # object kinda things
    INT = [TokenCategory.OBJECT, "INT", NUMBER]
    FLOAT = [TokenCategory.OBJECT, "FLOAT", NUMBER]

    TYPE_REFERENCE = [TokenCategory.OBJECT, "TYPE_REFERENCE"]
    IDENTIFIER = [TokenCategory.OBJECT, "IDENTIFIER", TYPE_REFERENCE]

    # modifiers (not setters)
    SNOWFLAKE = [TokenCategory.OPERATOR, "SNOWFLAKE", REGULAR]
    DIVISION = [TokenCategory.OPERATOR, "DIVISION", REGULAR]
    MODULOS = [TokenCategory.OPERATOR, "MODULOS", REGULAR]
    INT_DIV = [TokenCategory.OPERATOR, "INT_DIV", REGULAR]
    MINUS = [TokenCategory.OPERATOR, "MINUS", REGULAR]
    PLUS = [TokenCategory.OPERATOR, "PLUS", REGULAR]

    EXPONENT = [TokenCategory.OPERATOR, "EXPONENT", REGULAR]

    P_OPEN = [TokenCategory.OPERATOR, "P_OPEN", REGULAR]
    P_CLOSE = [TokenCategory.OPERATOR, "P_CLOSE", REGULAR]
    B_OPEN = [TokenCategory.OPERATOR, "B_OPEN", REGULAR]
    B_CLOSE = [TokenCategory.OPERATOR, "B_CLOSE", REGULAR]
    COLON = [TokenCategory.OPERATOR, "COLON", REGULAR]

    # comparators
    NOT_EQUALS = [TokenCategory.OPERATOR, "NOT_EQUALS", COMPARATOR]
    EQUALS_EQUALS = [TokenCategory.OPERATOR, "EQUALS_EQUALS", COMPARATOR]
    GREATER_EQUALS = [TokenCategory.OPERATOR, "GREATER_EQUALS", COMPARATOR]
    LESS_EQUALS = [TokenCategory.OPERATOR, "LESS_EQUALS", COMPARATOR]
    LESS_THAN = [TokenCategory.OPERATOR, "LESS_THAN", COMPARATOR]
    GREATER_THAN = [TokenCategory.OPERATOR, "GREATER_THAN", COMPARATOR]

    # setters
    EQUALS = [TokenCategory.SETTER, "EQUALS", SETTER]

    # label/error
    TYPE_LABEL = [TokenCategory.LABEL, "TYPE_LABEL"]
    EOL = [TokenCategory.LABEL, "EOL", TYPE_LABEL]
    COMMA = [TokenCategory.LABEL, "COMMA", TYPE_LABEL]

    # things to parse specifically for
    TYPE_RESERVED = [TokenCategory.STATEMENT, "TYPE_RESERVED"]
    STATEMENT = [TokenCategory.STATEMENT, "STATEMENT", TYPE_RESERVED]
    COND_MOD = [TokenCategory.STATEMENT, "COND_MOD", TYPE_RESERVED]

    IF = [TokenCategory.STATEMENT, "IF", STATEMENT]
    AND = [TokenCategory.STATEMENT, "AND", COND_MOD]
    OR = [TokenCategory.STATEMENT, "OR", COND_MOD]
    ELSE = [TokenCategory.STATEMENT, "ELSE", STATEMENT]
    END = [TokenCategory.STATEMENT, "END", STATEMENT]

    WHILE = [TokenCategory.STATEMENT, "WHILE", STATEMENT]
    CONTINUE = [TokenCategory.STATEMENT, "CONTINUE", STATEMENT]
    BREAK = [TokenCategory.STATEMENT, "BREAK", STATEMENT]

    FOR = [TokenCategory.STATEMENT, "FOR", STATEMENT]
    # EXEC = [TokenCategory.STATEMENT, "EXEC", STATEMENT]
    # FIN = [TokenCategory.STATEMENT, "FIN", STATEMENT]

    DEF = [TokenCategory.STATEMENT, "DEF", STATEMENT]
    RETURN = [TokenCategory.STATEMENT, "RETURN", STATEMENT]

    AS = [TokenCategory.STATEMENT, "AS", STATEMENT]
    IN = [TokenCategory.STATEMENT, "IN", STATEMENT]

    NEW = [TokenCategory.STATEMENT, "NEW", STATEMENT]
    #GLOBAL = [TokenCategory.STATEMENT, "GLOBAL", STATEMENT]
    #OUTER = [TokenCategory.STATEMENT, "OUTER", STATEMENT]
    parse_for = {
        "def": "DEF", "RETURN": "RETURN", "new": "NEW", #"global": "GLOBAL", "outer": "OUTER",
        "int": "INT", "float": "FLOAT", "bool": "BOOL", "string": "STRING", "NONE": "NONE", "Str": "STRING",

        "if": "IF", "end": "END", "AND": "AND", "OR": "OR", "else": "ELSE",
        "while": "WHILE", "continue": "CONTINUE", "BREAK": "BREAK",
        "Array": "ARRAY", "as": "AS", "native": "INT", "Nat": "INT", "Obj": "TYPE_OBJECT", "object": "TYPE_OBJECT", "Arr": "ARRAY",
        "FOR": "FOR", "in": "IN",
        "TRUE": "TRUE", "FALSE": "FALSE"
    }


class Parser():
    def __init__(self, token_source: list[Token]):
        self.token_source = token_source
        self.token_source_len = len(token_source)
        self.token_index = 0
        self.arrays = []
        self.trees = []

    def token(self, in_advance=0):
        return self.token_source[self.token_index+in_advance] if self.token_index+in_advance < self.token_source_len else None

    def advance(self, how_many=1):
        self.token_index += how_many

    def parse_value(self, skip=False):
        identStr = self.token().isType(TokenType.IDENTIFIER) or self.token().isType(TokenType.STRING)
        #isFString = self.token().isType(TokenType.IDENTIFIER) and self.token().value == "F" or self.token().value == "f"
        #isFString = isFString and self.token(1) and self.token(1).isType(TokenType.STRING)
        #t = self.token()
        if self.token().isType(TokenType.INT):
            self.advance()
            return INTNode(self.token(-1).value)
        elif (not skip and identStr and self.token(1) and self.token(1).isType(TokenType.B_OPEN)) or self.token().isType(TokenType.ARRAY):
            return self.parse_bracket()
        elif self.token().isType(TokenType.STRING):
            self.advance()
            s = self.token(-1).value
            value = []
            if type(s) is list:
                self.advance()
            else:
                escapes = {
                    "\\0": "\0",
                    "\\a": "\a",
                    "\\b": "\b",
                    "\\t": "\t",
                    "\\n": "\n",
                    "\\v": "\v",
                    "\\f": "\f",
                    "\\r": "\r",
                    "\\e": "\x1b",
                    "\\{": "{",
                    "\\}": "}"
                }
                s: str = self.token(-1).value
                for esc, val in escapes.items():
                    s = s.replace(esc, val)

                value = []
                for char in s:
                    value.append(hex(ord(char))[2:])
                    if len(value[-1]) == 1:
                        value[-1] = "0" + value[-1]
            
            return STRINGNode(value)
        elif self.token().isType(TokenType.NONE):
            return NONENode()
        elif self.token().isType(TokenType.FLOAT):
            self.advance()
            return FLOATNode(self.token(-1).value)
        elif self.token().isType(TokenType.IDENTIFIER) and self.token(1) and self.token(1).isType(TokenType.P_OPEN):
            return self.parse_function_call()
        elif self.token().isType(TokenType.IDENTIFIER):
            self.advance()
            return IDENTIFIERNode(self.token(-1).value)#, extra)
        elif self.token().isChildOf(TokenType.BOOL):
            self.advance()
            return BOOLNode(self.token(-1).value)
        elif self.token().isType(TokenType.MINUS) or self.token().isType(TokenType.PLUS):
            operator = self.token()
            self.advance()
            return UnaryNode(self.parse_value(), operator.value)
        elif self.token().isType(TokenType.P_OPEN):
            self.advance()
            value = self.parse_comparison()
            self.advance()
            return value
        # elif self.token().isType(TokenType.B_OPEN):
        #     return BracketUse()
        raise SyntaxError(f"Invalid pattern, got: {self.token()}.")
    

    def parse_exponents(self):
        left = self.parse_value()

        while self.token() and self.token().isType(TokenType.EXPONENT):
            operator = self.token().value
            self.advance()

            right = self.parse_value()
            left = OperationNode(left, operator, right)
        return left

    def parse_multiplication(self):
        left = self.parse_exponents()

        while self.token() and (self.token().isType(TokenType.SNOWFLAKE) or self.token().isType(TokenType.DIVISION)
                                or self.token().isType(TokenType.INT_DIV)):
            operator = self.token().value
            self.advance()

            right = self.parse_exponents()
            left = OperationNode(left, operator, right)
        return left

    def parse_addition(self):
        left = self.parse_multiplication()

        while self.token() and (self.token().isType(TokenType.PLUS) or self.token().isType(TokenType.MINUS) or self.token().isType(TokenType.MODULOS)):
            operator = self.token().value
            self.advance()

            right = self.parse_multiplication()
            left = OperationNode(left, operator, right)
        return left

    def parse_comparison(self):
        left = self.parse_addition()

        while self.token() and self.token().isChildOf(TokenType.COMPARATOR):
            operator = self.token().value
            self.advance()

            right = self.parse_addition()
            left = OperationNode(left, operator, right)
        if self.token(1) and self.token().isChildOf(TokenType.SETTER) and self.token(1).isType(TokenType.IDENTIFIER):
            self.advance(2)
            return AssignmentNode(self.token(-1).value, left)
        return left

    def parse_assignment(self):
        identifier = self.token().value
        if self.token(-1) and self.token(-1).isType(TokenType.NEW): #or self.token(-1).isType(TokenType.GLOBAL) or self.token(-1).isType(TokenType.OUTER)):
            extra = self.token(-1).value
        else:
            extra = ""
        while not self.token(-1).isChildOf(TokenType.SETTER):
            self.advance()
        return AssignmentNode(identifier, self.parse_comparison(), extra)

    def parse_function_call(self):
        args = []
        name = self.token().value
        self.advance(2)
        while self.token() and not self.token().isType(TokenType.P_CLOSE):
            args.append(self.parse_statement()) #args.append(self.parse_comparison())
            if self.token() and self.token().isType(TokenType.COMMA):
                self.advance()
        self.advance()
        if self.token() and self.token().isChildOf(TokenType.SETTER) and self.token(1) and self.token(1).isType(TokenType.IDENTIFIER):
            self.advance(2)
            return AssignmentNode(self.token(-1).value, FunctionCall(name, args))
        return FunctionCall(name, args)

    def parse_function_assignment(self):
        args = {}
        self.advance()
        retType = self.token()
        self.advance()
        name = self.token().value
        self.advance(2)
        while self.token() and not self.token().isType(TokenType.P_CLOSE):
            args[self.token(1).value] = self.token()
            self.advance(2)
            while self.token().isType(TokenType.COMMA) or self.token(1).isType(TokenType.COMMA):
                self.advance()
            if self.token().isType(TokenType.P_CLOSE):
                break
        for var, typ in args.items():
            if typ.isType(TokenType.ARRAY):
                self.arrays.append(var)
            elif var in self.arrays:
                self.arrays.remove(var)
        self.advance()
        code = []
        while not self.token().isType(TokenType.RETURN):
            while self.token() and self.token().isType(TokenType.EOL):
                self.advance()
            if self.token().isType(TokenType.RETURN):
                break
            code.append(self.parse_statement())
        if not retType.isType(TokenType.NONE):
            self.advance()
            code.append(FunctionReturn(self.parse_comparison()))
        else:
            code.append(FunctionReturn(NONENode()))
        self.advance()
        return FunctionAssign(name, args, retType, code)

    def parse_if(self, nested=False):
        self.advance()
        left = self.parse_comparison()#statement
        while self.token().isChildOf(TokenType.COND_MOD):
            self.advance()
            left = CONDMODNode(left, self.token(-1), self.parse_comparison())
        code = [self.parse_statement()]
        while self.token().isType(TokenType.EOL):
            self.advance()
        while not self.token().isType(TokenType.END) and not self.token().isType(TokenType.ELSE):
            code.append(self.parse_statement())
            while self.token().isType(TokenType.EOL):
                self.advance()
        codeElse = []
        if self.token().isType(TokenType.ELSE):
            self.advance()
            while not self.token().isType(TokenType.END):
                codeElse.append(self.parse_statement(True))
                while self.token().isType(TokenType.EOL):
                    self.advance()
            if not nested:
                self.advance()
        elif not nested:
            self.advance()
        return IFNode(left, code, codeElse)

    def parse_while(self):
        self.advance()
        left = self.parse_comparison()
        while self.token().isChildOf(TokenType.COND_MOD):
            self.advance()
            left = OperationNode(left, self.token(-1), self.parse_comparison())
        code = []
        while not self.token().isType(TokenType.END):
            code.append(self.parse_statement())
            while self.token() and self.token().isType(TokenType.EOL):
                self.advance()
        while self.token().isType(TokenType.EOL):
            self.advance()
        self.advance()
        return WHILENode(left, code)

    def parse_for(self):
        self.advance()
        var = self.parse_value()
        self.advance()
        item_parse = self.parse_statement()
        if self.token(1) and self.token().isType(TokenType.AS):
            self.advance()
            asType = self.token().getAsStr()
        else:
            asType = None
        self.advance()
        code = []
        while self.token() and not self.token().isType(TokenType.END):
            code.append(self.parse_statement())
            while self.token() and self.token().isType(TokenType.EOL):
                self.advance()
        while self.token() and self.token().isType(TokenType.EOL):
            self.advance()
        self.advance()
        return FORNode(var.value, item_parse, code, asType)

    def parse_bracket(self, ident=None, parent=None):
        isArray = self.token().isType(TokenType.ARRAY)
        if not isArray:
            if not ident:
                item = self.parse_value(True)
                self.advance()
            else:
                item = ident
            value = []
            isSlice = False
            i = 0
            firstItem = None
            while not self.token(-1).isType(TokenType.B_CLOSE) and not self.token().isType(TokenType.B_CLOSE):
                if self.token().isType(TokenType.COLON):
                    value.append(":")
                    self.advance()
                    i += 1
                    isSlice = True
                    continue
                value.append(self.parse_statement())
                if not firstItem:
                    firstItem = value[-1]
                if str(value[-1]).lstrip("-").isdigit():
                    firstItem = value[-1]
                    value[-1] = str(value[-1])
                if self.token().isType(TokenType.COLON):
                    isSlice = True
                self.advance()
                i += 1
            if i > 3:
                raise SyntaxError("Too many \":\" present.")
            if self.token() and self.token().isType(TokenType.B_CLOSE):
                self.advance()
            extract = ""
            if not isSlice and self.token().isType(TokenType.AS):
                self.advance()
                value[-1] = firstItem
                extract = self.token().getAsStr()
                self.advance()
            elif not isSlice and self.token().isType(TokenType.EQUALS):
                self.advance()
                ret = BracketUse(item if not parent else parent, value, isSlice, "", self.parse_statement())
                return ret
            if self.token() and self.token().isType(TokenType.B_OPEN):
                self.advance()
                ret = BracketUse(item if not parent else parent, value, isSlice, "objectarray")
                ret: BracketUse = self.parse_bracket(item, ret)
                return ret
            return BracketUse(item if not parent else parent, value, isSlice, extract)
        else:
            self.advance()
            length = INTNode(10)
            contents = []
            if self.token().isType(TokenType.GREATER_THAN):
                self.advance(2)
                while not self.token().isType(TokenType.B_CLOSE):
                    while self.token().isType(TokenType.EOL):
                        self.advance()
                    if self.token().isType(TokenType.B_CLOSE):
                        break
                    if self.token().isType(TokenType.COMMA):
                        self.advance()
                    contents.append(self.parse_statement())
                    if self.token() and self.token().isType(TokenType.COMMA):
                        self.advance()
                length = INTNode(len(contents))
            else:
                self.advance()
                if not self.token().isType(TokenType.B_CLOSE):
                    length = self.parse_comparison()
                else:
                    length = INTNode(10)
            self.advance()
            return ARRAYNode(length, contents)

    def parse_statement(self, nested=False):
        if self.token().isType(TokenType.NEW): #or self.token().isType(TokenType.GLOBAL) or self.token().isType(TokenType.OUTER):
            self.advance()
        if self.token().isType(TokenType.IF):
            return self.parse_if(nested)
        if self.token().isType(TokenType.WHILE):
            return self.parse_while()
        if self.token().isType(TokenType.FOR):
            return self.parse_for()
        if self.token().isType(TokenType.BREAK) or self.token().isType(TokenType.CONTINUE):
            self.advance()
            return LOOPMODNode(self.token(-1).value)
        setter = self.token(1) and self.token(1).isChildOf(TokenType.SETTER)
        if self.token().isType(TokenType.IDENTIFIER) and setter:
            return self.parse_assignment()
        if self.token() and self.token().isType(TokenType.DEF) and self.token(1).isChildOf(TokenType.TYPE_OBJECT):
            return self.parse_function_assignment()
        if self.token().isType(TokenType.IDENTIFIER) and self.token(1) and self.token(1).isType(TokenType.B_OPEN):
            return self.parse_bracket()
        elif self.token().isType(TokenType.B_OPEN) and self.token(-1) and self.token(-1).isType(TokenType.B_CLOSE):
            return self.parse_bracket()
        endParen = self.token(1) and self.token(1).isType(TokenType.P_OPEN)
        if self.token().isType(TokenType.IDENTIFIER) and endParen:
            return self.parse_function_call()
        isVal = self.token().isChildOf(TokenType.NUMBER) or self.token().isType(TokenType.IDENTIFIER) or self.token().isChildOf(TokenType.BOOL)
        isStart = self.token().isChildOf(TokenType.REGULAR) or self.token().isType(TokenType.P_OPEN) or self.token().isType(TokenType.STRING)
        if isVal or isStart or self.token().isChildOf(TokenType.B_OPEN) or self.token().isType(TokenType.ARRAY):
            return self.parse_comparison()
        if self.token().isType(TokenType.PLUS) or self.token().isType(TokenType.MINUS):
            return self.parse_comparison()
        if self.token().isType(TokenType.EOL):
            while self.token().isType(TokenType.EOL):
                self.advance()
            return self.parse_statement(nested)
        if self.token().isType(TokenType.RETURN):
            self.advance()
            return FunctionReturn(self.parse_statement())
        raise SyntaxError(f"Current statement doesnt fit any pattern, {self.token()}.")

    def Parse(self, first=True):
        trees = []
        while self.token():
            while self.token() and self.token().isType(TokenType.EOL): #or self.token() and self.token().isType(TokenType.END):
                self.advance()
            if not self.token():
                break
            if self.token().isType(TokenType.RETURN):
                self.advance()
                trees.append(FunctionReturn(self.parse_comparison()))
                break
            trees.append(self.parse_statement())
            print(trees[-1])
        if first:
            return ProgramNode(trees)
        return trees

# class that holds all binary trees of the program
class ProgramNode():
    def __init__(self, nodes):
        self.branches = nodes
    def __str__(self):
        return "\n".join(str(branch) for branch in self.branches)
    def __repr__(self):
        return self.__str__()

# class that holds if statements
class IFNode():
    def __init__(self, conditions, code, codeelse):
        self.conditions = conditions
        self.code = code
        self.codeelse = codeelse
    def __str__(self):
        return f"if {self.conditions} then\n    {self.code}\n, else\n    {self.codeelse}\nend"
    def __repr__(self):
        return self.__str__()

class WHILENode():
    def __init__(self, conditions, code):
        self.conditions = conditions
        self.code = code
    def __str__(self):
        return f"while {self.conditions} do\n    {self.code}\nend"
    def __repr__(self):
        return self.__str__()

class FORNode():
    def __init__(self, var, parse_item, code, asType=None):
        self.var = var
        self.parse_item = parse_item
        self.code = code
        self.asType = asType
    def __str__(self):
        return f"for {self.var} in {self.parse_item} do\n    {self.code}\nend"
    def __repr__(self):
        return self.__str__()

class LOOPMODNode():
    def __init__(self, mod):
        self.mod = mod
    def __str__(self):
        return self.mod
    def __repr__(self):
        return self.__str__()

# node class telling the tree that its assigning a variable a value
class AssignmentNode():
    def __init__(self, identifier, value, extra=""):
        self.identifier = identifier
        self.value = value
        self.extra = extra
    def __str__(self):
        return f"|Assign {self.identifier}, {self.value}|"
    def __repr__(self):
        return self.__str__()

# node that assigns functions to variables
class FunctionAssign():
    def __init__(self, name, args, retType: Token, code):
        self.retType = retType
        self.name = name
        self.args = args
        self.code = code
    def __str__(self):
        return f"{self.retType}{self.name}({self.args})|{self.code}|"
    def __repr__(self):
        return self.__str__()

# node that represents a return statement
class FunctionReturn():
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return f"return {self.value}"
    def __repr__(self):
        return self.__str__()

class CONDMODNode():
    def __init__(self, left, mod: str, right):
        self.mod = mod
        self.left = left
        self.right = right
    def __str__(self):
        return f"{self.left} {self.mod} {self.right}"
    def __repr__(self):
        return self.__str__()

# supports - and +, - negates x, + makes abs(x)
class UnaryNode():
    def __init__(self, value, operation):
        self.value = value
        self.operation = operation
    def __str__(self):
        return f"{self.operation}{self.value}"
    def __repr__(self):
        return self.__str__()

# node that represents a function call
class FunctionCall():
    def __init__(self, name, args):
        self.name = name
        self.args = args
        self.retType = None
    def __str__(self):
        return f"{self.name}({self.args})"
    def __repr__(self):
        return self.__str__()

class BracketUse():
    def __init__(self, item, args, isSlice=False, extract="", assign=False):
        self.assign = assign
        self.extract = extract
        self.item = item
        self.args = args
        self.isSlice = isSlice
    def __str__(self):
        return f"{self.item}{self.args} as {self.extract}"
    def __repr__(self):
        return self.__str__()

# tells the tree what operation is happening between left and right node and in what order
class OperationNode():
    def __init__(self, left, operation, right):
        self.left = left
        self.right = right
        self.operation = operation
    def __str__(self):
        return f"({self.left} {self.operation} {self.right})"
    def __repr__(self):
        return self.__str__()


class EndNode():
    def __init__(self):
        self.parent = None
        self.value = None
    def isChildOf(self, type):
        return self.parent.isChildOf(type)
    def isType(self, type):
        return self.parent.isType(type)

class NONENode(EndNode):
    def __init__(self):
        self.parent = Token(TokenType.NONE[0], TokenType.NONE[1])
    def __str__(self):
        return "None"
    def __repr__(self):
        return self.__str__()

# node to tell the tree that it is of type INT
class INTNode(EndNode):
    __module__ = None
    def __init__(self, val):
        self.parent = Token(TokenType.INT[0], TokenType.INT[1], val)
        self.value = int(val)
    def __str__(self):
        return f"{self.value}"
    def __repr__(self):
        return self.__str__()

class ARRAYNode(EndNode):
    __module__ = None
    def __init__(self, size, contents=[]):
        self.parent = Token(TokenType.ARRAY[0], TokenType.ARRAY[1], "ARRAY")
        self.size = size
        self.contents = contents
    def __str__(self):
        return f"{self.size}: {self.contents}"
    def __repr__(self):
        return self.__str__()

# node to tell the tree that it is of type FLOAT
class FLOATNode(EndNode):
    __module__ = None
    def __init__(self, val):
        self.parent = Token(TokenType.FLOAT[0], TokenType.FLOAT[1], val)
        self.value = float(val)
    def __str__(self):
        return f"{self.value}"
    def __repr__(self):
        return self.__str__()

class STRINGNode(EndNode):
    __module__ = None
    def __init__(self, val):
        self.parent = Token(TokenType.STRING[0], TokenType.STRING[1], val)
        self.value = val
    def __str__(self):
        return f"({self.value})"
    def __repr__(self):
        return self.__str__()

class BOOLNode(EndNode):
    __module__ = None
    def __init__(self, val):
        self.parent = Token(TokenType.BOOL[0], TokenType.BOOL[1], val)
        self.value = str(val).lower() == "true"
    def __str__(self):
        return f"{self.value}"
    def __repr__(self):
        return self.__str__()

# node to tell the tree that it is of type IDENTIFIER
class IDENTIFIERNode(EndNode):
    __module__ = None
    def __init__(self, val):
        self.parent = Token(TokenType.IDENTIFIER[0], TokenType.IDENTIFIER[1], val)
        self.value = val
    def __str__(self):
        return f"{self.value}"
    def __repr__(self):
        return self.__str__()



class SemanticAnalyzer():
    def __init__(self, programNode: ProgramNode, selfvars={}):
        self.trees = programNode.branches
        self.vars = {} if not selfvars else selfvars
        self.baked_functions = {
            "print": None,
            "println": None,
            "printarr": None,
            "printarrln": None,
            "exit": None,
            "len": INTNode,
            "intput": INTNode,
            "strint": INTNode,
            "objlen": INTNode,
            "strcon": STRINGNode,
            "input": STRINGNode,
            "equals": BOOLNode,
            "range": None,
            "itype": INTNode,
            "refcount": INTNode
        }
        plusRules = {
            INTNode: {INTNode: INTNode, FLOATNode: FLOATNode, BOOLNode: INTNode, UnaryNode: INTNode, STRINGNode: INTNode},
            FLOATNode: {INTNode: FLOATNode, FLOATNode: FLOATNode, BOOLNode: FLOATNode, UnaryNode: FLOATNode, STRINGNode: FLOATNode},
            BOOLNode: {INTNode: INTNode, FLOATNode: FLOATNode, BOOLNode: INTNode, UnaryNode: INTNode, STRINGNode: INTNode},
            UnaryNode: {INTNode: INTNode, FLOATNode: FLOATNode, BOOLNode: INTNode, UnaryNode: UnaryNode},
            STRINGNode: {INTNode: INTNode, BOOLNode: INTNode}
        }
        boolRules = {
            INTNode: {INTNode: BOOLNode, FLOATNode: BOOLNode, BOOLNode: BOOLNode, UnaryNode: BOOLNode, STRINGNode: BOOLNode},
            FLOATNode: {INTNode: BOOLNode, FLOATNode: BOOLNode, BOOLNode: BOOLNode, UnaryNode: BOOLNode, STRINGNode: BOOLNode},
            BOOLNode: {INTNode: BOOLNode, FLOATNode: BOOLNode, BOOLNode: BOOLNode, UnaryNode: BOOLNode, STRINGNode: BOOLNode},
            UnaryNode: {INTNode: BOOLNode, FLOATNode: BOOLNode, BOOLNode: BOOLNode, UnaryNode: BOOLNode, STRINGNode: BOOLNode},
            STRINGNode: {INTNode: BOOLNode, FLOATNode: BOOLNode, BOOLNode: BOOLNode, UnaryNode: BOOLNode, STRINGNode: BOOLNode}
        }
        self.operation_outputs = {
            "+": plusRules,
            "-": plusRules,
            "%": plusRules,
            "*": plusRules,
            "^": plusRules,

            "/": {
                INTNode: {INTNode: FLOATNode, FLOATNode: FLOATNode, BOOLNode: FLOATNode, UnaryNode: FLOATNode},
                FLOATNode: {INTNode: FLOATNode, FLOATNode: FLOATNode, BOOLNode: FLOATNode, UnaryNode: FLOATNode},
                BOOLNode: {INTNode: FLOATNode, FLOATNode: FLOATNode, BOOLNode: FLOATNode, UnaryNode: FLOATNode},
                UnaryNode: {INTNode: FLOATNode, FLOATNode: FLOATNode, BOOLNode: FLOATNode, UnaryNode: FLOATNode}
            },
            "//": {
                INTNode: {INTNode: INTNode, FLOATNode: INTNode, BOOLNode: INTNode, UnaryNode: INTNode, STRINGNode: INTNode},
                FLOATNode: {INTNode: INTNode, FLOATNode: INTNode, BOOLNode: INTNode, UnaryNode: INTNode, STRINGNode: FLOATNode},
                BOOLNode: {INTNode: INTNode, FLOATNode: INTNode, BOOLNode: INTNode, UnaryNode: INTNode, STRINGNode: INTNode},
                UnaryNode: {INTNode: INTNode, FLOATNode: INTNode, BOOLNode: INTNode, UnaryNode: INTNode, STRINGNode: INTNode}

            },

            "==": boolRules,
            "!=": boolRules,
            "!": boolRules,
            "<=": boolRules,
            ">=": boolRules,
            "<": boolRules,
            ">": boolRules
        }

    def Analyze(self, returnVars=False):
        newTrees = []
        for tree in self.trees:
            analyzed = self.treeAnalyze(tree)
            if type(analyzed) is tuple:
                newTrees.append(analyzed[0])
                continue
            newTrees.append(analyzed)
        if not returnVars:
            return ProgramNode(newTrees)
        return ProgramNode(newTrees), self.vars


    def getNewType(self, node1, operator, node2, isType=False):
        if not isType:
            type1 = type(node1)
            type2 = type(node2)
        else:
            self.checkIsValid(node1, operator, node2)
            return self.operation_outputs[operator][node1][node2]
        if type1 is IDENTIFIERNode:
            type1 = self.getVar(node1.value)
        if type2 is IDENTIFIERNode:
            type2 = self.getVar(node2.value)
        return self.checkIsValid(type1, operator, type2)

    def getVar(self, key):
        var = self.vars.get(key, None)
        if var is None:
            raise KeyError(f'Undefined variable "{key}"')
        return var

    def computeValue(self, val1, operator, val2=None):
        if not val2 is None:
            string = f"{val1.value}{operator}{val2.value}"
        else:
            string = f"{operator}{val1.value}"
        if "+" in string and val2 is None:
            if str(val1.value).lower() == "true" or str(val1.value).lower() == "false":
                return True
            return abs(eval(str(val1.value)))
        if "-" in string and val2 is None:
            if str(val1.value).lower() == "true" or str(val1.value).lower() == "false":
                return eval(f"not {str(val1.value).title()}")
            return -(eval(str(val1.value)))
        string = string.replace("^", "**").replace("!", "!=").replace("!==", "!=")
        return self.getNewType(val1, operator, val2)(eval(string))

    def isNode(self, tree):
        if getattr(tree, "left", None):
            return False
        return True

    def isEndNode(self, tree):
        arg1 = self.isNode(tree) and not self.isUnary(tree) and not type(tree) is FunctionCall and not type(tree) is IFNode and not type(tree) is FORNode
        return arg1 and not type(tree) is FunctionAssign and not type(tree) is FunctionReturn and not type(tree) is BracketUse

    def isUnary(self, tree):
        return type(tree) is UnaryNode

    def isConst(self, tree):
        return self.isEndNode(tree) and tree.isChildOf(TokenType.CONSTANT)

    def checkIsValid(self, type1, operation, type2):
        try:
            output = self.operation_outputs[operation][type1][type2]
            return output
        except:
            raise TypeError(f"Cannot combine types: {type1}, {type2}")

    def treeAnalyze(self, tree):
        if type(tree) is FunctionAssign:
            self.vars[tree.name] = tree.retType.getAsNode()
            for var, varType in tree.args.items():
                self.vars[var] = varType.getAsNode()
            code = SemanticAnalyzer(ProgramNode(tree.code), self.vars).Analyze().branches
            return FunctionAssign(tree.name, tree.args, tree.retType, code), tree.retType.getAsNode()
        
        if type(tree) is FunctionCall:
            ret = self.vars.get(tree.name, self.baked_functions.get(tree.name))
            tree.retType = ret
            for i in range(len(tree.args)):
                analyze, analyzeType = self.treeAnalyze(tree.args[i])
                tree.args[i] = analyze
            return tree, ret
        
        if type(tree) is IFNode:
            code, newVars1 = SemanticAnalyzer(ProgramNode(tree.code), self.vars).Analyze(True)
            code = code.branches
            codeElse, newVars2 = SemanticAnalyzer(ProgramNode(tree.codeelse), self.vars).Analyze(True)
            codeElse = codeElse.branches
            for var, typ in newVars1.items():
                if var in newVars2:
                    if not newVars2[var] is typ:
                        raise TypeError(f"Uncertain variable mismatch types: {typ} and {newVars2[var]} for variable '{var[5:]}'")
            for var, typ in newVars2.items():
                if var in newVars1:
                    if not newVars1[var] is typ:
                        raise TypeError(f"Uncertain variable mismatch types: {typ} and {newVars2[var]} for variable '{var[5:]}'")
            newVars = newVars1 | newVars2
            self.vars |= newVars
            return IFNode(tree.conditions, code, codeElse)
        
        if type(tree) is WHILENode:
            code = SemanticAnalyzer(ProgramNode(tree.code), self.vars).Analyze().branches
            return WHILENode(tree.conditions, code)
        
        if type(tree) is FORNode:
            self.vars |= {str(tree.var): INTNode}
            code = SemanticAnalyzer(ProgramNode(tree.code), self.vars).Analyze().branches
            item, itemType = self.treeAnalyze(tree.parse_item)
            return FORNode(tree.var, item, code, tree.asType), itemType
        
        if type(tree) is LOOPMODNode:
            return tree, None
        
        if type(tree) is ARRAYNode:
            size, sizeType = self.treeAnalyze(tree.size)
            if not sizeType is INTNode:
                raise TypeError("Array size must be int")
            contents = []
            for v in tree.contents:
                cont, _ = self.treeAnalyze(v)
                contents.append(cont)
            return ARRAYNode(size, contents), ARRAYNode
        
        if type(tree) is BracketUse:
            analyze, analyzeType = self.treeAnalyze(tree.item)
            #if tree.isSlice:
            return BracketUse(analyze, tree.args, tree.isSlice, tree.extract, tree.assign), analyzeType
        
        if type(tree) is AssignmentNode:        # if assignment then analyze right instead and return it
            analyzed, varType = self.treeAnalyze(tree.value)
            self.vars[tree.identifier] = varType
            return AssignmentNode(tree.identifier, analyzed, tree.extra)
        
        elif self.isUnary(tree):                    # if unary then make new node of respective type, and negate it
            analyzed, varType = self.treeAnalyze(tree.value)
            if self.isConst(analyzed):
                computed = self.computeValue(analyzed, tree.operation)
                return type(analyzed)(computed), type(analyzed)
            return UnaryNode(analyzed, tree.operation), varType
        
        elif self.isEndNode(tree) and (tree.isChildOf(TokenType.CONSTANT) or tree.isType(TokenType.IDENTIFIER)):    # if int then climb back up the tree
            return tree, type(tree) if not tree.isType(TokenType.IDENTIFIER) else self.getVar(tree.value)
        
        elif type(tree) is FunctionReturn:
            analyze, analyzeType = self.treeAnalyze(tree.value)
            return FunctionReturn(analyze), analyzeType
        

        if type(tree) is OperationNode:
            left, leftType = self.treeAnalyze(tree.left)
            right, rightType = self.treeAnalyze(tree.right)
            self.checkIsValid(leftType, tree.operation, rightType)
            isOperation = (type(left) is OperationNode) or (type(right) is OperationNode) or (type(left) is UnaryNode) or (type(right) is UnaryNode)
            if self.isEndNode(left) and self.isEndNode(right) and not isOperation and left.isChildOf(TokenType.CONSTANT) and right.isChildOf(TokenType.CONSTANT):
                val = self.computeValue(left, tree.operation, right)
                return val, type(val)
            else:
                newType = self.getNewType(leftType, tree.operation, rightType, True)
                return OperationNode(left, tree.operation, right), newType


def getIfStartLabelGenerator():
    labelIndex = 0
    while True:
        yield f"IF_STRT_{labelIndex}"
        labelIndex += 1
getIfStartLabel = getIfStartLabelGenerator()

def getIfEndLabelGenerator():
    labelIndex = 0
    while True:
        yield f"IF_END_{labelIndex}"
        labelIndex += 1
getIfEndLabel = getIfEndLabelGenerator()

def getIfElseLabelGenerator():
    labelIndex = 0
    while True:
        yield f"IF_ELSE_{labelIndex}"
        labelIndex += 1
getIfElseLabel = getIfElseLabelGenerator()

def getWhileStartLabelGenerator():
    labelIndex = 0
    while True:
        yield f"WHILE_STRT_{labelIndex}"
        labelIndex += 1
getWhileStartLabel = getWhileStartLabelGenerator()

def getWhileEndLabelGenerator():
    labelIndex = 0
    while True:
        yield f"WHILE_END_{labelIndex}"
        labelIndex += 1
getWhileEndLabel = getWhileEndLabelGenerator()

def getWhileContinueLabelGenerator():
    labelIndex = 0
    while True:
        yield f"WHILE_CONT_{labelIndex}"
        labelIndex += 1
getWhileContinueLabel = getWhileContinueLabelGenerator()

def getWhileBreakLabelGenerator():
    labelIndex = 0
    while True:
        yield f"WHILE_BRK_{labelIndex}"
        labelIndex += 1
getWhileBreakLabel = getWhileBreakLabelGenerator()

def getRoDataLabelGenerator():
    labelIndex = 0
    while True:
        yield f"RO_DATA_{labelIndex}"
        labelIndex += 1
getRoDataLabel = getRoDataLabelGenerator()

varTypes = {}
restoreVars = [{}, []]

class CodeGenerator():
    def __init__(self, analyzedTokens: ProgramNode, isFunc=False, varAmt=0):
        self.tokens = analyzedTokens.branches
        self.varAmt = varAmt
        self.first = True
        self.isFunc = isFunc
        self.args = []

        self.conds = {
            "==": "jne",
            "!=": "je",
            "<": "jge",
            ">": "jle",
            "<=": "jg",
            ">=": "jl"
        }

        self.skipped_funcs = []

        self.rodata = []
        self.rodataMap = {}
        self.data = ["_pgstrt: .quad 0\n"]#_tmpvar: .quad 0\n"] # GLOBAL VARIABLES ONLY
        self.text = []                                                  # holds functions (only used by first created CodeGenerator instance)
        self.main = []                                                  # holds main, also where sub generators store their function data

        self.vars = {}                                                  # HOLDS ALL VARIABLE LOCATIONS AS STRINGS
        self.localVarTypes = {}
        #["rax", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r10", "r11"]

    def Generate(self, ret=True, prevVars={}, args: list=[], objVars: dict[str: Token]={}):
        self.args = args
        if prevVars or not ret:
            self.vars = prevVars
            #if "new" in args:
            #    self.vars |= {prevVars[args.index("new")+1]: args[args.index("new")+2]}
        else:
            self.text = [
                "_abs:\n",
                "  mov rax, [rbp+24]\n",
                "  cmp rax, 0\n",
                "  jge 0f\n",
                "  neg rax\n",
                "  0:\n",
                "  ret\n",
                "_exponent:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  mov rbp, rsp\n",
                "  mov rax, [rbp+24]\n",
                "  0:\n",
                "    cmp qword ptr [rbp+32], 1\n",
                "    jle 1f\n",
                "    imul rax, [rbp+24]\n",
                "    dec qword ptr [rbp+32]\n",
                "    jmp 0b\n",
                "  1:\n",
                "    pop rbp\n",
                "    pop rsp\n",
                "    ret\n",
                "intstr:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  mov rbp, rsp\n",
                "  sub rsp, 24\n",
                "  push 32\n",
                "  call heapalloc\n",
                "  add rsp, 8\n",
                "  mov rbx, rax\n",
                "  xor rdi, rdi\n",
                "  mov qword ptr [rbp-8], 10\n",
                "  mov qword ptr [rbp-16], 0\n",
                "  mov qword ptr [rbp-24], 1\n",
                "  mov rax, [rbp+24]\n",
                "  cmp rax, 0\n",
                "  jne 0f\n",
                "  mov rax, rbx\n",
                "  mov qword ptr [rax], 1\n",
                "  mov qword ptr [rax+8], 0x30\n",
                "  jmp 4f\n",
                "  0:\n",
                "  cmp rax, 0\n",
                "  jge 0f\n",
                "  neg rax\n",
                "  0:\n",
                "    cmp rax, 0\n",
                "    je 1f\n",
                "    mov r15, 10\n",
                "    xor rdx, rdx\n",
                "    div r15\n",
                "    mov r15, [rbp-8]\n",
                "    imul r15, [rbp-16]\n",
                "    mov qword ptr [rbp-16], r15\n",
                "    add qword ptr [rbp-16], rdx\n",
                "    cmp rdx, 0\n",
                "    jne 2f\n",
                "    cmp qword ptr [rbp-24], 0\n",
                "    je 3f\n",
                "    inc rdi\n",
                "    jmp 3f\n",
                "    2:\n",
                "    mov qword ptr [rbp-24], 0\n",
                "    3:\n",
                "    jmp 0b\n",
                "  1:\n",
                "  xor rsi, rsi\n",
                "  mov rax, [rbp-16]\n",
                "  lea r15, [rbx+8]\n",
                "  mov qword ptr [rbp-8], 10\n",
                "  cmp qword ptr [rbp+24], 0\n",
                "  jge 0f\n",
                "  mov byte ptr [rbx+8], 0x2d\n",
                "  mov rsi, 1\n",
                "  0:\n",
                "    cmp rax, 0\n",
                "    je 1f\n",
                "    xor rdx, rdx\n",
                "    div qword ptr [rbp-8]\n",
                "    add dl, 0x30\n",
                "    mov byte ptr [r15+rsi], dl\n",
                "    inc rsi\n",
                "    jmp 0b\n",
                "  1:\n",
                "  0:\n",
                "    cmp rdi, 0\n",
                "    je 1f\n",
                "    mov byte ptr [r15+rsi], 0x30\n",
                "    inc rsi\n",
                "    dec rdi\n",
                "    jmp 0b\n",
                "  1:\n",
                "  mov rax, rbx\n",
                "  mov qword ptr [rax], rsi\n",
                "  4:\n",
                "  add rsp, 24\n",
                "  pop rbp\n",
                "  pop rsp\n",
                "  ret\n",
                "print:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  mov rbp, rsp\n",
                "  mov r15, 0\n",
                "  0:\n",
                "    cmp r15, [rbp+24]\n",
                "    je 1f\n",
                "    mov rax, 1\n",
                "    mov rdi, 1\n",
                "    mov rsi, r15\n",
                "    imul rsi, 8\n",
                "    add rsi, rbp\n",
                "    add rsi, 32\n",
                "    mov rdx, [rsi]\n",
                "    lea rsi, [rdx+8]\n",
                "    mov rdx, [rdx]\n",
                "    syscall\n",
                "    inc r15\n",
                "    cmp r15, [rbp+24]\n",
                "    je 2f\n",
                "    mov rax, 1\n",
                "    mov rdi, 1\n",
                "    mov byte ptr [rbp-8], 0x20\n",
                "    lea rsi, [rbp-8]\n",
                "    mov rdx, 1\n",
                "    syscall\n",
                "    2:\n",
                "    dec r15\n",
                "    inc r15\n",
                "    jmp 0b\n",
                "  1:\n",
                "  pop rbp\n",
                "  pop rsp\n",
                "  ret\n",
                "println:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  mov rbp, rsp\n",
                "  sub rsp, 8\n",
                "  mov r15, 0\n",
                "  0:\n",
                "    cmp r15, [rbp+24]\n",
                "    je 1f\n",
                "    mov rax, 1\n",
                "    mov rdi, 1\n",
                "    mov rsi, r15\n",
                "    imul rsi, 8\n",
                "    add rsi, rbp\n",
                "    add rsi, 32\n",
                "    mov rdx, [rsi]\n",
                "    lea rsi, [rdx+8]\n",
                "    mov rdx, [rdx]\n",
                "    syscall\n",
                "    inc r15\n",
                "    cmp r15, [rbp+24]\n",
                "    je 2f\n",
                "    mov rax, 1\n",
                "    mov rdi, 1\n",
                "    mov byte ptr [rbp-8], 0x20\n",
                "    lea rsi, [rbp-8]\n",
                "    mov rdx, 1\n",
                "    syscall\n",
                "    2:\n",
                "    dec r15\n",
                "    \n",
                "    inc r15\n",
                "    jmp 0b\n",
                "  1:\n",
                "  mov rax, 1\n",
                "  mov rdi, 1\n",
                "  mov byte ptr [rbp-8], 0x0a\n",
                "  lea rsi, [rbp-8]\n",
                "  mov rdx, 1\n",
                "  syscall\n",
                "  add rsp, 8\n",
                "  pop rbp\n",
                "  pop rsp\n",
                "  ret\n",
                "exit:\n",
                "  add rsp, 8\n",
                "  pop rdi\n",
                "  mov rax, 60\n",
                "  syscall\n",
                "heapalloc:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  push rdx\n",
                "  push rcx\n",
                "  push r8\n",
                "  push r10\n",
                "  mov rbp, rsp\n",
                "  sub rsp, 32\n",
                "  mov rax, [rbp+56]\n",
                "  xor rdx, rdx\n",
                "  mov rcx, 16\n",
                "  div rcx\n",
                "  cmp rdx, 0\n",
                "  je 1f\n",
                "  sub rcx, rdx\n",
                "  add qword ptr [rbp+56], rcx\n",
                "  1:\n",
                "  mov rax, [rbp+56]\n",
                "  xor rdx, rdx\n",
                "  mov rcx, 8\n",
                "  div rcx\n",
                "  mov qword ptr [rbp-32], rax\n",
                "  cmp qword ptr [_pgstrt], 0\n",
                "  jne 0f\n",
                "  mov rax, 9\n",
                "  xor rdi, rdi\n",
                "  mov rsi, [rbp+56]\n",
                "  add rsi, 32\n",
                "  add rsi, 4095\n",
                "  and rsi, -4096\n",
                "  mov rdx, 3\n",
                "  mov r10, 0x22\n",
                "  mov r8, -1\n",
                "  xor r9, r9\n",
                "  syscall\n",
                "  cmp rax, 0\n",
                "  jle 1f\n",
                "  mov qword ptr [_pgstrt], rax\n",
                "  mov r14, rax\n",
                "  lea r13, [r14+8]\n",
                "  mov qword ptr [r14], 0\n",
                "  mov rdi, [rbp+56]\n",
                "  add rdi, 32\n",
                "  add rdi, 4095\n",
                "  and rdi, -4096\n",
                "  add rdi, r14\n",
                "  sub rdi, 8\n",
                "  mov qword ptr [rdi], -1\n",
                "  0:\n",
                "  mov r15, [rbp+56]\n",
                "  add r15, 16\n",
                "  mov rax, 1\n",
                "  mov rbx, 1\n",
                "  jmp 50f\n",
                "  10:\n",
                "  mov rdx, r13\n",
                "  16:\n",
                "    cmp qword ptr [rdx], -1\n",
                "    je 17f\n",
                "    add rdx, 8\n",
                "    jmp 16b\n",
                "  17:\n",
                "  sub rdx, r13\n",
                "  cmp rax, -1\n",
                "  je 15f\n",
                "  mov rax, r13\n",
                "  50:\n",
                "  jmp 0f\n",
                "  15:\n",
                "  cmp rdx, 32\n",
                "  jl 30f\n",
                "  mov rsi, [rbp+56]\n",
                "  add rsi, 16\n",
                "  cmp rsi, rdx\n",
                "  jg 30f\n",
                "  mov rax, r13\n",
                "  jmp 2f\n",
                "  30:\n",
                "  mov qword ptr [r13], -1\n",
                "  31:\n",
                "  mov rax, 9\n",
                "  xor rdi, rdi\n",
                "  mov rsi, [rbp+56]\n",
                "  add rsi, 32\n",
                "  add rsi, 4095\n",
                "  and rsi, -4096\n",
                "  mov rdx, 3\n",
                "  mov r10, 0x22\n",
                "  mov r8, -1\n",
                "  xor r9, r9\n",
                "  syscall\n",
                "  cmp rax, 0\n",
                "  jle 1f\n",
                "  mov qword ptr [r14], rax\n",
                "  mov r14, rax\n",
                "  lea r13, [r14+8]\n",
                "  mov rdi, [rbp+56]\n",
                "  add rdi, 32\n",
                "  add rdi, 4095\n",
                "  and rdi, -4096\n",
                "  add rdi, r14\n",
                "  sub rdi, 8\n",
                "  mov qword ptr [rdi], -1\n",
                "  mov rax, r13\n",
                "  jmp 2f\n",
                "  0:\n",
                "  mov qword ptr [rbp-8], r15\n",
                "  mov r15, [_pgstrt]\n",
                "  mov rax, -1\n",
                "  3:\n",
                "    mov qword ptr [rbp-16], r15\n",
                "    lea r15, [r15+8]\n",
                "    5:\n",
                "      cmp qword ptr [r15], 0\n",
                "      jle 6f\n",
                "      mov rdx, [rbp-8]\n",
                "      cmp rdx, [r15]\n",
                "      jg 8f\n",
                "      lea r15, [r15+8]\n",
                "      cmp qword ptr [r15], 0\n",
                "      jne 7f\n",
                "      mov rdx, [r15-8]\n",
                "      sub rdx, [rbp-8]\n",
                "      cmp rdx, 256\n",
                "      jg 7f\n",
                "      mov rbx, -1\n",
                "      lea rdi, [r15+8]\n",
                "      mov rcx, [rbp-32]\n",
                "      xor rax, rax\n",
                "      cld\n",
                "      rep stosq\n",
                "      lea rax, [r15-8]\n",
                "      jmp 2f\n",
                "      8:\n",
                "      lea r15, [r15+8]\n",
                "      7:\n",
                "      lea r15, [r15-8]\n",
                "      mov qword ptr [rbp-24], r15\n",
                "      mov r15, [r15]\n",
                "      add r15, [rbp-24]\n",
                "      jmp 5b\n",
                "    6:\n",
                "    mov r15, [rbp-16]\n",
                "    cmp qword ptr [r15], 0\n",
                "    je 10b\n",
                "    mov r15, [r15]\n",
                "    jmp 3b\n",
                "  4:\n",
                "  1:\n",
                "    mov rax, 0x6d654d6565724630\n",
                "    push rax\n",
                "    lea rsi, [rsp]\n",
                "    mov rdi, 1\n",
                "    mov rax, 0x00203A726F727245\n",
                "    push rax\n",
                "    mov rax, 1\n",
                "    lea rsi, [rsp]\n",
                "    mov rdx, 16\n",
                "    syscall\n",
                "    mov rax, 60\n",
                "    mov rdi, 126\n",
                "    syscall\n",
                "  2:\n",
                "  cmp rbx, -1\n",
                "  je 1f\n",
                "  mov rsi, [rbp+56]\n",
                "  add rsi, 16\n",
                "  mov qword ptr [rax], rsi\n",
                "  1:\n",
                "  lea rax, [rax+8]\n",
                "  mov qword ptr [rax], 1\n",
                "  lea rax, [rax+8]\n",
                "  cmp rbx, -1\n",
                "  je 1f\n",
                "  mov r13, rax\n",
                "  add r13, [rbp+56]\n",
                "  1:\n",
                "  add rsp, 32\n",
                "  pop r10\n",
                "  pop r8\n",
                "  pop rcx\n",
                "  pop rdx\n",
                "  pop rbp\n",
                "  pop rsp\n",
                "  ret\n",
                "strint:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  mov rbp, rsp\n",
                "  sub rsp, 8\n",
                "  mov qword ptr [rbp-8], 0\n",
                "  mov rax, [rbp+24]\n",
                "  mov rbx, 1\n",
                "  mov rdi, [rax]\n",
                "  lea rdi, [rax+rdi]\n",
                "  add rdi, 7\n",
                "  lea r15, [rax+7]\n",
                "  mov qword ptr [rbp+24], r15\n",
                "  0:\n",
                "    cmp qword ptr [rbp+24], rdi\n",
                "    je 1f\n",
                "    mov r15b, 0x2d\n",
                "    cmp byte ptr [rdi], r15b\n",
                "    jne 2f\n",
                "    lea r15, [rax+8]\n",
                "    cmp rdi, r15\n",
                "    jne 1f\n",
                "    mov r15, qword ptr [rbp-8]\n",
                "    imul r15, -1\n",
                "    mov qword ptr [rbp-8], r15\n",
                "    jmp 1f\n",
                "    2:\n",
                "    xor r15, r15\n",
                "    mov r15b, byte ptr [rdi]\n",
                "    sub r15, 0x30\n",
                "    imul r15, rbx\n",
                "    add qword ptr [rbp-8], r15\n",
                "    imul rbx, 10\n",
                "    dec rdi\n",
                "    jmp 0b\n",
                "  1:\n",
                "  mov rax, [rbp-8]\n",
                "  add rsp, 8\n",
                "  pop rbp\n",
                "  pop rsp\n",
                "  ret\n",
                "intput:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  mov rbp, rsp\n",
                "  sub rsp, 8\n",
                "  push 32\n",
                "  call heapalloc\n",
                "  add rsp, 8\n",
                "  mov qword ptr [rbp-8], rax\n",
                "  lea rsi, [rax+8]\n",
                "  xor rax, rax\n",
                "  xor rdi, rdi\n",
                "  mov rdx, [rbp+24]\n",
                "  syscall\n",
                "  mov r15, [rbp-8]\n",
                "  mov qword ptr [r15], rax\n",
                "  mov rax, r15\n",
                "  mov r15, [rax]\n",
                "  sub r15, 1\n",
                "  lea rdx, [rax+8]\n",
                "  add rdx, r15\n",
                "  cmp byte ptr [rdx], 0x0a\n",
                "  jne 1f\n",
                "  mov byte ptr [rdx], 0\n",
                "  sub qword ptr [rax], 1\n",
                "  mov qword ptr [rbp-8], rax\n",
                "  1:\n",
                "  call strint\n",
                "  add rsp, 8\n",
                "  pop rbp\n",
                "  pop rsp\n",
                "  ret\n",
                "strcon:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  mov rbp, rsp\n",
                "  sub rsp, 24\n",
                "  mov rdi, [rbp+24]\n",
                "  inc qword ptr [rdi-8]\n",
                "  mov rdi, [rdi]\n",
                "  mov rbx, [rbp+32]\n",
                "  inc qword ptr [rbx-8]\n",
                "  mov rbx, [rbx]\n",
                "  mov r15, rdi\n",
                "  add r15, rbx\n",
                "  mov qword ptr [rbp-24], r15\n",
                "  add r15, 8\n",
                "  push r15\n",
                "  call heapalloc\n",
                "  add rsp, 8\n",
                "  mov r15, [rbp-24]\n",
                "  mov qword ptr [rax], r15\n",
                "  mov rbx, [rbp+32]\n",
                "  mov r15, 0\n",
                "  mov rsi, [rbx]\n",
                "  lea rax, [rax+8]\n",
                "  0:\n",
                "    cmp r15, rsi\n",
                "    je 1f\n",
                "    mov qword ptr [rbp-8], rbx\n",
                "    mov rbx, [rbp+32]\n",
                "    lea rbx, [rbx+8]\n",
                "    mov bl, byte ptr [rbx+r15]\n",
                "    mov byte ptr [rax+r15], bl\n",
                "    mov rbx, [rbp-8]\n",
                "    inc r15\n",
                "    jmp 0b\n",
                "  1:\n",
                "  lea rax, [rax-8]\n",
                "  mov rbx, [rbp+24]\n",
                "  mov rsi, [rbx]\n",
                "  lea rax, [rax+r15]\n",
                "  lea rax, [rax+8]\n",
                "  mov qword ptr [rbp-16], r15\n",
                "  mov r15, 0\n",
                "  0:\n",
                "    cmp r15, rsi\n",
                "    je 1f\n",
                "    mov qword ptr [rbp-8], rbx\n",
                "    mov rbx, [rbp+24]\n",
                "    lea rbx, [rbx+8]\n",
                "    mov bl, byte ptr [rbx+r15]\n",
                "    mov byte ptr [rax+r15], bl\n",
                "    mov rbx, [rbp-8]\n",
                "    inc r15\n",
                "    jmp 0b\n",
                "  1:\n",
                "  mov r15, [rbp-16]\n",
                "  sub rax, r15\n",
                "  lea rax, [rax-8]\n",
                "  mov rdi, [rbp+24]\n",
                "  dec qword ptr [rdi-8]\n",
                "  mov rbx, [rbp+32]\n",
                "  dec qword ptr [rbx-8]\n",
                "  add rsp, 24\n",
                "  pop rbp\n",
                "  pop rsp\n",
                "  ret\n",
                "len:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  mov rbp, rsp\n",
                "  mov rax, [rbp+24]\n",
                "  mov rax, [rax]\n",
                "  pop rbp\n",
                "  pop rsp\n",
                "  ret\n",
                "objlen:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  push rdx\n",
                "  mov rbp, rsp\n",
                "  mov rax, [rbp+32]\n",
                "  mov rax, [rax-16]\n",
                "  sub rax, 16\n",
                "  mov r15, 8\n",
                "  xor rdx, rdx\n",
                "  div r15\n",
                "  pop rdx\n",
                "  pop rbp\n",
                "  pop rsp\n",
                "  ret\n",
                "equals:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  push rbx\n",
                "  mov rbp, rsp\n",
                "  mov rax, [rbp+32]\n",
                "  mov rbx, [rbp+40]\n",
                "  mov r15, [rax-16]\n",
                "  cmp r15, [rbx-16]\n",
                "  jne 0f\n",
                "  mov rdi, r15\n",
                "  sub rdi, 24\n",
                "  3:\n",
                "    cmp rdi, -1\n",
                "    jle 4f\n",
                "    mov r15, [rax+rdi]\n",
                "    cmp r15, [rbx+rdi]\n",
                "    jne 0f\n",
                "    sub rdi, 8\n",
                "    jmp 3b\n",
                "  4:\n",
                "  mov rax, 1\n",
                "  jmp 1f\n",
                "  0:\n",
                "  mov rax, -1\n",
                "  1:\n",
                "  pop rbx\n",
                "  pop rbp\n",
                "  pop rsp\n",
                "  ret\n",
                "input:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  push rdx\n",
                "  mov rbp, rsp\n",
                "  mov rax, [rbp+32]\n",
                "  add rax, 8\n",
                "  push rax\n",
                "  call heapalloc\n",
                "  add rsp, 8\n",
                "  lea rax, [rax+8]\n",
                "  mov r15, rax\n",
                "  xor rax, rax\n",
                "  xor rdi, rdi\n",
                "  mov rsi, r15\n",
                "  mov rdx, [rbp+32]\n",
                "  syscall\n",
                "  mov rdi, rax\n",
                "  mov rax, r15\n",
                "  lea rax, [rax-8]\n",
                "  mov qword ptr [rax], rdi\n",
                "  add rdi, 7\n",
                "  cmp byte ptr [rax+rdi], 0x0a\n",
                "  jne 1f\n",
                "  mov byte ptr [rax+rdi], 0\n",
                "  dec qword ptr [rax]\n",
                "  1:\n",
                "  push rax\n",
                "  push 0\n",
                "  push qword ptr [rax]\n",
                "  push 1\n",
                "  call _strsplit\n",
                "  add rsp, 24\n",
                "  dec qword ptr [rax-8]\n",
                "  pop rdx\n",
                "  dec qword ptr [rdx-8]\n",
                "  pop rdx\n",
                "  pop rbp\n",
                "  pop rsp\n",
                "  ret\n",
                "_strsplit:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  push rdx\n",
                "  mov rbp, rsp\n",
                "  sub rsp, 8\n",
                "  jmp 11f\n",
                "  10:\n",
                "    mov rax, 0x000000203a727245\n",
                "    push rax\n",
                "    mov rax, 1\n",
                "    mov rdi, 1\n",
                "    mov rsi, rsp\n",
                "    mov rdx, 5\n",
                "    syscall\n",
                "    mov rax, 0x6563696c53646142\n",
                "    push rax\n",
                "    mov rsi, rsp\n",
                "    mov rax, 1\n",
                "    mov rdx, 8\n",
                "    syscall\n",
                "    add rsp, 16\n",
                "    push 0\n",
                "    call exit\n",
                "  11:\n",
                "  mov rax, [rbp+40]\n",
                "  mov rbx, [rbp+56]\n",
                "  mov rbx, [rbx]\n",
                "  cmp rax, rbx\n",
                "  jle 0f\n",
                "  mov qword ptr [rbp+40], rbx\n",
                "  0:\n",
                "  cmp qword ptr [rbp+32], 0\n",
                "  jl 0f\n",
                "  cmp qword ptr [rbp+32], 0\n",
                "  je 10b\n",
                "  mov rax, [rbp+40]\n",
                "  sub rax, [rbp+48]\n",
                "  cmp rax, 0\n",
                "  jl 10b\n",
                "  mov rbx, [rbp+32]\n",
                "  sub rbx, 1\n",
                "  add rax, rbx\n",
                "  add rbx, 1\n",
                "  xor rdx, rdx\n",
                "  div rbx\n",
                "  jmp 1f\n",
                "  0:\n",
                "  mov rax, [rbp+48]\n",
                "  sub rax, [rbp+40]\n",
                "  cmp rax, 0\n",
                "  jl 10b\n",
                "  mov rbx, [rbp+32]\n",
                "  neg rbx\n",
                "  xor rdx, rdx\n",
                "  div rbx\n",
                "  cmp rdx, 0\n",
                "  je 1f\n",
                "  inc rax\n",
                "  1:\n",
                "  mov rsi, [rbp+56]\n",
                "  mov rsi, [rsi]\n",
                "  cmp qword ptr [rbp+48], rsi\n",
                "  jge 10b\n",
                "  cmp qword ptr [rbp+48], 0\n",
                "  jl 10b\n",
                "  cmp qword ptr [rbp+40], -1\n",
                "  jl 10b\n",
                "  add rax, 8\n",
                "  mov qword ptr [rbp-8], rax\n",
                "  push rax\n",
                "  call heapalloc\n",
                "  add rsp, 8\n",
                "  mov rbx, [rbp-8]\n",
                "  mov rsi, [rbp+56]\n",
                "  xor rdx, rdx\n",
                "  add rdx, [rbp+48]\n",
                "  mov rdi, 8\n",
                "  cmp qword ptr [rbp+32], 0\n",
                "  jg 4f\n",
                "  0:\n",
                "    cmp rdx, 0\n",
                "    jl 1f\n",
                "    cmp rdi, rbx\n",
                "    jge 1f\n",
                "    add rdx, 8\n",
                "    mov r15b, [rsi+rdx]\n",
                "    sub rdx, 8\n",
                "    mov byte ptr [rax+rdi], r15b\n",
                "    inc rdi\n",
                "    add rdx, [rbp+32]\n",
                "    jmp 0b\n",
                "  1:\n",
                "  jmp 1f\n",
                "  4:\n",
                "    cmp rdx, [rsi]\n",
                "    jge 1f\n",
                "    cmp rdi, rbx\n",
                "    jge 1f\n",
                "    add rdx, 8\n",
                "    mov r15b, [rsi+rdx]\n",
                "    sub rdx, 8\n",
                "    mov byte ptr [rax+rdi], r15b\n",
                "    inc rdi\n",
                "    add rdx, [rbp+32]\n",
                "    jmp 4b\n",
                "  1:\n",
                "  sub rdi, 8\n",
                "  mov qword ptr [rax], rdi\n",
                "  add rsp, 8\n",
                "  pop rdx\n",
                "  pop rbp\n",
                "  pop rsp\n",
                "  ret\n",
                "_decarrcheck:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  mov rbp, rsp\n",
                "  sub rsp, 8\n",
                "  mov rax, [rbp+24]\n",
                "  cmp qword ptr [rax-8], 1\n",
                "  jne 4f\n",
                "  lea r15, [rax]\n",
                "  mov rbx, [rax]\n",
                "  imul rbx, 16\n",
                "  sub rbx, 8\n",
                "  lea rbx, [r15+rbx]\n",
                "  0:\n",
                "    cmp rbx, r15\n",
                "    jle 4f\n",
                "    cmp qword ptr [rbx+8], 0\n",
                "    je 3f\n",
                "    cmp qword ptr [rbx+8], 2\n",
                "    jne 2f\n",
                "    push r15\n",
                "    push rbx\n",
                "    push rax\n",
                "    push qword ptr [rbx]\n",
                "    call _decarrcheck\n",
                "    add rsp, 8\n",
                "    pop rax\n",
                "    pop rbx\n",
                "    pop r15\n",
                "    jmp 3f\n",
                "    2:\n",
                "    mov qword ptr [rbp-8], r15\n",
                "    mov r15, [rbx]\n",
                "    dec qword ptr [r15-8]\n",
                "    mov r15, [rbp-8]\n",
                "    3:\n",
                "    lea rbx, [rbx-16]\n",
                "    jmp 0b\n",
                "  4:\n",
                "  dec qword ptr [rax-8]\n",
                "  add rsp, 8\n",
                "  pop rbp\n",
                "  pop rsp\n",
                "  ret\n",
                "_checkarrtype:\n",
                "  imul r15, 16\n",
                "  add r15, 8\n",
                "  lea rax, [rax+r15]\n",
                "  cmp qword ptr [rax+8], 0\n",
                "  je 1f\n",
                "  mov r15, [rax]\n",
                "  cmp qword ptr [rax+8], 1\n",
                "  jne 0f\n",
                "  dec qword ptr [r15-8]\n",
                "  jmp 1f\n",
                "  0:\n",
                "  cmp qword ptr [rax+8], 2\n",
                "  jne 1f\n",
                "  push rax\n",
                "  push qword ptr [rax]\n",
                "  call _decarrcheck\n",
                "  add rsp, 8\n",
                "  pop rax\n",
                "  1:\n",
                "  ret\n",
                "_arrsplit:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  push rdx\n",
                "  push rcx\n",
                "  push r8\n",
                "  mov rbp, rsp\n",
                "  sub rsp, 8\n",
                "  jmp 11f\n",
                "  10:\n",
                "    mov rax, 0x000000203a727245\n",
                "    push rax\n",
                "    mov rax, 1\n",
                "    mov rdi, 1\n",
                "    mov rsi, rsp\n",
                "    mov rdx, 5\n",
                "    syscall\n",
                "    mov rax, 0x6563696c53646142\n",
                "    push rax\n",
                "    mov rsi, rsp\n",
                "    mov rax, 1\n",
                "    mov rdx, 8\n",
                "    syscall\n",
                "    add rsp, 16\n",
                "    push 0\n",
                "    call exit\n",
                "  11:\n",
                "  mov rax, [rbp+56]\n",
                "  mov rbx, [rbp+72]\n",
                "  mov rbx, [rbx]\n",
                "  cmp rax, rbx\n",
                "  jle 0f\n",
                "  mov qword ptr [rbp+56], rbx\n",
                "  0:\n",
                "  cmp qword ptr [rbp+48], 0\n",
                "  jl 0f\n",
                "  cmp qword ptr [rbp+48], 0\n",
                "  je 10b\n",
                "  mov rax, [rbp+56]\n",
                "  sub rax, [rbp+64]\n",
                "  cmp rax, 0\n",
                "  jl 10b\n",
                "  mov rbx, [rbp+48]\n",
                "  sub rbx, 1\n",
                "  add rax, rbx\n",
                "  add rbx, 1\n",
                "  xor rdx, rdx\n",
                "  div rbx\n",
                "  jmp 1f\n",
                "  0:\n",
                "  mov rax, [rbp+64]\n",
                "  sub rax, [rbp+56]\n",
                "  cmp rax, 0\n",
                "  jl 10b\n",
                "  mov rbx, [rbp+48]\n",
                "  neg rbx\n",
                "  xor rdx, rdx\n",
                "  div rbx\n",
                "  cmp rdx, 0\n",
                "  je 1f\n",
                "  inc rax\n",
                "  1:\n",
                "  mov rsi, [rbp+72]\n",
                "  mov rsi, [rsi]\n",
                "  cmp qword ptr [rbp+64], rsi\n",
                "  jge 10b\n",
                "  cmp qword ptr [rbp+64], 0\n",
                "  jl 10b\n",
                "  cmp qword ptr [rbp+56], -1\n",
                "  jl 10b\n",
                "  imul rax, 16\n",
                "  add rax, 8\n",
                "  mov qword ptr [rbp-8], rax\n",
                "  push rax\n",
                "  call heapalloc\n",
                "  add rsp, 8\n",
                "  mov rbx, [rbp-8]\n",
                "  mov rsi, [rbp+72]\n",
                "  xor rdx, rdx\n",
                "  add rdx, [rbp+64]\n",
                "  mov rdi, 8\n",
                "  cmp qword ptr [rbp+48], 0\n",
                "  jg 4f\n",
                "  0:\n",
                "    cmp rdx, 0\n",
                "    jl 1f\n",
                "    cmp rdi, rbx\n",
                "    jge 1f\n",
                "    mov r15, rdx\n",
                "    imul r15, 16\n",
                "    add r15, 8\n",
                "    add r15, rsi\n",
                "    mov r8, [r15]\n",
                "    mov rcx, [r15+8]\n",
                "    cmp rcx, 0\n",
                "    je 13f\n",
                "    inc qword ptr [r8-8]\n",
                "    13:\n",
                "    mov qword ptr [rax+rdi], r8\n",
                "    mov qword ptr [rax+rdi+8], rcx\n",
                "    add rdi, 16\n",
                "    add rdx, [rbp+48]\n",
                "    jmp 0b\n",
                "  1:\n",
                "  jmp 1f\n",
                "  4:\n",
                "    cmp rdx, [rsi]\n",
                "    jge 1f\n",
                "    cmp rdi, rbx\n",
                "    jge 1f\n",
                "    mov r15, rdx\n",
                "    imul r15, 16\n",
                "    add r15, 8\n",
                "    add r15, rsi\n",
                "    mov r8, [r15]\n",
                "    mov rcx, [r15+8]\n",
                "    cmp rcx, 0\n",
                "    je 13f\n",
                "    inc qword ptr [r8-8]\n",
                "    13:\n",
                "    mov qword ptr [rax+rdi], r8\n",
                "    mov qword ptr [rax+rdi+8], rcx\n",
                "    add rdi, 16\n",
                "    add rdx, [rbp+48]\n",
                "    jmp 4b\n",
                "  1:\n",
                "  sub rdi, 8\n",
                "  shr rdi, 4\n",
                "  mov qword ptr [rax], rdi\n",
                "  add rsp, 8\n",
                "  pop r8\n",
                "  pop rcx\n",
                "  pop rdx\n",
                "  pop rbp\n",
                "  pop rsp\n",
                "  ret\n",
                "itype:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  mov rbp, rsp\n",
                "  mov rax, [rbp+24]\n",
                "  imul rax, 16\n",
                "  add rax, 16\n",
                "  mov r15, [rbp+32]\n",
                "  mov rax, [r15+rax]\n",
                "  pop rbp\n",
                "  pop rsp\n",
                "  ret\n",
                "printarr:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  mov rbp, rsp\n",
                "  sub rsp, 24\n",
                "  mov qword ptr [rbp-8], 0\n",
                "  mov qword ptr [rbp-16], 0\n",
                "  mov qword ptr [rbp-24], 0\n",
                "  mov r15, [rbp+24]\n",
                "  inc qword ptr [r15-8]\n",
                "  push [rbp+24]\n",
                "  call len\n",
                "  add rsp, 8\n",
                "  mov qword ptr [rbp-8], rax\n",
                "  mov r15, 16\n",
                "  push r15\n",
                "  call heapalloc\n",
                "  add rsp, 8\n",
                "  mov qword ptr [rax], 1\n",
                "  mov dword ptr [rax+8], 0x0000005b\n",
                "  push rax\n",
                "  push 1\n",
                "  call print\n",
                "  mov r15, [rsp+8]\n",
                "  sub qword ptr [r15-8], 1\n",
                "  add rsp, 16\n",
                "  sub rsp, 24\n",
                "  mov qword ptr [rsp+16], 0\n",
                "  mov qword ptr [rsp+8], 10\n",
                "  mov qword ptr [rsp], 1\n",
                "  mov rax, [rbp-8]\n",
                "  mov qword ptr [rsp+16], 0\n",
                "  mov qword ptr [rsp+8], rax\n",
                "  mov qword ptr [rsp], 1\n",
                "  xor rax, rax\n",
                "  mov [rbp-24], rax\n",
                "  2:\n",
                "  mov rax, [rsp+16]\n",
                "  mov [rbp-24], rax\n",
                "  cmp qword ptr [rsp], 0\n",
                "  jl 0f\n",
                "  cmp rax, [rsp+8]\n",
                "  jge 3f\n",
                "  jmp 1f\n",
                "  0:\n",
                "  cmp rax, [rsp+8]\n",
                "  jle 3f\n",
                "  1:\n",
                "  push [rbp+24]\n",
                "  push [rbp-24]\n",
                "  call itype\n",
                "  add rsp, 16\n",
                "  mov qword ptr [rbp-16], rax\n",
                "  mov rdx, 2\n",
                "  mov rcx, [rbp-16]\n",
                "  mov rax, rcx\n",
                "  cmp rcx, rdx\n",
                "  jne 0f\n",
                "  mov rcx, 1\n",
                "  jmp 1f\n",
                "  0:\n",
                "  mov rcx, -1\n",
                "  1:\n",
                "  mov rax, rcx\n",
                "  cmp rax, 1\n",
                "  jne 4f\n",
                "  5:\n",
                "  mov rax, [rbp+24]\n",
                "  mov r15, [rbp-24]\n",
                "  imul r15, 16\n",
                "  add r15, 8\n",
                "  lea r15, [rax+r15]\n",
                "  mov rax, [r15]\n",
                "  push rax\n",
                "  call printarr\n",
                "  add rsp, 8\n",
                "  jmp 6f\n",
                "  4:\n",
                "  mov rdx, 1\n",
                "  mov rcx, [rbp-16]\n",
                "  mov rax, rcx\n",
                "  cmp rcx, rdx\n",
                "  jne 0f\n",
                "  mov rcx, 1\n",
                "  jmp 1f\n",
                "  0:\n",
                "  mov rcx, -1\n",
                "  1:\n",
                "  mov rax, rcx\n",
                "  cmp rax, 1\n",
                "  jne 7f\n",
                "  8:\n",
                "  mov r15, 16\n",
                "  push r15\n",
                "  call heapalloc\n",
                "  add rsp, 8\n",
                "  mov qword ptr [rax], 1\n",
                "  mov dword ptr [rax+8], 0x00000027\n",
                "  push rax\n",
                "  push 1\n",
                "  call print\n",
                "  mov r15, [rsp+8]\n",
                "  sub qword ptr [r15-8], 1\n",
                "  add rsp, 16\n",
                "  mov rax, [rbp+24]\n",
                "  mov r15, [rbp-24]\n",
                "  imul r15, 16\n",
                "  add r15, 8\n",
                "  lea r15, [rax+r15]\n",
                "  mov rax, [r15]\n",
                "  push rax\n",
                "  push 1\n",
                "  call print\n",
                "  add rsp, 16\n",
                "  mov r15, 16\n",
                "  push r15\n",
                "  call heapalloc\n",
                "  add rsp, 8\n",
                "  mov qword ptr [rax], 1\n",
                "  mov dword ptr [rax+8], 0x00000027\n",
                "  push rax\n",
                "  push 1\n",
                "  call print\n",
                "  mov r15, [rsp+8]\n",
                "  sub qword ptr [r15-8], 1\n",
                "  add rsp, 16\n",
                "  jmp 9f\n",
                "  7:\n",
                "  mov rax, [rbp+24]\n",
                "  mov r15, [rbp-24]\n",
                "  imul r15, 16\n",
                "  add r15, 8\n",
                "  lea r15, [rax+r15]\n",
                "  mov rax, [r15]\n",
                "  push rax\n",
                "  call intstr\n",
                "  add rsp, 8\n",
                "  push rax\n",
                "  push 1\n",
                "  call print\n",
                "  add rsp, 16\n",
                "  9:\n",
                "  6:\n",
                "  push [rbp-24]\n",
                "  mov rdx, 1\n",
                "  mov rcx, [rbp-8]\n",
                "  sub rcx, rdx\n",
                "  mov rdx, rcx\n",
                "  pop rcx\n",
                "  mov rax, rcx\n",
                "  cmp rcx, rdx\n",
                "  jge 0f\n",
                "  mov rcx, 1\n",
                "  jmp 1f\n",
                "  0:\n",
                "  mov rcx, -1\n",
                "  1:\n",
                "  mov rax, rcx\n",
                "  cmp rax, 1\n",
                "  jne 10f\n",
                "  11:\n",
                "  mov r15, 16\n",
                "  push r15\n",
                "  call heapalloc\n",
                "  add rsp, 8\n",
                "  mov qword ptr [rax], 2\n",
                "  mov dword ptr [rax+8], 0x0000202c\n",
                "  push rax\n",
                "  push 1\n",
                "  call print\n",
                "  mov r15, [rsp+8]\n",
                "  sub qword ptr [r15-8], 1\n",
                "  add rsp, 16\n",
                "  jmp 12f\n",
                "  10:\n",
                "  12:\n",
                "  13:\n",
                "  mov rax, [rsp]\n",
                "  add qword ptr [rsp+16], rax\n",
                "  jmp 2b\n",
                "  14:\n",
                "  3:\n",
                "  add rsp, 24\n",
                "  mov r15, 16\n",
                "  push r15\n",
                "  call heapalloc\n",
                "  add rsp, 8\n",
                "  mov qword ptr [rax], 1\n",
                "  mov dword ptr [rax+8], 0x0000005d\n",
                "  push rax\n",
                "  push 1\n",
                "  call print\n",
                "  mov r15, [rsp+8]\n",
                "  sub qword ptr [r15-8], 1\n",
                "  add rsp, 16\n",
                "  mov rax, 0\n",
                "  jmp 99f\n",
                "  99:\n",
                "  mov r15, [rbp+24]\n",
                "  push r15\n",
                "  call _decarrcheck\n",
                "  add rsp, 8\n",
                "  add rsp, 24\n",
                "  pop rbp\n",
                "  pop rsp\n",
                "  ret\n",
                "printarrln:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  mov rbp, rsp\n",
                "  mov r15, [rbp+24]\n",
                "  inc qword ptr [r15-8]\n",
                "  push [rbp+24]\n",
                "  call printarr\n",
                "  add rsp, 8\n",
                "  push 0\n",
                "  call println\n",
                "  add rsp, 8\n",
                "  mov rax, 0\n",
                "  mov r15, [rbp+24]\n",
                "  push r15\n",
                "  call _decarrcheck\n",
                "  add rsp, 8\n",
                "  pop rbp\n",
                "  pop rsp\n",
                "  ret\n",
                "refcount:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  mov rbp, rsp\n",
                "  mov rax, [rbp+24]\n",
                "  mov rax, [rax-8]\n",
                "  pop rbp\n",
                "  pop rsp\n",
                "  ret\n"
            ]
        total_vars = []
        varIsFunc = {}
        #self.varTypes = prevVarTypes
        for tree in self.tokens:
            if (type(tree) is AssignmentNode and tree.value not in total_vars) or (type(tree) is FunctionAssign and tree.name not in total_vars):
                try:
                    total_vars.append(tree.identifier)
                    varIsFunc[tree.identifier] = False
                except:
                    total_vars.append(tree.name)
                    varIsFunc[tree.name] = True
        
        local_var_count = self.countVars(ProgramNode(self.tokens), ret, args)

        if len(args) == 0:
            self.addLine("push rsp")
            self.addLine("push rbp")
            self.addLine("mov rbp, rsp")
            if not (ret and not prevVars and not args and not objVars and not self.isFunc):
                self.addLine(f"sub rsp, {local_var_count*8}")
            for v in range(1, local_var_count+1):
                v *= 8
                if not (ret and not prevVars and not args and not objVars and not self.isFunc):
                    self.addLine(f"mov qword ptr [rbp-{v}], 0")
            for var, varType in objVars.items():
                if not (varType.isType(TokenType.INT) or varType.isType(TokenType.FLOAT) or varType.isType(TokenType.BOOL)):
                    if varType.isType(TokenType.ARRAY):
                        varTypes[var] = "objectarray"
                    else:
                        varTypes[var] = "object"
                    self.addLine(f"mov r15, {self.getVarLoc(var)}")
                    self.addLine(f"inc qword ptr [r15-8]")
                else:
                    varTypes[var] = "native"

        for tree in self.tokens:
            self.addLine("")
            self.traverse_tree(tree, True, args)
        if len(args) == 0:
            self.addLine("99:")
            # for var in objVars:
            #     if varTypes[var] == "object":
            #         self.addLine(f"mov r15, {self.getVarLoc(var)}")
            #         self.addLine(f"dec qword ptr [r15-8]")
            for var in self.vars:
                if var in varTypes and "object" in varTypes[var]: # == "object":
                    self.addLine(f"mov r15, {self.getVarLoc(var)}")
                    if "array" in varTypes[var]:
                        self.addLine("push r15")
                        self.addLine("call _decarrcheck")
                        self.addLine("add rsp, 8")
                    else:
                        self.addLine("dec qword ptr [r15-8]")
            if not (ret and not prevVars and not args and not objVars and not self.isFunc):
                self.addLine(f"add rsp, {local_var_count*8}")
            self.addLine("pop rbp")
            self.addLine("pop rsp")

        if not ret and len(args) == 0:
            self.addLine("ret")
        
        while len(self.skipped_funcs) > 0:
            if not ret:
                self.text += self.main
                self.main = []
            func = self.skipped_funcs[0]
            self.skipped_funcs.remove(func)
            self.addFunc(func)

        for var, typ in self.localVarTypes.items():
            varTypes[var] = typ
        
        if not ret:
            #self.addLine("ret")
            if not "data" in args:
                return self.text + self.main, self.rodata
            return self.text + self.main, self.rodata, self.data[1:]
        if "main" in args:
            if not "data" in args:
                return self.main, self.rodata
            return self.main, self.rodata, self.data[1:]

        first_half = [".intel_syntax noprefix\n", ".global _start\n", ".section .rodata\n"] + self.rodata + [".data\n"] + self.data
        second_half = [".text\n"] + self.text + ["_start:\n"] + self.main
        return first_half + second_half

    def countVars(self, node, ret, args):
        if type(node) is AssignmentNode:
            if ret:
                if not node.identifier in self.vars:
                    self.addData(node.identifier)
                    self.vars[node.identifier] = f"[{node.identifier}]"
                    return 1
                return 0
            else:
                if node.identifier not in self.vars:
                    self.addVar(node.identifier, 0, node.extra)
                    return 1
                return 0
        elif type(node) is ProgramNode:
            count = 0
            for v in node.branches:
                count += self.countVars(v, ret, args)
            return count
        elif type(node) is IFNode:
            count = 0
            for v in node.code:
                count += self.countVars(v, ret, args)
            return count
        elif type(node) is WHILENode:
            count = 0
            for v in node.code:
                count += self.countVars(v, ret, args)
            return count
        elif type(node) is FORNode:
            count = 1#self.countVars(node.var, ret, args)
            for v in node.code:
                count += self.countVars(v, ret, args)
            return count
        else:
            return 0

    def addVar(self, var, regOrVal=0, extra=""):
        if not (self.vars.get(var, None) is None):
            return
        if self.isFunc:
            self.varAmt += 1
            self.vars[var] = f"[rbp-{self.varAmt*8}]"
            if var in varTypes and extra == "new":
                self.localVarTypes[var] = varTypes[var]
                varTypes[var] = "native"
        else:
            self.addData(var)
            self.vars[var] = f"[{var}]"
        if regOrVal != 0:
            self.setVarAsm(var, regOrVal)

    
    def addFunc(self, funcNode: FunctionAssign):
        local = {}                                                                      # all locals in function
        count = len(funcNode.args)                                                      # num of all locals in function
        for var, varType in funcNode.args.items():
            local[var] = f"[rbp+{16+8*count}]"                                          # sets all local memory locations
            count -= 1                                                                  # updates local count
        local["%parent"] = self.vars
        reference = local
        while not reference.get("%parent", None) is None:                               # if parent then continue into loop
            reference = reference["%parent"]                                            # store reference to parent
            for key in reference:                                                       # loop through reference to change locals without discarding info
                if len(reference[key]) >= 7 and key != "%parent" and reference[key][1:5] == "rbp+":
                    reference[key] = reference[key][0] + "r10+" + reference[key][5:]    # replace if not in current scope
        main = CodeGenerator(ProgramNode(funcNode.code), True).Generate(False, local, [], funcNode.args)
        readOnly = main[1]
        main = main[0]
        self.rodata += readOnly
        #gen = CodeGenerator(ProgramNode(funcNode.code), True).Generate(False, local)    # gets function body code
        self.addText(f"{funcNode.name}:")                                               # funcname:
        self.text += main #gen                                                                #   body

    
    def loadVarAsm(self, var, reg):
        if not var in self.rodataMap:
            self.addLine(f"mov {reg}, {self.getVarLoc(var)}")
        else:
            self.addLine(f"lea {reg}, {self.rodataMap[var]}")
    
    def setVarAsm(self, var, regOrVal):
        self.addLine(f"mov {self.getVarLoc(var)}, {regOrVal}")

    def addLine(self, txt: str):
        self.main.append(txt + "\n")
    def addText(self, txt: str):
        self.text.append(txt + "\n")
    def addData(self, txt: str):
        self.data.append(txt + ": .quad 0\n")
    def addRoData(self, data, body):
        if type(data) is list:
            newdata = ""
            for v in data:
                newdata += v
            data = newdata
        if not data in self.rodataMap:
            self.rodataMap[data] = next(getRoDataLabel)
            self.rodata.append(self.rodataMap[data] + ":\n")
            for v in body:
                self.rodata.append(v + "\n")

    def isNode(self, tree):
        exclude = not type(tree) is AssignmentNode and not type(tree) is UnaryNode and not type(tree) is FunctionCall and not type(tree) is LOOPMODNode
        if getattr(tree, "left", None) is None and exclude:
            return True
        return False

    def getVarLoc(self, var):
        current = self.vars
        if var in current:
            return current[var]
        current = current["%parent"]
        self.addLine("mov r10, [rbp]")
        while not var in current:
            current = current["%parent"]
            self.addLine("mov r10, [r10]")
        return current[var]

    def conditional(self, valOrReg1, cond: str | Token, valOrReg2=None):
        if type(cond) is Token:
            cond = cond.value
        if cond.lower() != "and" and cond.lower() != "or":
            self.addLine(f"cmp {valOrReg1}, {valOrReg2 if valOrReg2 else "1"}")
            self.addLine(f"{self.conds[cond]} 0f")
            self.addLine(f"mov {valOrReg1}, 1")
            self.addLine("jmp 1f")
            self.addLine("0:")
            self.addLine(f"mov {valOrReg1}, -1")
            self.addLine("1:")
        elif cond.lower() == "and":
            self.addLine(f"cmp {valOrReg1}, 1")
            self.addLine("jne 0f")
            self.addLine(f"cmp {valOrReg2}, 1")
            self.addLine("jne 0f")
            self.addLine(f"mov {valOrReg1}, 1")
            self.addLine("jmp 1f")
            self.addLine("0:")
            self.addLine(f"mov {valOrReg1}, -1")
            self.addLine("1:")
        elif cond.lower() == "or":
            self.addLine(f"cmp {valOrReg1}, 1")
            self.addLine("je 0f")
            self.addLine(f"cmp {valOrReg2}, 1")
            self.addLine("je 0f")
            self.addLine("jmp 1f")
            self.addLine("0:")
            self.addLine(f"mov {valOrReg1}, 1")
            self.addLine("jmp 2f")
            self.addLine("1:")
            self.addLine(f"mov {valOrReg1}, -1")
            self.addLine("2:")

    def insertOperation(self, valOrReg1, operation, valOrReg2):
        if operation == "+":
            self.addLine(f"add {valOrReg1}, {valOrReg2}")
        elif operation == "-":
            self.addLine(f"sub {valOrReg1}, {valOrReg2}")
        elif operation == "*":
            self.addLine(f"imul {valOrReg1}, {valOrReg2}")
        elif operation == "^":
            self.addLine(f"call _exponent")
        elif operation == "//":
            if valOrReg1 == "rdx":
                self.addLine("mov r8, rdx")
                valOrReg1 = "r8"
            elif valOrReg2 == "rdx":
                self.addLine("mov r8, rdx")
                valOrReg2 = "r8"
            self.addLine("xor rdx, rdx")
            self.addLine(f"mov rax, {valOrReg1}")
            self.addLine(f"mov rcx, {valOrReg2}")
            self.addLine("div rcx")
            self.addLine("mov rcx, rax")
        elif operation == "%":
            if valOrReg1 == "rdx":
                self.addLine("mov r8, rdx")
                valOrReg1 = "r8"
            elif valOrReg2 == "rdx":
                self.addLine("mov r8, rdx")
                valOrReg2 = "r8"
            self.addLine(f"mov rax, {valOrReg1}")
            self.addLine(f"mov rcx, {valOrReg2}")
            self.addLine("xor rdx, rdx")
            self.addLine("div rcx")
            self.addLine("mov rcx, rdx")
        else:
            self.addLine(f"mov rax, {valOrReg1}")
            self.conditional(valOrReg1, operation, valOrReg2 if valOrReg2 else None)

    def insertUnary(self, valOrReg, operation):
        if operation == "-":
            self.addLine(f"neg {valOrReg}")
        if operation == "+":
            self.addLine(f"push {valOrReg}")
            self.addLine("call _abs")
            self.addLine("add rsp, 8")
            self.addLine(f"mov {valOrReg}, rax")

    def retIsObj(self, item: EndNode):
        return not ((type(item) is INTNode) or (type(item) is FLOATNode) or (type(item) is BOOLNode))

    def checkVarAppearance(self, item, var: str):       # NEED TO ADD BRACKET CHECKING FOR SINGLE INDEXES
        if type(item) is ARRAYNode:
            for cont in item.contents:
                if self.checkVarAppearance(cont, var):
                    return True
            return False
        elif type(item) is IDENTIFIERNode:
            return item.value == var
        else:
            return False
        # if type(item) is BracketUse:
        #     return (self.checkVarAppearance(item.args) or self.checkVarAppearance(item.assign)) and not item.isSlice

    def traverse_tree(self, tree, first=False, args: list=[]):
        if type(tree) is FunctionCall:
            undo = []
            doToString = tree.name == "print" or tree.name == "println" or tree.name == "strcon"
            for arg in tree.args if not (tree.name == "print" or tree.name == "println") else tree.args[::-1]:
                retType = self.traverse_tree(arg, False, ["print", "nonliteral"] if doToString else ["nonliteral"])
                if retType == "native" and type(arg) is OperationNode:
                    self.addLine("call intstr")
                    self.addLine("add rsp, 8")
                    self.addLine("push rax")
                undo.append(retType)
            if tree.name == "print" or tree.name == "println":
                self.addLine(f"push {len(tree.args)}")
                undo.append("")
            elif len(tree.args) == 0 and tree.name == "exit":
                self.addLine("push 0")
                self.addLine("call exit")
                return
            self.addLine(f"call {tree.name}")
            for i in range(len(undo)):
                var = undo[i]
                if var == "object":
                    self.addLine(f"mov r15, [rsp+{(len(undo)-1-i)*8}]")
                    self.addLine("sub qword ptr [r15-8], 1")
                elif var == "objectarray":
                    self.addLine(f"mov r15, [rsp+{(len(undo)-1-i)*8}]")
                    self.addLine("push r15")
                    self.addLine("call _decarrcheck")
                    self.addLine("add rsp, 8")
            self.addLine(f"add rsp, {len(tree.args)*8 + (8 if tree.name == "print" or tree.name == "println" else 0)}")
            if not first:
                self.addLine("push rax")
            baked = SemanticAnalyzer(ProgramNode([])).baked_functions
            try:
                nat = (baked[tree.name] is INTNode) or (baked[tree.name] is FLOATNode) or (baked[tree.name] is BOOLNode)
            except:
                nat = (tree.retType is INTNode) or (tree.retType is FLOATNode) or (tree.retType is BOOLNode)
            if "print" in args and nat:
                self.addLine("call intstr")
                self.addLine("add rsp, 8")
                self.addLine("push rax")
            if tree.name in baked and nat:
                return "native"
            return "objectvar" if not nat else "native"
        if type(tree) is OperationNode:
            self.traverse_tree(tree.left)
            self.traverse_tree(tree.right)
            self.addLine("pop rdx")         # right side of equation, second register
            self.addLine("pop rcx")         # left side of equation, first register
            self.insertOperation("rcx", tree.operation, "rdx")  # inserts the whole equation, left op right
            if not first:
                self.addLine("push rcx\n")
            if first:
                self.addLine("mov rax, rcx\n")
            return "native"

        if type(tree) is CONDMODNode:
            type1 = self.traverse_tree(tree.left)
            type2 = self.traverse_tree(tree.right)
            self.addLine("pop rdx")
            self.addLine("pop rcx")
            self.insertOperation("rcx", tree.mod, "rdx")
            self.addLine("push rcx")
            return "native"

        if type(tree) is IFNode:            # must use unique letter names for each if statement, or nested functions will get confused or reuse already used names
            startLabel = next(getIfStartLabel)
            elseLabel = next(getIfElseLabel)
            endLabel = next(getIfEndLabel)
            self.traverse_tree(tree.conditions, False, args)
            # always a CONDMOD node, traverse it and insert cmp statements at and/or ops
            
            self.addLine("pop rax")
            self.addLine("cmp rax, 1")
            self.addLine(f"jne {elseLabel}")

            self.addLine(f"{startLabel}:")
            main = CodeGenerator(ProgramNode(tree.code), False).Generate(False, self.vars, ["main"] + args)
            readOnly = main[1]
            main = main[0]
            self.main += main
            self.rodata += readOnly
            #self.main += CodeGenerator(ProgramNode(tree.code), False).Generate(False, self.vars, ["main"])
            self.addLine(f"jmp {endLabel}")
            self.addLine(f"{elseLabel}:")
            if len(tree.codeelse) > 0:
                main = CodeGenerator(ProgramNode(tree.codeelse), False).Generate(False, self.vars, ["main"] + args)
                readOnly = main[1]
                main = main[0]
                self.rodata += readOnly
                self.main += main
                #self.main += CodeGenerator(ProgramNode(tree.codeelse), False).Generate(False, self.vars, ["main"])
            self.addLine(f"{endLabel}:")
            return

        if type(tree) is WHILENode:
            startLabel = next(getWhileStartLabel)
            endLabel = next(getWhileEndLabel)
            contLabel = next(getWhileContinueLabel)
            brkLabel = next(getWhileBreakLabel)
            self.addLine(f"{startLabel}:")

            self.traverse_tree(tree.conditions, False)
            # NOT always a CONDMOD node, traverse it and insert cmp statements at and/or ops
            self.addLine("pop rax")
            self.addLine("cmp rax, 1")
            self.addLine(f"jne {endLabel}")
            main = CodeGenerator(ProgramNode(tree.code), False).Generate(False, self.vars, ["main", "continueLabel", contLabel, "breakLabel", brkLabel])
            readOnly = main[1]
            main = main[0]
            self.main += main
            self.rodata += readOnly
            #self.main += CodeGenerator(ProgramNode(tree.code), False).Generate(False, self.vars, ["main", "continueLabel", contLabel, "breakLabel", brkLabel])
            self.addLine(f"{contLabel}:")
            self.addLine(f"jmp {startLabel}")
            self.addLine(f"{brkLabel}:")
            self.addLine(f"{endLabel}:")
            return

        if type(tree) is FORNode:
            startLabel = next(getWhileStartLabel)
            endLabel = next(getWhileEndLabel)
            contLabel = next(getWhileContinueLabel)
            brkLabel = next(getWhileBreakLabel)
            self.addVar(tree.var, 0, "new")
            isRange = type(tree.parse_item) == FunctionCall and tree.parse_item.name == "range"
            if isRange:
                varTypes[tree.var] = "native"
                self.addLine("sub rsp, 24")
                call = tree.parse_item
                if len(call.args) == 1:
                    self.traverse_tree(call.args[0])
                    self.addLine("pop rax")
                    self.addLine("mov qword ptr [rsp+16], 0")
                    self.addLine("mov qword ptr [rsp+8], rax")
                    self.addLine("mov qword ptr [rsp], 1")
                    self.addLine("xor rax, rax")
                elif len(call.args) >= 2:
                    self.traverse_tree(call.args[1])
                    self.addLine("pop rax")
                    self.addLine("mov qword ptr [rsp+8], rax")
                    if len(call.args) == 3:
                        self.traverse_tree(call.args[2])
                        self.addLine("pop rax")
                        self.addLine("mov qword ptr [rsp], rax")
                    else:
                        self.addLine("mov qword ptr [rsp], 1")
                    self.traverse_tree(call.args[0])
                    self.addLine("pop rax")
                    self.addLine("mov qword ptr [rsp+16], rax")
                else:
                    self.addLine("mov qword ptr [rsp+16], 0")
                    self.addLine("mov qword ptr [rsp+8], 10")
                    self.addLine("mov qword ptr [rsp], 1")
                self.setVarAsm(tree.var, "rax")
            else:
                self.addLine("sub rsp, 32")
                varTypes[tree.var] = tree.asType
                self.traverse_tree(tree.parse_item)
                self.addLine("pop rax")
                self.addLine("mov qword ptr [rsp+24], rax")
                self.addLine("mov qword ptr [rsp+16], 0")
                self.addLine("mov rax, [rax]")
                self.addLine("mov qword ptr [rsp+8], rax")
                self.addLine("mov qword ptr [rsp], 1")
            self.addLine(f"{startLabel}:")
            self.addLine(f"mov rax, [rsp+16]")
            if isRange:
                self.setVarAsm(tree.var, "rax")
                self.addLine("cmp qword ptr [rsp], 0")
                self.addLine("jl 0f")
                self.addLine("cmp rax, [rsp+8]")
                self.addLine(f"jge {endLabel}")
                self.addLine("jmp 1f")
                self.addLine("0:")
                self.addLine("cmp rax, [rsp+8]")
                self.addLine(f"jle {endLabel}")
                self.addLine("1:")
            else:
                self.addLine("mov r15, [rsp+16]")
                self.addLine("cmp qword ptr [rsp], 0")
                self.addLine("jl 0f")
                self.addLine("cmp r15, [rsp+8]")
                self.addLine(f"jge {endLabel}")
                self.addLine("jmp 1f")
                self.addLine("0:")
                self.addLine("cmp r15, [rsp+8]")
                self.addLine(f"jle {endLabel}")
                self.addLine("1:")

                self.addLine("mov r15, [rsp+24]")
                self.addLine("imul rax, 16")
                self.addLine("add rax, 8")
                self.addLine("push qword ptr [r15+rax+8]")  # r15 is type
                self.addLine("push [r15+rax]")
                self.addLine("cmp qword ptr [r15+rax+8], 1")
                self.addLine("jl 0f")
                self.addLine("pop rax")
                self.addLine("inc qword ptr [rax-8]")
                self.addLine("jmp 1f")
                self.addLine("0:")
                self.addLine("pop rax")
                self.addLine("1:")
                self.addLine("push rax")                    # rax is the item
                self.setVarAsm(tree.var, "rax")

            main = CodeGenerator(ProgramNode(tree.code), self.isFunc, self.varAmt).Generate(False, self.vars, ["main", "data", "continueLabel", contLabel, "breakLabel", brkLabel, "forloop"])
            readOnly = main[1]
            data = main[2]
            main = main[0]
            self.main += main
            self.rodata += readOnly
            self.data += data

            self.addLine(f"{contLabel}:")
            if not isRange:
                self.addLine("mov rax, [rsp+16]")
                self.addLine("add qword ptr [rsp+32], rax")
                self.addLine("pop rax")     # rax is the item
                self.addLine("pop r15")     # r15 is the type
                self.addLine("cmp r15, 1")
                self.addLine("jl 2f")
                self.addLine("cmp r15, 2")
                self.addLine("jl 1f")
                self.addLine("push rax")
                self.addLine("call _decarrcheck")
                self.addLine("add rsp, 8")
                self.addLine("jmp 2f")
                self.addLine("1:")
                self.addLine("dec qword ptr [rax-8]")
                self.addLine("2:")
            else:
                self.addLine("mov rax, [rsp]")
                self.addLine("add qword ptr [rsp+16], rax")
            self.addLine(f"jmp {startLabel}")
            self.addLine(f"{brkLabel}:")
            if not isRange:
                self.addLine("pop rax")     # rax is the item
                self.addLine("pop r15")     # r15 is the type
                self.addLine("cmp r15, 1")
                self.addLine("jl 2f")
                self.addLine("cmp r15, 2")
                self.addLine("jl 1f")
                self.addLine("push rax")
                self.addLine("call _decarrcheck")
                self.addLine("add rsp, 8")
                self.addLine("jmp 2f")
                self.addLine("1:")
                self.addLine("dec qword ptr [rax-8]")
                self.addLine("2:")
            self.addLine(f"{endLabel}:")
            if isRange:
                self.addLine("add rsp, 24")
            else:
                self.addLine("add rsp, 32")
            if not isRange:
                self.addLine(f"mov qword ptr {self.getVarLoc(tree.var)}, 0")
                varTypes[tree.var] = "native"
            return

        if type(tree) is LOOPMODNode:
            if tree.mod.lower() == "continue":
                self.addLine(f"jmp {args[args.index("continueLabel")+1]}")
            elif tree.mod.lower() == "break":
                self.addLine(f"jmp {args[args.index("breakLabel")+1]}")
            return

        if type(tree) is FunctionAssign:
            self.skipped_funcs.append(tree)
            return

        if type(tree) is FunctionReturn:
            retType = self.traverse_tree(tree.value, False, ["nonliteral", "dec"])
            self.addLine(f"pop rax")
            if "forloop" in args:
                self.addLine("add rsp, 24")
            self.addLine("jmp 99f")
            return retType
        
        if type(tree) is UnaryNode:
            self.traverse_tree(tree.value)
            self.addLine("pop rcx")
            self.insertUnary("rcx", tree.operation)
            self.addLine("push rcx")
            return "native"

        if type(tree) is AssignmentNode:
            inTmp = False
            inVarsAndTypes = tree.identifier in self.vars and tree.identifier in varTypes
            varTypeBefore = varTypes[tree.identifier] if inVarsAndTypes else ""
            if inVarsAndTypes and (varTypes[tree.identifier] == "object" or "array" in varTypes[tree.identifier]):
                inTmp = True
                self.addLine(f"mov r15, {self.getVarLoc(tree.identifier)}")
                self.addLine("push r15")
                #self.addLine("mov qword ptr [_tmpvar], r15")
            self.addVar(tree.identifier, "new" if not tree.extra else tree.extra)
            newType = self.traverse_tree(tree.value, False, ["nonliteral"])
            varTypes[tree.identifier] = newType if not "var" in newType else newType[:-3]
            if first:
                self.addLine("pop rax")
            if "object" in newType and "var" in newType:
                self.addLine("inc qword ptr [rax-8]")
            self.setVarAsm(tree.identifier, "rax")
            if inTmp:
                self.addLine("pop r15")
                #self.addLine("mov r15, [rsp]")
                if "array" in varTypeBefore: #"array" in varTypes[tree.identifier]:
                    self.addLine("push r15")
                    self.addLine("call _decarrcheck")
                    self.addLine("add rsp, 8")
                else:
                    self.addLine("dec qword ptr [r15-8]")
            return

        if type(tree) is BracketUse:
            if tree.assign != False:
                assignType = self.traverse_tree(tree.assign)    # the type that is being assigned
                varType = self.traverse_tree(tree.item)         # check this for strings later, its the item being indexed to change
                if not type(tree.args[0]) is str:
                    self.traverse_tree(tree.args[0])
                else:
                    self.addLine(f"push {tree.args[0]}")
                self.addLine("pop r15")
                self.addLine("pop rax")
                self.addLine("call _checkarrtype")
                self.addLine("pop r15")                     # pops value to assign into r15
                if assignType == "objectvar":
                    self.addLine("mov qword ptr [rax+8], 1")
                elif assignType == "objectarrayvar" or assignType == "objectarray":
                    self.addLine("mov qword ptr [rax+8], 2")
                else:
                    self.addLine("mov qword ptr [rax+8], 0")
                self.addLine("mov qword ptr [rax], r15")
                if "var" in assignType and not "native" in assignType:
                    self.addLine("inc qword ptr [r15-8]")
                return
            elif tree.isSlice:
                varType = self.traverse_tree(tree.item)
                treeargs = tree.args + ([":"]*(3-len(tree.args)))
                for i in range(3):
                    arg = treeargs[i]
                    if type(arg) != str:
                        self.traverse_tree(arg)
                    else:
                        if i == 0:
                            if arg == ":" and type(treeargs[2]) is str and treeargs[2][0] == "-":
                                self.addLine("mov r15, [rsp]")
                                self.addLine("mov r15, [r15]")
                                self.addLine("dec r15")
                                self.addLine("push r15")
                            elif arg != ":":
                                self.addLine(f"push {arg}")
                            else:
                                self.addLine("push 0")
                        elif i == 1:
                            if arg == ":" and type(treeargs[2]) is str and treeargs[2][0] == "-":
                                self.addLine("push -1")
                            elif arg != ":":
                                self.addLine(f"push {arg}")
                            else:
                                self.addLine("mov r15, [rsp+8]")
                                self.addLine("push qword ptr [r15]")
                        else:
                            if arg == ":":
                                self.addLine("push 1")
                            else:
                                self.addLine(f"push {arg}")
                if not "array" in varType:
                    self.addLine("call _strsplit")
                else:
                    self.addLine("call _arrsplit")
                self.addLine("add rsp, 32")
                self.addLine("push rax")
                return varType if not "var" in varType else varType[:-3]
            else:
                varType = self.traverse_tree(tree.item)
                if not "array" in varType:
                    if type(tree.args[0]) is str:
                        self.addLine(f"push {tree.args[0]}")
                        self.addLine(f"mov r15, {tree.args[0]}")
                    else:
                        self.traverse_tree(tree.args[0])
                        self.addLine("mov r15, [rsp]")
                    self.addLine("inc r15")
                    self.addLine("push r15")
                    self.addLine("push 1")
                    self.addLine("call _strsplit")
                    self.addLine("add rsp, 32")
                    self.addLine("push rax")
                    return "object"
                else:
                    self.addLine("pop rax")
                    if type(tree.args[0]) is str:
                        self.addLine(f"mov r15, {tree.args[0]}")
                    else:
                        self.traverse_tree(tree.args[0])
                        self.addLine("pop r15")
                    self.addLine("imul r15, 16")
                    self.addLine("add r15, 8")
                    self.addLine("lea r15, [rax+r15]")
                    self.addLine("mov rax, [r15]")
                    self.addLine("push rax")
                    if "print" in args and "native" in tree.extract:
                        self.addLine("call intstr")
                        self.addLine("add rsp, 8")
                        self.addLine("push rax")
                        tree.extract = "object"
                    return tree.extract + "var"

        if self.isNode(tree):
            if type(tree) is INTNode:
                self.addLine(f"push {tree.value}")
                if "print" in args:
                    self.addLine("call intstr")
                    self.addLine("add rsp, 8")
                    self.addLine("push rax")
                return "native"
            if type(tree) is BOOLNode:
                self.addLine(f"push {1 if tree.value == True else -1}")
                if "print" in args:
                    self.addLine("call intstr")
                    self.addLine("add rsp, 8")
                    self.addLine("push rax")
                return "native"
            if type(tree) is IDENTIFIERNode:
                self.addLine(f"push {self.getVarLoc(tree.value)}")
                if "print" in args and varTypes[tree.value] == "native":
                    self.addLine("call intstr")
                    self.addLine("add rsp, 8")
                    self.addLine("push rax")
                return varTypes[tree.value] + "var"
            if type(tree) is NONENode:
                self.addLine("push 0")
                if "print" in args:
                    self.addLine("call intstr")
                    self.addLine("add rsp, 8")
                    self.addLine("push rax")
                return
            if type(tree) is STRINGNode:
                if True: #"nonliteral" in args:
                    byteAmt = 16
                    value = tree.value
                    size = len(value)+9
                    while byteAmt < size:
                        byteAmt += 16
                    self.addLine(f"mov r15, {byteAmt}")
                    self.addLine(f"push r15")
                    self.addLine("call heapalloc")
                    self.addLine("add rsp, 8")
                    self.addLine(f"mov qword ptr [rax], {len(value)}")
                    for i in range((len(value) + 3) // 4, -1, -1):
                        chars = ""
                        for v in range(3, -1, -1):
                            index = i*4+v
                            if index < len(value):
                                chars += value[index]
                            else:
                                chars = "00" + chars
                        if chars == "00000000":
                            continue
                        self.addLine(f"mov dword ptr [rax+{i*4+8}], 0x{chars}")
                if "dec" in args:
                    self.addLine("dec qword ptr [rax-8]")
                self.addLine("push rax")
                return "object"
            if type(tree) is ARRAYNode:
                self.traverse_tree(tree.size)
                self.addLine("pop rax")
                self.addLine("push rax")
                self.addLine("imul rax, 16")
                self.addLine("add rax, 8")
                self.addLine("push rax")
                self.addLine("call heapalloc")
                self.addLine("add rsp, 8")
                self.addLine("pop r15")
                self.addLine("mov qword ptr [rax], r15")
                self.addLine("push rax")
                for i in range(len(tree.contents)):
                    v = tree.contents[i]
                    objType = self.traverse_tree(v)
                    self.addLine("pop r15")
                    self.addLine("mov rax, [rsp]")
                    if "object" in objType and ("var" in objType or "array" in objType):
                        if "var" in objType:
                            self.addLine("inc qword ptr [r15-8]")
                        if "array" in objType:
                            self.addLine(f"mov qword ptr [rax+{i*16+16}], 2")
                        elif "object" in objType:
                            self.addLine(f"mov qword ptr [rax+{i*16+16}], 1")
                    elif "object" in objType:
                        self.addLine(f"mov qword ptr [rax+{i*16+16}], 1")
                    #else:
                        #self.addLine(f"mov qword ptr [rax+{i*8+16}], 0")
                    #self.addLine("mov rax, [rsp]")
                    self.addLine(f"mov qword ptr [rax+{i*16+8}], r15")
                if "dec" in args:
                    self.addLine("dec qword ptr [rax-8]")
                return "objectarray"

        raise SyntaxError(f"Forgot to add {tree} here")


class Optimizer():
    def __init__(self, source: list[str]):
        self.source = source
    
    def Optimize(self) -> list[str]:
        push1 = ""
        push2 = ""
        push1ln = 0
        push2ln = 0
        start = len(CodeGenerator(ProgramNode([])).Generate())
        for i in range(start, len(self.source)):
            # i += start
            line = self.source[i]
            if not line or line[:1] == " ":
                continue
            elif line == "push rsp" or line == "pop rsp" or line == "push rbp" or line == "pop rbp" or ":" in line or "call" in line:
                push1 = ""
                push1ln = 0
                push2 = ""
                push2ln = 0
                continue
            if line[:4] == "push":
                if not push1:
                    push1 = line[5:]
                    push1ln = i
                elif not push2:
                    push2 = line[5:]
                    push2ln = i
                else:
                    push1 = push2
                    push1ln = push2ln
                    push2 = line[5:]
                    push2ln = i
            elif line[:3] == "pop":
                if push2:
                    self.source[push2ln] = ""
                    self.source[i] = f"mov {line[4:-1]}, {push2}\n"
                    push2 = ""
                elif push1:
                    self.source[push1ln] = ""
                    self.source[i] = f"mov {line[4:-1]}, {push1}\n"
                    push1 = ""
            else:
                push1 = ""
                push1ln = 0
                push2 = ""
                push2ln = 0

        invalidateRegs = {
            "eax": "rax", "ax": "rax", "al": "rax", "ah": "rax",
            "ebx": "rbx", "bx": "rbx", "bl": "rbx", "bh": "rbx",
            "ecx": "rcx", "cx": "rcx", "cl": "rcx", "ch": "rcx",
            "edx": "rdx", "dx": "rdx", "dl": "rdx", "dh": "rdx",
            "esi": "rsi", "si": "rsi", "sil": "rsi",
            "edi": "rdi", "di": "rdi", "dil": "rdi",
            "ebp": "rbp", "bp": "rbp", "bpl": "rbp",
            "esp": "rsp", "sp": "rsp", "spl": "rsp",
            "r8d": "r8", "r8w": "r8", "r8b": "r8",
            "r9d": "r9", "r9w": "r9", "r9b": "r9",
            "r10d": "r10", "r10w": "r10", "r10b": "r10",
            "r11d": "r11", "r11w": "r11", "r11b": "r11",
            "r12d": "r12", "r12w": "r12", "r12b": "r12",
            "r13d": "r13", "r13w": "r13", "r13b": "r13",
            "r14d": "r14", "r14w": "r14", "r14b": "r14",
            "r15d": "r15", "r15w": "r15", "r15b": "r15"
        }
        regs = {}
        for i in range(start, len(self.source)):
            # i += start
            line = self.source[i]
            if not line or line[:1] == " ":
                continue
            elif line[:4] == "push" or line[:3] == "xor":
                reg = line[5:].strip("\n") if line[:4] == "push" else line[4:line.index(",")]
                if reg in regs:
                    del regs[reg]
                elif reg in invalidateRegs and invalidateRegs[reg] in regs:
                    del regs[invalidateRegs[reg]]
                continue
            elif line[:3] == "mov":                                             #     reg
                builtreg = line[4:line.index(",")]                              # mov rax, 10
                built = line[line.rindex(",")+2:line.index("\n")].strip("\n")   # mov rbx, rax
                if builtreg in regs:                                            #          built
                    movln = regs[builtreg][0]
                    data = regs[builtreg][1]
                    if built == data[0]:                # if new built is the same as the old register
                        if "[" in builtreg and not "qword ptr" in builtreg:
                            self.source[movln] = f"mov qword ptr {builtreg}, {data[1]}\n"
                        else:
                            self.source[movln] = f"mov {builtreg}, {data[1]}\n"
                if not "[" in built:
                    regs[builtreg] = (i, (builtreg, built))
                elif builtreg in regs:
                    del regs[builtreg]

        newList: list[str] = self.source[:start]
        for i in range(start, len(self.source)):
            v = self.source[i]
            l = newList[-1]
            if not v or v.count("\n") == len(v):
                continue
            elif v[:10] == "sub rsp, 0" or v[:10] == "add rsp, 0":
                continue
            while v.endswith("\n\n"):
                v = v[:-1]
            if v[:3] == "mov":
                if v[4:v.index(",")] == v[v.index(",")+2:-1]:
                    continue
            if v[:3] == "mov" and l[:3] == "mov":
                first = l[4:l.index(",")]
                second = v[v.index(",")+2:-1]
                if first == second:
                    val = l[l.index(",")+2:-1]
                    place = v[4:v.index(",")]
                    if not "[" in val and not "qword ptr" in place:
                        if place == val:
                            continue
                        newList[-1] = ""
                        if "[" in place:
                            newList.append(f"mov qword ptr {place}, {val}\n")
                        else:
                            newList.append(f"mov {place}, {val}\n")
                        continue
            newList.append(v)

        for i in range(start, len(newList)):
            v = newList[i]
            l = newList[i-1]
            if v[:3] == "mov" and l[:3] == "mov":
                strt = l.index("[") if " ptr" in l else 4
                mov1 = l[strt:l.index(",")]
                mov2 = l[l.index(",")+2:]
                if f"{mov2}, {mov1}" == v[v.index("[") if " ptr" in v else 4:]:
                    newList[i] = ""
        return newList




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KOG compiler")
    parser.add_argument("source", help="path to the .kog file")
    parser.add_argument("output", help="path for the .s file")
    parser.add_argument("--no-optim", action="store_true", help="disable optimizations")
    args = parser.parse_args()

    optimize = not args.no_optim
    out = Compiler(args.source).Compile(optimize)
    with open(args.output, "w") as f:
        if type(out) is list:
            f.writelines(out)
        else:
            f.write(out)
    # try:
    #     out = Compiler("./Input.kog").Compile(True)
    #     with open("./Input.s", "w") as f:
    #         f.writelines(out)
    # except FileNotFoundError:
    #     out = Compiler("./VSCode/Python/Compiler/Input.kog").Compile(True)
    #     with open("./VSCode/Python/Compiler/Input.s", "w") as f:
    #         f.writelines(out)
