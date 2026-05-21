# Sofia Moreno Lopez
# A01028251

from enum import Enum

class TokenType(Enum):
    ENDFILE      = '$'
    ERROR        = 'err'
    ELSE         = 'else'
    IF           = 'if'
    INT          = 'int'
    RETURN       = 'return'
    VOID         = 'void'
    WHILE        = 'while'
    ID           = 'ID'
    NUM          = 'NUM'
    COMENTARIO   = 'comentario'
    MENORQ       = '<'
    MENORIGUALQ  = '<='
    MAYORQ       = '>'
    MAYORIGUALQ  = '>='
    EQUIV        = '=='
    NEGACION     = '!='
    ASIGNAR      = '='
    SUMA         = '+'
    RESTA        = '-'
    MULT         = '*'
    DIV          = '/'
    PUNTOYCOMA   = ';'
    COMA         = ','
    PARABIERTO   = '('
    PARCERRADO   = ')'
    BRACKABIERTO = '['
    BRACKCERRADO = ']'
    CORABIERTO   = '{'
    CORCERRADO   = '}'

RESERVADO = {
    'else'  : TokenType.ELSE,
    'if'    : TokenType.IF,
    'int'   : TokenType.INT,
    'return': TokenType.RETURN,
    'void'  : TokenType.VOID,
    'while' : TokenType.WHILE,
}

class NodeKind(Enum):
    StmtK = 0
    ExpK  = 1
    DeclK = 2

class StmtKind(Enum):
    IfK       = 0
    WhileK    = 1
    ReturnK   = 2
    CompoundK = 3

class ExpKind(Enum):
    OpK     = 0   
    ConstK  = 1
    IdK     = 2
    AssignK = 3
    CallK   = 4

class DeclKind(Enum):
    VarK   = 0
    FunK   = 1
    ParamK = 2

class ExpType(Enum):
    Void    = 0
    Integer = 1
    Boolean = 2

MAXCHILDREN = 3

class TreeNode:
    def __init__(self):
        self.child   = [None] * MAXCHILDREN  
        self.sibling = None
        self.lineno  = 0

        self.nodekind = None

        self.stmt = None
        self.exp  = None
        self.decl = None

        self.op   = None
        self.val  = None
        self.name = None

        self.type = None

        self.typeSpec  = None
        self.isArray   = False
        self.arraySize = 0