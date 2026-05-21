# Sofia Moreno Lopez
# A01028251

from globalTypes import *
from lexer import *

token        = None
lexema  = None
Error        = False
imprimeLexer = False

# para parar el modo panico:
SYNC_DECL   = {TokenType.INT, TokenType.VOID, TokenType.ENDFILE}
SYNC_STMT   = {TokenType.PUNTOYCOMA, TokenType.CORCERRADO, TokenType.ENDFILE}
SYNC_FACTOR = {TokenType.PUNTOYCOMA, TokenType.PARCERRADO,
               TokenType.BRACKCERRADO, TokenType.COMA, TokenType.ENDFILE}

# Conjunto de tokens con los que puede empezar una sentencia
_FIRST_STMT = {
    TokenType.PUNTOYCOMA,
    TokenType.PARABIERTO,   
    TokenType.ID,           
    TokenType.NUM,          
    TokenType.CORABIERTO,   
    TokenType.IF,           
    TokenType.WHILE,        
    TokenType.RETURN,       
}

#relacionales 
_RELOPS = {TokenType.MENORQ,      TokenType.MENORIGUALQ,
           TokenType.MAYORQ,      TokenType.MAYORIGUALQ,
           TokenType.EQUIV,       TokenType.NEGACION}


def _skipComments():
    global token, lexema, lineno
    while token == TokenType.COMENTARIO:
        token, lexema, lineno = getToken(imprimeLexer)

def syntaxError(message):
    global Error
    flecha = " " * (len(lexema) // 2) + "^"
    print(f"\nLinea {lineno}: Error sintactico - {message}")
    print(f"'{lexema}'")
    print(f"{flecha}")
    Error = True

def match(expected):
    global token, lexema, lineno
    if token == expected:
        token, lexema, lineno = getToken(imprimeLexer)
        _skipComments()
    else:
        syntaxError(
            f"se esperaba '{expected.name}' "
            f"pero se encontro '{token.name}' -> '{lexema}'"
        )

def panic(syncSet):
    global token, lexema, lineno
    while token not in syncSet and token != TokenType.ENDFILE:
        token, lexema, lineno = getToken(imprimeLexer)

# nodo sentencia
def newStmtNode(kind):
    t          = TreeNode()
    t.nodekind = NodeKind.StmtK
    t.stmt     = kind
    t.lineno   = lineno
    return t

# nodo expresion
def newExpNode(kind):
    t          = TreeNode()
    t.nodekind = NodeKind.ExpK
    t.exp      = kind
    t.lineno   = lineno
    t.type     = ExpType.Void
    return t

#nodo declaracion
def newDeclNode(kind):
    t          = TreeNode()
    t.nodekind = NodeKind.DeclK
    t.decl     = kind
    t.lineno   = lineno
    return t

#reglas segun el docs de la clase
def program():
    """program -> declaration-list"""
    return declaration_list()

def declaration_list():
    """declaration-list -> declaration { declaration }"""
    t = None
    p = None
    while token != TokenType.ENDFILE:
        if token not in {TokenType.INT, TokenType.VOID}:
            syntaxError(
                f"declaracion invalida en ambito global: se encontro '{lexema}'"
            )
            panic(SYNC_DECL)
            continue
        q = declaration()
        if q is not None:
            if t is None:
                t = p = q
            else:
                p.sibling = q
                p = q
    return t

def declaration():
    """declaration -> var-declaration | fun-declaration"""
    global token, lexema, lineno

    if token not in {TokenType.INT, TokenType.VOID}:
        syntaxError(f"se esperaba tipo (int/void), se encontro '{lexema}'")
        panic(SYNC_DECL)
        return None

    typeSpec = token
    match(token)

    name     = lexema
    nameLine = lineno
    if token != TokenType.ID:
        syntaxError(f"se esperaba identificador, se encontro '{lexema}'")
        panic(SYNC_DECL)
        return None
    match(TokenType.ID)

    if token == TokenType.PARABIERTO:
        return fun_declaration(typeSpec, name, nameLine)
    else:
        return var_declaration(typeSpec, name, nameLine)

def var_declaration(typeSpec, name, nameLine):
    """var-declaration -> type-specifier ID ;
                        | type-specifier ID [ NUM ] ;"""
    t          = newDeclNode(DeclKind.VarK)
    t.name     = name
    t.lineno   = nameLine
    t.typeSpec = typeSpec
    t.isArray  = False

    if token == TokenType.BRACKABIERTO:
        match(TokenType.BRACKABIERTO)
        t.isArray = True
        if token == TokenType.NUM:
            t.arraySize = int(lexema)
        match(TokenType.NUM)
        match(TokenType.BRACKCERRADO)

    match(TokenType.PUNTOYCOMA)
    return t

def fun_declaration(typeSpec, name, nameLine):
    """fun-declaration -> type-specifier ID ( params ) compound-stmt"""
    t          = newDeclNode(DeclKind.FunK)
    t.name     = name
    t.lineno   = nameLine
    t.typeSpec = typeSpec

    match(TokenType.PARABIERTO)
    t.child[0] = params()
    match(TokenType.PARCERRADO)
    t.child[1] = compound_stmt()
    return t

def params():
    """params -> param-list | void"""
    if token == TokenType.VOID:
        match(TokenType.VOID)
        if token == TokenType.PARCERRADO:
            return None
        else:
            t          = newDeclNode(DeclKind.ParamK)
            t.typeSpec = TokenType.VOID
            t.name     = lexema
            t.isArray  = False
            match(TokenType.ID)
            if token == TokenType.BRACKABIERTO:     # param de arreglo
                match(TokenType.BRACKABIERTO)
                match(TokenType.BRACKCERRADO)
                t.isArray = True
            p = t
            while token == TokenType.COMA:
                match(TokenType.COMA)
                q = param()
                if q is not None:
                    p.sibling = q
                    p = q
            return t
    else:
        return param_list()

def param_list():
    """param-list -> param { , param }"""
    t = param()
    p = t
    while token == TokenType.COMA:
        match(TokenType.COMA)
        q = param()
        if q is not None:
            if t is None:
                t = p = q
            else:
                p.sibling = q
                p = q
    return t

def param():
    """param -> type-specifier ID
              | type-specifier ID [ ]"""
    if token not in {TokenType.INT, TokenType.VOID}:
        syntaxError(f"se esperaba tipo en parametro, se encontro '{lexema}'")
        panic({TokenType.COMA, TokenType.PARCERRADO, TokenType.ENDFILE})
        return None

    t          = newDeclNode(DeclKind.ParamK)
    t.typeSpec = token
    match(token)

    t.name    = lexema
    t.isArray = False
    match(TokenType.ID)

    if token == TokenType.BRACKABIERTO:
        match(TokenType.BRACKABIERTO)
        match(TokenType.BRACKCERRADO)
        t.isArray = True

    return t

def compound_stmt():
    """compound-stmt -> { local-declarations statement-list }"""
    t = newStmtNode(StmtKind.CompoundK)
    match(TokenType.CORABIERTO)
    t.child[0] = local_declarations()
    t.child[1] = statement_list()
    match(TokenType.CORCERRADO)
    return t

def local_declarations():
    """local-declarations -> { var-declaration }"""
    t = None
    p = None
    while token in {TokenType.INT, TokenType.VOID}:
        typeSpec = token
        match(token)
        name     = lexema
        nameLine = lineno
        if token != TokenType.ID:
            syntaxError(
                f"se esperaba ID en declaracion local, se encontro '{lexema}'"
            )
            panic(SYNC_DECL | {TokenType.CORCERRADO})
            continue
        match(TokenType.ID)
        q = var_declaration(typeSpec, name, nameLine)
        if q is not None:
            if t is None:
                t = p = q
            else:
                p.sibling = q
                p = q
    return t

def statement_list():
    """statement-list -> { statement }"""
    t = None
    p = None
    while token in _FIRST_STMT:
        q = statement()
        if q is not None:
            if t is None:
                t = p = q
            else:
                p.sibling = q
                p = q
    return t

def statement():
    """statement -> expression-stmt | compound-stmt
                  | selection-stmt  | iteration-stmt
                  | return-stmt"""
    if   token == TokenType.CORABIERTO: return compound_stmt()
    elif token == TokenType.IF:         return selection_stmt()
    elif token == TokenType.WHILE:      return iteration_stmt()
    elif token == TokenType.RETURN:     return return_stmt()
    else:                               return expression_stmt()

def expression_stmt():
    """expression-stmt -> expression ; | ;"""
    t = None
    if token != TokenType.PUNTOYCOMA:
        t = expression()
    match(TokenType.PUNTOYCOMA)
    return t

def selection_stmt():
    """selection-stmt -> if ( expression ) statement
                       | if ( expression ) statement else statement"""
    t = newStmtNode(StmtKind.IfK)
    match(TokenType.IF)
    match(TokenType.PARABIERTO)
    t.child[0] = expression()       # condicion
    match(TokenType.PARCERRADO)
    t.child[1] = statement()        # rama then
    if token == TokenType.ELSE:
        match(TokenType.ELSE)
        t.child[2] = statement()    # rama else (opcional)
    return t

def iteration_stmt():
    """iteration-stmt -> while ( expression ) statement"""
    t = newStmtNode(StmtKind.WhileK)
    match(TokenType.WHILE)
    match(TokenType.PARABIERTO)
    t.child[0] = expression()       # condicion
    match(TokenType.PARCERRADO)
    t.child[1] = statement()        # cuerpo
    return t

def return_stmt():
    """return-stmt -> return ; | return expression ;"""
    t = newStmtNode(StmtKind.ReturnK)
    match(TokenType.RETURN)
    if token != TokenType.PUNTOYCOMA:
        t.child[0] = expression()
    match(TokenType.PUNTOYCOMA)
    return t

def expression():
    """expression -> var = expression | simple-expression"""
    global token, lexema, lineno

    if token == TokenType.ID:
        savedName = lexema
        savedLine = lineno
        match(TokenType.ID)

        if token == TokenType.ASIGNAR:
            t          = newExpNode(ExpKind.AssignK)
            t.name     = savedName
            t.lineno   = savedLine
            match(TokenType.ASIGNAR)
            t.child[0] = expression()
            return t

        elif token == TokenType.BRACKABIERTO:
            match(TokenType.BRACKABIERTO)
            idxExpr = expression()
            match(TokenType.BRACKCERRADO)

            if token == TokenType.ASIGNAR:
                t          = newExpNode(ExpKind.AssignK)
                t.name     = savedName
                t.lineno   = savedLine
                t.child[1] = idxExpr
                match(TokenType.ASIGNAR)
                t.child[0] = expression()
                return t
            else:
                varNode          = newExpNode(ExpKind.IdK)
                varNode.name     = savedName
                varNode.lineno   = savedLine
                varNode.child[0] = idxExpr
                return _finish_simple_exp(
                    _finish_additive_exp(
                        _finish_term(varNode)))

        elif token == TokenType.PARABIERTO:
            callNode = _build_call(savedName, savedLine)
            return _finish_simple_exp(
                _finish_additive_exp(
                    _finish_term(callNode)))

        else:
            varNode        = newExpNode(ExpKind.IdK)
            varNode.name   = savedName
            varNode.lineno = savedLine
            return _finish_simple_exp(
                _finish_additive_exp(
                    _finish_term(varNode)))
    else:
        return simple_expression()


#helpers

def _finish_term(leftFactor):
    """Continua term -> factor { mulop factor } con factor izquierdo dado."""
    t = leftFactor
    while token in {TokenType.MULT, TokenType.DIV}:
        p          = newExpNode(ExpKind.OpK)
        p.child[0] = t
        p.op       = token
        t          = p
        match(token)
        t.child[1] = factor()
    return t

def _finish_additive_exp(leftTerm):
    """Continua additive-expression -> term { addop term } con term dado."""
    t = leftTerm
    while token in {TokenType.SUMA, TokenType.RESTA}:
        p          = newExpNode(ExpKind.OpK)
        p.child[0] = t
        p.op       = token
        t          = p
        match(token)
        t.child[1] = term()
    return t

def _finish_simple_exp(leftAdd):
    """Continua simple-expression con additive-expression izquierda dada."""
    t = leftAdd
    if token in _RELOPS:
        p          = newExpNode(ExpKind.OpK)
        p.child[0] = t
        p.op       = token
        t          = p
        match(token)
        t.child[1] = additive_expression()
    return t

#regla 27: call -> ID ( args )
def _build_call(name, nameLine):
    """para regla 27"""
    t          = newExpNode(ExpKind.CallK)
    t.name     = name
    t.lineno   = nameLine
    match(TokenType.PARABIERTO)
    t.child[0] = args()
    match(TokenType.PARCERRADO)
    return t


def var():
    """var -> ID | ID [ expression ]"""
    global token, lexema, lineno
    t        = newExpNode(ExpKind.IdK)
    t.name   = lexema
    t.lineno = lineno
    match(TokenType.ID)
    if token == TokenType.BRACKABIERTO:
        match(TokenType.BRACKABIERTO)
        t.child[0] = expression()   # indice
        match(TokenType.BRACKCERRADO)
    return t

def simple_expression():
    """simple-expression -> additive-expression relop additive-expression
                          | additive-expression"""
    t = additive_expression()
    if token in _RELOPS:
        p          = newExpNode(ExpKind.OpK)
        p.child[0] = t
        p.op       = token
        t          = p
        match(token)
        t.child[1] = additive_expression()
    return t

def additive_expression():
    """additive-expression -> term { addop term }"""
    t = term()
    while token in {TokenType.SUMA, TokenType.RESTA}:
        p          = newExpNode(ExpKind.OpK)
        p.child[0] = t
        p.op       = token
        t          = p
        match(token)
        t.child[1] = term()
    return t

def term():
    """term -> factor { mulop factor }"""
    t = factor()
    while token in {TokenType.MULT, TokenType.DIV}:
        p          = newExpNode(ExpKind.OpK)
        p.child[0] = t
        p.op       = token
        t          = p
        match(token)
        t.child[1] = factor()
    return t

def factor():
    """factor -> ( expression ) | var | call | NUM"""
    global token, lexema, lineno
    t = None

    if token == TokenType.PARABIERTO:
        match(TokenType.PARABIERTO)
        t = expression()
        match(TokenType.PARCERRADO)

    elif token == TokenType.NUM:
        t     = newExpNode(ExpKind.ConstK)
        t.val = int(lexema)
        match(TokenType.NUM)

    elif token == TokenType.ID:
        savedName = lexema
        savedLine = lineno
        match(TokenType.ID)

        if token == TokenType.PARABIERTO:
            t = _build_call(savedName, savedLine)
        else:
            t        = newExpNode(ExpKind.IdK)
            t.name   = savedName
            t.lineno = savedLine
            if token == TokenType.BRACKABIERTO:
                match(TokenType.BRACKABIERTO)
                t.child[0] = expression()
                match(TokenType.BRACKCERRADO)

    else:
        syntaxError(f"token inesperado en factor: '{lexema}'")
        panic(SYNC_FACTOR)

    return t

def args():
    """args -> arg-list | empty  (regla 28)"""
    if token == TokenType.PARCERRADO:
        return None
    return arg_list()

def arg_list():
    """arg-list -> expression { , expression }"""
    t = expression()
    p = t
    while token == TokenType.COMA:
        match(TokenType.COMA)
        q = expression()
        if q is not None:
            if t is None:
                t = p = q
            else:
                p.sibling = q
                p = q
    return t


#--------------imprimir el AST--------------------------------

indentno = 0

def printSpaces():
    print(" " * indentno, end="")

def printToken(tok, tokStr):
    reservados = {TokenType.IF, TokenType.ELSE, TokenType.WHILE,
                  TokenType.RETURN, TokenType.INT, TokenType.VOID}
    if tok in reservados:
        print(f"palabra reservada: {tokStr}", end="")
    elif tok == TokenType.ASIGNAR:       print("=",   end="")
    elif tok == TokenType.MENORQ:        print("<",   end="")
    elif tok == TokenType.MENORIGUALQ:   print("<=",  end="")
    elif tok == TokenType.MAYORQ:        print(">",   end="")
    elif tok == TokenType.MAYORIGUALQ:   print(">=",  end="")
    elif tok == TokenType.EQUIV:         print("==",  end="")
    elif tok == TokenType.NEGACION:      print("!=",  end="")
    elif tok == TokenType.PARABIERTO:    print("(",   end="")
    elif tok == TokenType.PARCERRADO:    print(")",   end="")
    elif tok == TokenType.BRACKABIERTO:  print("[",   end="")
    elif tok == TokenType.BRACKCERRADO:  print("]",   end="")
    elif tok == TokenType.CORABIERTO:    print("{",   end="")
    elif tok == TokenType.CORCERRADO:    print("}",   end="")
    elif tok == TokenType.PUNTOYCOMA:    print(";",   end="")
    elif tok == TokenType.COMA:          print(",",   end="")
    elif tok == TokenType.SUMA:          print("+",   end="")
    elif tok == TokenType.RESTA:         print("-",   end="")
    elif tok == TokenType.MULT:          print("*",   end="")
    elif tok == TokenType.DIV:           print("/",   end="")
    elif tok == TokenType.ENDFILE:       print("EOF", end="")
    elif tok == TokenType.NUM:           print(f"NUM, val= {tokStr}",   end="")
    elif tok == TokenType.ID:            print(f"ID, nombre= {tokStr}", end="")
    elif tok == TokenType.ERROR:         print(f"ERROR: {tokStr}",      end="")
    else:                                print(f"Token desconocido: {tok}", end="")

def printTree(tree):
    global indentno
    indentno += 2
    while tree is not None:
        printSpaces()
        #nodos declaracion
        if tree.nodekind == NodeKind.DeclK:
            if tree.decl == DeclKind.VarK:
                arrStr = f"[{tree.arraySize}]" if tree.isArray else ""
                print(f"{tree.lineno}  Var: {tree.name}{arrStr}"
                      f"  tipo: {tree.typeSpec.name}")
            elif tree.decl == DeclKind.FunK:
                print(f"{tree.lineno}  Fun: {tree.name}"
                      f"  retorno: {tree.typeSpec.name}")
            elif tree.decl == DeclKind.ParamK:
                arrStr = "[]" if tree.isArray else ""
                print(f"{tree.lineno}  Param: {tree.name}{arrStr}"
                      f"  tipo: {tree.typeSpec.name}")
            else:
                print(f"{tree.lineno}  DeclNode desconocido")

        #nodos statement
        elif tree.nodekind == NodeKind.StmtK:
            if tree.stmt == StmtKind.IfK:
                print(f"{tree.lineno}  If")
            elif tree.stmt == StmtKind.WhileK:
                print(f"{tree.lineno}  While")
            elif tree.stmt == StmtKind.ReturnK:
                print(f"{tree.lineno}  Return")
            elif tree.stmt == StmtKind.CompoundK:
                print(f"{tree.lineno}  Compound")
            else:
                print(f"{tree.lineno}  StmtNode desconocido")

        #nodos expresion
        elif tree.nodekind == NodeKind.ExpK:
            if tree.exp == ExpKind.OpK:
                print(f"{tree.lineno}  Op: ", end="")
                printToken(tree.op, " ")
                print()
            elif tree.exp == ExpKind.AssignK:
                # Asignacion: child[0]=valor, child[1]=indice (si es arreglo)
                idx = "[indice]" if tree.child[1] is not None else ""
                print(f"{tree.lineno}  Assign: {tree.name} {idx}")
            elif tree.exp == ExpKind.ConstK:
                print(f"{tree.lineno}  Const: {tree.val}")
            elif tree.exp == ExpKind.IdK:
                print(f"{tree.lineno}  Id: {tree.name}")
            elif tree.exp == ExpKind.CallK:
                print(f"{tree.lineno}  Call: {tree.name}")
            else:
                print(f"{tree.lineno}  ExpNode desconocido")

        else:
            print(f"{tree.lineno}  Nodo desconocido")

        for i in range(MAXCHILDREN):
                    if (tree.nodekind == NodeKind.StmtK and
                            tree.stmt == StmtKind.IfK and
                            i == 2 and tree.child[2] is not None):
                        printSpaces()
                        print(f"{tree.lineno}  Else")
                    printTree(tree.child[i])

        tree = tree.sibling
    indentno -= 2


#------------------funcion de entrada del parser------------------

def parse(imprime=True):
    global token, lexema, lineno, Error
    Error = False
    token, lexema, lineno = getToken(imprimeLexer)
    _skipComments()
    t = program()
    if token != TokenType.ENDFILE:
        syntaxError("el codigo termina antes de fin de archivo")
        panic({TokenType.ENDFILE})
    if imprime:
        printTree(t)
    return t, Error


def globalesParser(prog, pos, long):
    globalesLexer(prog, pos, long)