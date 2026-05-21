# Sofia Moreno Lopez
# A01028251

from globalTypes import *

#tabla de transiciones 
tabla = [
  [  1,   2,  21,  22,  31,   3,   6,   7,   9,   8,  23,  24,  25,  26,  27,  28,  29,  30,   0,  32],
  [  1,   1,  10,  10,  10,  10,  10,  10,  10,  10,  10,  10,  10,  10,  10,  10,  10,  10,  10,  32],
  [ 32,   2,  11,  11,  11,  11,  11,  11,  11,  11,  11,  11,  11,  11,  11,  11,  11,  11,  11,  32],
  [ 13,  13,  13,  13,   4,  13,  13,  13,  13,  13,  13,  13,  13,  13,  13,  13,  13,  13,  13,  32],
  [  4,   4,   4,   4,   5,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4],
  [  4,   4,   4,   4,   5,  12,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4],
  [ 14,  14,  14,  14,  14,  14,  14,  14,  15,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  32],
  [ 16,  16,  16,  16,  16,  16,  16,  16,  17,  16,  16,  16,  16,  16,  16,  16,  16,  16,  16,  32],
  [ 32,  32,  32,  32,  32,  32,  32,  32,  18,  32,  32,  32,  32,  32,  32,  32,  32,  32,  32,  32],
  [ 19,  19,  19,  19,  19,  19,  19,  19,  20,  19,  19,  19,  19,  19,  19,  19,  19,  19,  19,  32],
]

TOKEN_MAP = {
    10: None, # ID / palabra reservada
    11: TokenType.NUM,           # NUM
    12: TokenType.COMENTARIO,    # COMENTARIO
    13: TokenType.DIV,           # DIVISION
    14: TokenType.MENORQ,        # MENOR QUE
    15: TokenType.MENORIGUALQ,   # MENOR O IGUAL QUE
    16: TokenType.MAYORQ,        # MAYOR QUE
    17: TokenType.MAYORIGUALQ,   # MAYOR O IGUAL QUE
    18: TokenType.NEGACION,      # DIFERENTE DE
    19: TokenType.ASIGNAR,       # ASIGNACIÓN
    20: TokenType.EQUIV,         # EQUIVALENCIA (==)
    21: TokenType.SUMA,          # SUMA
    22: TokenType.RESTA,         # RESTA
    23: TokenType.PUNTOYCOMA,    # PUNTO Y COMA
    24: TokenType.COMA,          # COMA
    25: TokenType.PARABIERTO,    # PARENTESIS ABIERTO
    26: TokenType.PARCERRADO,    # PARENTESIS CERRADO
    27: TokenType.BRACKABIERTO,  # CORCHETE ABIERTO
    28: TokenType.BRACKCERRADO,  # CORCHETE CERRADO
    29: TokenType.CORABIERTO,    # LLAVE ABIERTA
    30: TokenType.CORCERRADO,    # LLAVE CERRADA
    31: TokenType.MULT,          # MULTIPLICACION
    32: TokenType.ERROR,         # ERROR
}

_ERROR_CONTEXT = {
    0: "un carácter no reconocido",
    1: "un identificador o palabra reservada",
    2: "un número",
    3: "el operador '/' o un comentario",
    6: "el operador '<' o '<='",                
    7: "el operador '>' o '>='",
    8: "el operador '==' o '='",
    9: "el operador '!='",
}

programa = ''
posicion = 0
progLong = 0
lineno   = 1

def globalesLexer(prog, pos, long):
    global programa, posicion, progLong, lineno
    programa = prog
    posicion = pos
    progLong = long
    lineno   = 1

def _col(c):
    if c.isalpha():                 return 0
    if c.isdigit():                 return 1
    if c == '+':                    return 2
    if c == '-':                    return 3
    if c == '*':                    return 4
    if c == '/':                    return 5
    if c == '<':                    return 6
    if c == '>':                    return 7
    if c == '=':                    return 8
    if c == '!':                    return 9
    if c == ';':                    return 10
    if c == ',':                    return 11
    if c == '(':                    return 12
    if c == ')':                    return 13
    if c == '[':                    return 14
    if c == ']':                    return 15
    if c == '{':                    return 16
    if c == '}':                    return 17
    if c in (' ', '\t', '\n', '$'): return 18
    return 19

def _reportarError(pos_err, lex, estado_previo=None):
    ini = pos_err
    while ini > 0 and programa[ini - 1] != '\n':
        ini -= 1
    fin = pos_err
    while fin < progLong and programa[fin] != '\n':
        fin += 1
    col_rel = pos_err - ini

    contexto = _ERROR_CONTEXT.get(estado_previo, "un token desconocido")
    print(f"\nLínea {lineno}: Error al intentar formar {contexto}: '{lex}'")
    print(f"  {programa[ini:fin]}")
    print(f"  {' ' * col_rel}^")

def getToken(imprime=True):
    global posicion, lineno

    estado         = 0
    estado_previo  = 0
    lexema         = ''
    pos_inicio     = posicion

    while programa[posicion] != '$' or estado != 0:

        c   = programa[posicion]
        col = _col(c)

        estado_previo = estado # se acuerda del estado antes de la transicion por si se necesita para reportar un error
        estado        = tabla[estado][col]

        if estado != 0:
            lexema += c

        if c == '\n':
            lineno += 1

        if estado in TOKEN_MAP:
            tokenType = TOKEN_MAP[estado]

            if estado == 10:    # ID / palabra reservada
                lexema    = lexema[:-1]
                posicion -= 1
                if c == '\n': lineno -= 1
            elif estado == 11:  # NUM
                lexema    = lexema[:-1]
                posicion -= 1
                if c == '\n': lineno -= 1
            elif estado == 13:  # DIV
                lexema    = lexema[:-1]
                posicion -= 1
                if c == '\n': lineno -= 1
            elif estado == 14:  # MENOR QUE
                lexema    = lexema[:-1]
                posicion -= 1
                if c == '\n': lineno -= 1
            elif estado == 16:  # MAYOR QUE
                lexema    = lexema[:-1]
                posicion -= 1
                if c == '\n': lineno -= 1
            elif estado == 19:  # ASIGNAR
                lexema    = lexema[:-1]
                posicion -= 1
                if c == '\n': lineno -= 1

            if tokenType is None:
                tokenType = RESERVADO.get(lexema, TokenType.ID)

            if tokenType == TokenType.ERROR:
                lex_err = lexema if lexema else c
                _reportarError(pos_inicio, lex_err, estado_previo)
                if imprime:
                    print(f"token of type ERROR = {lex_err}")
                posicion += 1
                return TokenType.ERROR, lex_err, lineno

            if imprime:
                print(f"token of type {tokenType.name} = {lexema}")
            lex_ret   = lexema
            posicion += 1
            return tokenType, lex_ret, lineno

        if estado == 0:
            pos_inicio = posicion + 1

        posicion += 1

    if imprime:
        print(f"token of type ENDFILE = ")
    return TokenType.ENDFILE, '', lineno