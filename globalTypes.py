from enum import Enum

class TokenType(Enum):
    ENDFILE = '$'
    ERROR   = 'err'
    ELSE   = 'else'
    IF     = 'if'
    INT    = 'int'
    RETURN = 'return'
    VOID   = 'void'
    WHILE  = 'while'
    ID      = 'ID'
    NUM     = 'NUM'
    COMENTARIO = 'comentario'
    MENORQ  = '<'
    MENORIGUALQ = '<='
    MAYORQ  = '>'
    MAYORIGUALQ = '>='
    EQUIV  = '=='
    NEGACION = '!='
    ASIGNAR = '='
    SUMA   = '+'
    RESTA  = '-'
    MULT  = '*'
    DIV   = '/'
    PUNTOYCOMA     = ';'
    COMA    = ','
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