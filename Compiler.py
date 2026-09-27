class Compiler():
    def __init__(self, src):
        self.source_file = src

    def get_full_source(self):
        with open(self.source_file, "r") as src:
            return [line for line in src]

    def Compile(self):
        lex = Lexer(self.source_file).Tokenize()
        print(f"///{lex}///")
        parser = Parser(lex).Parse()
        print(f"///{parser}///")
        semantic = SemanticAnalyzer(parser).Analyze()
        print(f"///{semantic}///")
        generator = CodeGenerator(semantic)
        return generator.Generate() + ["push 0\ncall exit\n"]


class Lexer():
    def __init__(self, src):
        self.source_file = src
        self.gen = self.__iter__()
        self.eol = False
        self.next_line()
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
            ">=": [TokenCategory.OPERATOR, TokenType.GREATER_EQUALS[1]]
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
            ")": [TokenCategory.OPERATOR, TokenType.P_CLOSE[1]]
        }

    # iterates over the whole file
    def __iter__(self):
        with open(self.source_file, "r") as src:
            for line in src:
                yield line.strip()

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
    def glance(self):
        return self.line[self.x] if self.line else ""


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
        if upper in TokenType.parse_for:
            isInTable = True
            upper = TokenType.parse_for[upper]
        token_return_type = getattr(TokenType, upper) if isInTable else token_return_type
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
        result = self.comparators.get(built) or self.operations.get(built)
        return Token(result[0], result[1], built)

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
            elif glanced.isidentifier():
                token = self.read_generic(TokenType.IDENTIFIER, "$isidentifier")
                if token.isType(TokenType.ELSE):
                    self.tokens.append(token)
                    self.tokens.append(Token(TokenType.EOL[0], TokenType.EOL[1], "EOL"))
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
            if glanced == ".":
                raise SyntaxError('Out of place symbol: "."')
            
            if token:
                self.tokens.append(token)
            if self.isEOL() and not self.isEOF() and not self.tokens[-2].isType(TokenType.EOL):
                self.tokens.append(Token(TokenType.EOL[0], TokenType.EOL[1], "EOL"))
        return self.tokens



class Token():
    def __init__(self, category, type, value=None):
        self.category = category
        self.type = type
        self.value = value

    def isChildOf(self, type: TokenType):
        parent = getattr(TokenType, self.type)[2]
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
        if self.isType(TokenType.NONE):
            return NONENode

    def __str__(self):
        return f"Token:[{self.category}, {self.type}, {self.value}]\n"
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

    TRUE = [TokenCategory.OBJECT, "TRUE", BOOL]
    FALSE = [TokenCategory.OBJECT, "FALSE", BOOL]

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
    BREAK = [TokenCategory.STATEMENT, "CONTINUE", STATEMENT]

    # FOR = [TokenCategory.STATEMENT, "FOR", STATEMENT]
    # EXEC = [TokenCategory.STATEMENT, "EXEC", STATEMENT]
    # FIN = [TokenCategory.STATEMENT, "FIN", STATEMENT]

    DEF = [TokenCategory.STATEMENT, "DEF", STATEMENT]
    RETURN = [TokenCategory.STATEMENT, "RETURN", STATEMENT]
    parse_for = {
        "DEF": "DEF", "RETURN": "RETURN",
        "INT": "INT", "FLOAT": "FLOAT", "BOOL": "BOOL", "NONE": "NONE",

        "IF": "IF", "THEN": "THEN", "END": "END", "AND": "AND", "OR": "OR", "ELSE": "ELSE",
        "WHILE": "WHILE", "CONTINUE": "CONTINUE", "BREAK": "BREAK",
        #"FOR": "FOR", "EXEC": "EXEC", "FIN": "FIN",
        "TRUE": "TRUE", "FALSE": "FALSE"
    }


class Parser():
    def __init__(self, token_source: list[Token]):
        self.token_source = token_source
        self.token_source_len = len(token_source)
        self.token_index = 0
        self.trees = []

    def token(self, in_advance=0):
        return self.token_source[self.token_index+in_advance] if self.token_index+in_advance < self.token_source_len else None

    def advance(self, how_many=1):
        self.token_index += how_many

    def parse_value(self):
        if self.token().isType(TokenType.INT):
            self.advance()
            return INTNode(self.token(-1).value)
        elif self.token().isType(TokenType.NONE):
            return NONENode()
        elif self.token().isType(TokenType.FLOAT):
            self.advance()
            return FLOATNode(self.token(-1).value)
        elif self.token().isType(TokenType.IDENTIFIER) and self.token(1) and self.token(1).isType(TokenType.P_OPEN):
            return self.parse_function_call()
        elif self.token().isType(TokenType.IDENTIFIER):
            self.advance()
            return IDENTIFIERNode(self.token(-1).value)
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
        while not self.token(-1).isChildOf(TokenType.SETTER):
            self.advance()
        return AssignmentNode(identifier, self.parse_comparison())

    def parse_function_call(self):
        args = []
        name = self.token().value
        self.advance(2)
        while self.token() and not self.token().isType(TokenType.P_CLOSE):
            args.append(self.parse_comparison())
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
        print(self.token())
        while self.token() and not self.token().isType(TokenType.P_CLOSE):
            print(self.token())
            args[self.token(1).value] = self.token()
            self.advance(2)
            print(self.token())
            while self.token().isType(TokenType.COMMA) or self.token(1).isType(TokenType.COMMA):
                self.advance()
            if self.token().isType(TokenType.P_CLOSE):
                break
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
        left = self.parse_comparison()
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
        print(self.token(-1), self.token(), self.token(1))
        return WHILENode(left, code)

    def parse_statement(self, nested=False):
        if self.token().isType(TokenType.IF):
            return self.parse_if(nested)
        if self.token().isType(TokenType.WHILE):
            return self.parse_while()
        if self.token().isType(TokenType.BREAK) or self.token().isType(TokenType.CONTINUE):
            self.advance()
            return LOOPMODNode(self.token(-1).value)
        setter = self.token(1) and self.token(1).isChildOf(TokenType.SETTER)
        if self.token().isType(TokenType.IDENTIFIER) and setter:
            return self.parse_assignment()
        if self.token() and self.token().isType(TokenType.DEF) and self.token(1).isChildOf(TokenType.TYPE_OBJECT):
            return self.parse_function_assignment()
        endParen = self.token(1) and self.token(1).isType(TokenType.P_OPEN)
        if self.token().isType(TokenType.IDENTIFIER) and endParen:
            return self.parse_function_call()
        isVal = self.token().isChildOf(TokenType.NUMBER) or self.token().isType(TokenType.IDENTIFIER) or self.token().isChildOf(TokenType.BOOL)
        if self.token().isChildOf(TokenType.REGULAR) or self.token().isType(TokenType.P_OPEN) or isVal:
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

class LOOPMODNode():
    def __init__(self, mod):
        self.mod = mod
    def __str__(self):
        return self.mod
    def __repr__(self):
        return self.__str__()

# node class telling the tree that its assigning a variable a value
class AssignmentNode():
    def __init__(self, identifier, value):
        self.identifier = identifier
        self.value = value
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
        return f"({self.operation}{self.value})"
    def __repr__(self):
        return self.__str__()

# node that represents a function call
class FunctionCall():
    def __init__(self, name, args):
        self.name = name
        self.args = args
    def __str__(self):
        return f"{self.name}({self.args})"
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
        self.op = None
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
        self.op = None
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
            "exit": None,
            "strlen": INTNode,
            "intput": INTNode,
            "strint": INTNode
        }
        plusRules = {
            INTNode: {INTNode: INTNode, FLOATNode: FLOATNode, BOOLNode: INTNode, UnaryNode: INTNode},
            FLOATNode: {INTNode: FLOATNode, FLOATNode: FLOATNode, BOOLNode: FLOATNode, UnaryNode: FLOATNode},
            BOOLNode: {INTNode: INTNode, FLOATNode: FLOATNode, BOOLNode: INTNode, UnaryNode: INTNode},
            UnaryNode: {INTNode: INTNode, FLOATNode: FLOATNode, BOOLNode: INTNode, UnaryNode: UnaryNode}
        }
        boolRules = {
            INTNode: {INTNode: BOOLNode, FLOATNode: BOOLNode, BOOLNode: BOOLNode, UnaryNode: BOOLNode},
            FLOATNode: {INTNode: BOOLNode, FLOATNode: BOOLNode, BOOLNode: BOOLNode, UnaryNode: BOOLNode},
            BOOLNode: {INTNode: BOOLNode, FLOATNode: BOOLNode, BOOLNode: BOOLNode, UnaryNode: BOOLNode},
            UnaryNode: {INTNode: BOOLNode, FLOATNode: BOOLNode, BOOLNode: BOOLNode, UnaryNode: BOOLNode}
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
                INTNode: {INTNode: INTNode, FLOATNode: INTNode, BOOLNode: INTNode, UnaryNode: INTNode},
                FLOATNode: {INTNode: INTNode, FLOATNode: INTNode, BOOLNode: INTNode, UnaryNode: INTNode},
                BOOLNode: {INTNode: INTNode, FLOATNode: INTNode, BOOLNode: INTNode, UnaryNode: INTNode},
                UnaryNode: {INTNode: INTNode, FLOATNode: INTNode, BOOLNode: INTNode, UnaryNode: INTNode}
            },

            "==": boolRules,
            "!=": boolRules,
            "!": boolRules,
            "<=": boolRules,
            ">=": boolRules,
            "<": boolRules,
            ">": boolRules
        }

    def Analyze(self):
        newTrees = []
        for tree in self.trees:
            analyzed = self.treeAnalyze(tree)
            if type(analyzed) is tuple:
                newTrees.append(analyzed[0])
                continue
            newTrees.append(analyzed)
        return ProgramNode(newTrees)


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
        arg1 = self.isNode(tree) and not self.isUnary(tree) and not type(tree) is FunctionCall and not type(tree) is IFNode
        return arg1 and not type(tree) is FunctionAssign and not type(tree) is FunctionReturn

    def isUnary(self, tree):
        return type(tree) is UnaryNode

    def isConst(self, tree):
        return self.isEndNode(tree) and tree.isChildOf(TokenType.CONSTANT)

    def checkIsValid(self, type1, operation, type2):
        try:
            output = self.operation_outputs[operation][type1][type2]
            return output
        except:
            raise TypeError(f"Cannot combine classes: {type1}, {type2}")

    def treeAnalyze(self, tree):
        if type(tree) is FunctionAssign:
            self.vars[tree.name] = tree.retType.getAsNode()
            for var, varType in tree.args.items():
                self.vars[var] = varType.getAsNode()
            code = SemanticAnalyzer(ProgramNode(tree.code), self.vars).Analyze().branches
            return FunctionAssign(tree.name, tree.args, tree.retType, code), tree.retType.getAsNode()
        if type(tree) is FunctionCall:
            return tree, self.vars.get(tree.name, self.baked_functions.get(tree.name))
        if type(tree) is IFNode:
            code = SemanticAnalyzer(ProgramNode(tree.code), self.vars).Analyze().branches
            return IFNode(tree.conditions, code, tree.codeelse)
        if type(tree) is WHILENode:
            code = SemanticAnalyzer(ProgramNode(tree.code), self.vars).Analyze().branches
            return WHILENode(tree.conditions, code)
        if type(tree) is LOOPMODNode:
            return tree, None
        if type(tree) is AssignmentNode:        # if assignment then analyze right instead and return it
            analyzed, varType = self.treeAnalyze(tree.value)
            self.vars[tree.identifier] = varType
            return AssignmentNode(tree.identifier, analyzed)
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
            if not isOperation and left.isChildOf(TokenType.CONSTANT) and right.isChildOf(TokenType.CONSTANT):
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

class CodeGenerator():
    def __init__(self, analyzedTokens: ProgramNode, isFunc=False):
        self.tokens = analyzedTokens.branches
        self.varAmt = 0
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
        
        self.data = []                                                  # GLOBAL VARIABLES ONLY
        self.text = []                                                  # holds functions (only used by first created CodeGenerator instance)
        self.main = []                                                  # holds main, also where sub generators store their function data

        self.vars = {}                                                  # HOLDS ALL VARIABLE LOCATIONS AS STRINGS
        #["rax", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r10", "r11"]

    def Generate(self, ret=True, prevVars={}, args=[]):
        self.args = args
        if prevVars or not ret:
            self.vars = prevVars
        else:
            self.text = [
                "_abs:\n",
                "  mov rax, [rbp+24]\n",
                "  cmp rax, 0\n",
                "  jge 0f\n",
                "  neg rax\n",
                "  0:\n",
                "  ret\n",
                "\n",
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
                "\n",
                "strlen:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  push rcx\n",
                "  mov rbp, rsp\n",
                "  mov rcx, [rbp+32]\n",
                "  xor rax, rax\n",
                "  0:\n",
                "    cmp byte ptr [rcx], 0\n",
                "    je 1f\n",
                "    inc rax\n",
                "    inc rcx\n",
                "    jmp 0b\n",
                "  1:\n",
                "    pop rcx\n",
                "    pop rbp\n",
                "    pop rsp\n",
                "    ret\n",
                "\n",
                "intstr:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  mov rbp, rsp\n",
                "  sub rsp, 16\n",
                "  mov qword ptr [rbp-8], 0\n",
                "  mov qword ptr [rbp-8], 0\n",
                "  mov rax, [rbp+24]\n",
                "  mov qword ptr [rbp-8], 0\n",
                "  mov rcx, rbp\n",
                "  sub rcx, 1\n",
                "  mov rdx, 1\n",
                "  mov qword ptr [rbp-16], 10\n",
                "  0:\n",
                "    cmp rax, 0\n",
                "    je 1f\n",
                "    xor rdx, rdx\n",
                "    div qword ptr [rbp-16]\n",
                "    add rdx, 48\n",
                "    mov [rcx], dl\n",
                "    dec rcx\n",
                "    jmp 0b\n",
                "  1:\n",
                "    mov qword ptr [rbp-16], 0x100\n",
                "    mov rcx, rbp\n",
                "    sub rcx, 8\n",
                "    cmp qword ptr [rcx], 0\n",
                "    jne 3f\n",
                "    mov rax, 0x30\n",
                "    jmp 4f\n",
                "  3:\n",
                "    cmp byte ptr [rcx], 0\n",
                "    jne 4f\n",
                "    xor rdx, rdx\n",
                "    mov rax, [rcx]\n",
                "    div qword ptr [rbp-16]\n",
                "    mov qword ptr [rbp-8], rax\n",
                "    jmp 3b\n",
                "  4:\n",
                "    add rsp, 16\n",
                "    pop rbp\n",
                "    pop rsp\n",
                "    ret\n",
                "print:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  mov rbp, rsp\n",
                "  mov r11, [rbp+24]\n",
                "  mov r9, rbp\n",
                "  add r9, 32\n",
                "  imul r11, 8\n",
                "  mov rax, 1\n",
                "  mov rdi, 1\n",
                "  mov rsi, r9\n",
                "  mov rdx, r11\n",
                "  syscall\n",
                "  pop rbp\n",
                "  pop rsp\n",
                "  ret\n",
                "println:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  mov rbp, rsp\n",
                "  sub rsp, 8\n",
                "  mov qword ptr [rbp-8], 0\n",
                "  mov r11, [rbp+24]\n",
                "  mov r9, rbp\n",
                "  add r9, 32\n",
                "  imul r11, 8\n",
                "  mov rax, 1\n",
                "  mov rdi, 1\n",
                "  mov rsi, r9\n",
                "  mov rdx, r11\n",
                "  syscall\n",
                "  mov rax, 1\n",
                "  mov rdi, 1\n",
                "  mov qword ptr [rbp-8], 0x0a\n",
                "  mov rsi, rsp\n",
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
                "strint:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  mov rbp, rsp\n",
                "  mov rax, rbp\n",
                "  add rax, 24\n",
                "  xor r8, r8\n",
                "  xor r9, r9\n",
                "  jmp 0f\n",
                "  2:\n",
                "    mov rax, 60\n",
                "    mov rdi, 127\n",
                "    syscall\n",
                "  0:\n",
                "    cmp byte ptr [rax], 0\n",
                "    je 1f\n",
                "    sub byte ptr [rax], 48\n",
                "    cmp byte ptr [rax], 9\n",
                "    jbe 3f\n",
                "    cmp byte ptr [rax], 0xda\n",
                "    jne 3f\n",
                "    sub byte ptr [rax], 0xda\n",
                "    jmp 1f\n",
                "    3:\n",
                "    imul r8, 10\n",
                "    mov r9b, byte ptr [rax]\n",
                "    add r8, r9\n",
                "    inc rax\n",
                "    jmp 0b\n",
                "  1:\n",
                "    mov rax, r8\n",
                "    pop rbp\n",
                "    pop rsp\n",
                "    ret\n",
                "intput:\n",
                "  push rsp\n",
                "  push rbp\n",
                "  mov rbp, rsp\n",
                "  sub rsp, 8\n",
                "  mov qword ptr [rbp-8], 0\n",
                "  xor rax, rax\n",
                "  xor rdi, rdi\n",
                "  mov rsi, rsp\n",
                "  mov rdx, [rbp+24]\n",
                "  syscall\n",
                "  call strint\n",
                "  add rsp, 8\n",
                "  pop rbp\n",
                "  pop rsp\n",
                "  ret\n"
            ]
        total_vars = []
        varIsFunc = {}
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
            self.addLine(f"sub rsp, {local_var_count*8}")
            for v in range(1, local_var_count+1):
                v *= 8
                self.addLine(f"mov qword ptr [rbp-{v}], 0")
            self.addLine("")

        for tree in self.tokens:
            self.addLine("")
            self.traverse_tree(tree, True, args)
        if len(args) == 0:
            self.addLine("99:")
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
        if not ret:
            #self.addLine("ret")
            return self.text + self.main
        if "main" in args:
            return self.main
        return [".intel_syntax noprefix\n", ".global _start\n", ".data\n"] + self.data + [".text\n"] + self.text + ["_start:\n"] + self.main

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
                    self.addVar(node.identifier)
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
        else:
            return 0

    def addVar(self, var, regOrVal=0):
        if not (self.vars.get(var, None) is None):
            return
        if self.isFunc:
            self.varAmt += 1
            self.vars[var] = f"[rbp-{self.varAmt*8}]"
        else:
            self.vars[var] = f"[{var}]"
        if regOrVal != 0:
            self.setVarAsm(var, regOrVal)

    def addFunc(self, funcNode: FunctionAssign):
        local = {}                                                                      # all locals in function
        count = len(funcNode.args)                                                      # num of all locals in function
        for var in funcNode.args:
            local[var] = f"[rbp+{16+8*count}]"                                          # sets all local memory locations
            count -= 1                                                                  # updates local count
        local["%parent"] = self.vars
        reference = local
        while not reference.get("%parent", None) is None:                               # if parent then continue into loop
            reference = reference["%parent"]                                            # store reference to parent
            for key in reference:                                                       # loop through reference to change locals without discarding info
                if len(reference[key]) >= 7 and key != "%parent" and reference[key][1:5] == "rbp+":
                    reference[key] = reference[key][0] + "r10+" + reference[key][5:]    # replace if not in current scope
        gen = CodeGenerator(ProgramNode(funcNode.code), True).Generate(False, local)    # gets function body code
        self.addText(f"{funcNode.name}:")                                               # funcname:
        self.text += gen                                                                #   body

    
    def loadVarAsm(self, var, reg):
        self.addLine(f"mov {reg}, {self.getVarLoc(var)}")
    
    def setVarAsm(self, var, regOrVal):
        self.addLine(f"mov {self.getVarLoc(var)}, {regOrVal}")

    def addLine(self, txt: str):
        self.main.append(txt + "\n")
    def addText(self, txt: str):
        self.text.append(txt + "\n")
    def addData(self, txt: str):
        self.data.append(txt + ": .quad 0\n")

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
            self.addLine("xor rdx, rdx")
            self.addLine(f"mov rax, {valOrReg1}")
            self.addLine(f"mov rcx, {valOrReg2}")
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

    def traverse_tree(self, tree, first=False, args: list=[]):
        if type(tree) is FunctionCall:
            for arg in tree.args if not (tree.name.lower() == "print" or tree.name.lower() == "println") else tree.args[::-1]:
                self.traverse_tree(arg, False, ["print"] if tree.name.lower() == "print" or tree.name.lower() == "println" else [])
                if tree.name.lower() == "print" or tree.name.lower() == "println":
                    self.addLine("call intstr")
                    self.addLine("add rsp, 8")
                    self.addLine("push rax")
            if tree.name.lower() == "print" or tree.name.lower() == "println":
                self.addLine(f"push {len(tree.args)}")
            elif len(tree.args) == 0 and tree.name.lower() == "exit":
                self.addLine("push 0")
                self.addLine("call exit")
                return
            self.addLine(f"call {tree.name}")
            self.addLine(f"add rsp, {len(tree.args)*8 + (8 if tree.name.lower() == "print" or tree.name.lower() == "println" else 0)}")
            if not first:
                self.addLine("push rax")
            return
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
            return

        if type(tree) is CONDMODNode:
            self.traverse_tree(tree.left)
            self.traverse_tree(tree.right)
            self.addLine("pop rdx")
            self.addLine("pop rcx")
            self.insertOperation("rcx", tree.mod, "rdx")
            self.addLine("push rcx")
            return

        if type(tree) is IFNode:            # must use unique letter names for each if statement, or nested functions will get confused or reuse already used names
            startLabel = next(getIfStartLabel)
            elseLabel = next(getIfElseLabel)
            endLabel = next(getIfEndLabel)
            self.traverse_tree(tree.conditions, False)
            # always a CONDMOD node, traverse it and insert cmp statements at and/or ops
            
            self.addLine("pop rax")
            self.addLine("cmp rax, 1")
            self.addLine(f"jne {elseLabel}")

            self.addLine(f"{startLabel}:")
            self.main += CodeGenerator(ProgramNode(tree.code), False).Generate(False, self.vars, ["main"])
            self.addLine(f"jmp {endLabel}")
            self.addLine(f"{elseLabel}:")
            if len(tree.codeelse) > 0:
                self.main += CodeGenerator(ProgramNode(tree.codeelse), False).Generate(False, self.vars, ["main"])
            self.addLine(f"{endLabel}:")
            return

        if type(tree) is WHILENode:
            startLabel = next(getWhileStartLabel)
            endLabel = next(getWhileEndLabel)
            contLabel = next(getWhileContinueLabel)
            brkLabel = next(getWhileBreakLabel)
            self.addLine(f"{startLabel}:")

            self.traverse_tree(tree.conditions, False)
            # always a CONDMOD node, traverse it and insert cmp statements at and/or ops
            self.addLine("pop rax")
            self.addLine("cmp rax, 1")
            self.addLine(f"jne {endLabel}")
            self.main += CodeGenerator(ProgramNode(tree.code), False).Generate(False, self.vars, ["main", "continueLabel", contLabel, "breakLabel", brkLabel])
            self.addLine(f"{contLabel}:")
            self.addLine(f"jmp {startLabel}")
            self.addLine(f"{brkLabel}:")
            self.addLine(f"{endLabel}:")
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
            self.traverse_tree(tree.value)
            self.addLine(f"pop rax")
            self.addLine("jmp 99f")
            return
        
        if type(tree) is UnaryNode:
            self.traverse_tree(tree.value)
            self.addLine("pop rcx")
            self.insertUnary("rcx", tree.operation)
            self.addLine("push rcx")
            return

        if type(tree) is AssignmentNode:
            self.addVar(tree.identifier)
            self.traverse_tree(tree.value)
            if first:
                self.addLine("pop rax")
            self.setVarAsm(tree.identifier, "rax")
            return

        if self.isNode(tree):
            if type(tree) is INTNode:
                self.addLine(f"push {tree.value}")
                return
            if type(tree) is BOOLNode:
                self.addLine(f"push {1 if tree.value == True else -1}")
                return
            if type(tree) is IDENTIFIERNode:
                self.addLine(f"push {self.getVarLoc(tree.value)}")
                return
            if type(tree) is NONENode:
                self.addLine("push 0")
                return

        raise SyntaxError(f"Forgot to add {tree} here")




if __name__ == "__main__":
    out = Compiler("./Input.kog").Compile()
    with open("./Output.s", "w") as output:
        output.writelines(out)
