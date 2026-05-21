# Sofia Moreno Lopez
# A01028251

from globalTypes import *

programa  = ''
posicion  = 0
progLong  = 0
error  = False


def globales(prog, pos, long):
    global programa, posicion, progLong
    programa = prog
    posicion = pos
    progLong = long

scopeStack = []
allScopes  = []
location   = 0    # contador de posiciones de memoria


def enterScope():
    scopeStack.append({})


def exitScope(name='', save=True):
# cierra el scope actual
    if scopeStack:
        scope = scopeStack.pop()
        if save:
            allScopes.append((name, scope))


def currentScope():
    return scopeStack[-1] if scopeStack else {}


def insertSymbol(name, kind, expType, isArray, arraySize, params, lineno,
                  silent=False):
    global location, error
    scope = currentScope()
    if name in scope:
        if not silent:
            semanticError(lineno, name,
                           f"'{name}' ya fue declarado en este alcance")
        return False
    scope[name] = {
        'kind'     : kind,
        'type'     : expType,
        'isArray'  : isArray,
        'arraySize': arraySize,
        'params'   : params,
        'loc'      : location,
        'lines'    : [lineno],
    }
    location += 1
    return True


def addLineRef(name, lineno):
    for scope in reversed(scopeStack):
        if name in scope:
            scope[name]['lines'].append(lineno)
            return


def lookupSymbol(name):
    for scope in reversed(scopeStack):
        if name in scope:
            return scope[name]
    return None


def printAllScopes():
    for (scopeName, scope) in allScopes:
        title = f"Tabla de símbolos {scopeName}" if scopeName else "Tabla de símbolos global"
        print()
        print(title)
        print("-" * 70)
        if not scope:
            print("  (vacía)")
            continue
        print(f"{'Nombre':<20} {'Tipo':<10} {'Clase':<8} {'Arreglo':<10} {'Loc':>4}  Líneas")
        print(f"{'------':<20} {'----':<10} {'-----':<8} {'-------':<10} {'---':>4}  ------")
        for name, info in scope.items():
            arrStr   = f"[{info['arraySize']}]" if info['isArray'] else "no"
            typeName = info['type'].name if info['type'] else '?'
            lines    = ' '.join(str(l) for l in info['lines'])
            print(f"{name:<20} {typeName:<10} {info['kind']:<8} {arrStr:<10}"
                  f" {info['loc']:>4}  {lines}")

def semanticError(lineno, tokenName, message):
    global error
    error = True

    lines    = programa.split('\n')
    lineText = lines[lineno - 1] if 0 < lineno <= len(lines) else ''

    col = lineText.find(str(tokenName)) if tokenName else 0
    col = max(col, 0)
    arrow = ' ' * col + '^'

    print(f"\nLínea {lineno}: Error semántico ; {message}")
    print(f"  {lineText}")
    print(f"  {arrow}")

currentFun     = None   # nombre de la función actual 
currentFunType = None   # tipo de retorno de la función actual


def traverseSymbols(t):
    global currentFun, currentFunType

    if t is None:
        return

    if t.nodekind == NodeKind.DeclK and t.decl == DeclKind.VarK:
        expType = ExpType.Integer if t.typeSpec == TokenType.INT else ExpType.Void
        if expType == ExpType.Void:
            semanticError(t.lineno, t.name,
                           f"variable '{t.name}' no puede ser de tipo void")
        else:
            insertSymbol(t.name, 'var', expType,
                          t.isArray, t.arraySize if t.isArray else 0,
                          None, t.lineno)
        for i in range(MAXCHILDREN):
            traverseSymbols(t.child[i])
        traverseSymbols(t.sibling)
        return

    if t.nodekind == NodeKind.DeclK and t.decl == DeclKind.FunK:
        retType = ExpType.Integer if t.typeSpec == TokenType.INT else ExpType.Void
        # Construir lista de parámetros formales
        paramList = []
        p = t.child[0]
        while p is not None:
            pType = ExpType.Integer if p.typeSpec == TokenType.INT else ExpType.Void
            paramList.append({'name': p.name, 'type': pType, 'isArray': p.isArray})
            p = p.sibling
        # Insertar la función en el scope actual (padre)
        insertSymbol(t.name, 'fun', retType, False, 0, paramList, t.lineno)
        # Guardar contexto
        prevFun     = currentFun
        prevFunType = currentFunType
        currentFun     = t.name
        currentFunType = retType
        # Abrir scope 
        enterScope()
        p = t.child[0]
        while p is not None:
            pType = ExpType.Integer if p.typeSpec == TokenType.INT else ExpType.Void
            if not (pType == ExpType.Void and p.name is None):
                insertSymbol(p.name, 'param', pType, p.isArray, 0, None, p.lineno)
            p = p.sibling
        traverseBodyOnly(t.child[1])
        exitScope(t.name)
        currentFun     = prevFun
        currentFunType = prevFunType
        traverseSymbols(t.sibling)
        return

    if t.nodekind == NodeKind.ExpK and t.exp in (ExpKind.IdK, ExpKind.AssignK):
        sym = lookupSymbol(t.name)
        if sym is None:
            semanticError(t.lineno, t.name,
                           f"identificador '{t.name}' no declarado")
        else:
            addLineRef(t.name, t.lineno)

    elif t.nodekind == NodeKind.ExpK and t.exp == ExpKind.CallK:
        sym = lookupSymbol(t.name)
        if sym is None:
            semanticError(t.lineno, t.name,
                           f"función '{t.name}' no declarada")
        else:
            addLineRef(t.name, t.lineno)

    elif t.nodekind == NodeKind.StmtK and t.stmt == StmtKind.CompoundK:
        enterScope()
        for i in range(MAXCHILDREN):
            traverseSymbols(t.child[i])
        exitScope(save=False)
        traverseSymbols(t.sibling)
        return

    for i in range(MAXCHILDREN):
        traverseSymbols(t.child[i])
    traverseSymbols(t.sibling)


def traverseBodyOnly(t):
    if t is None:
        return
    if t.nodekind == NodeKind.StmtK and t.stmt == StmtKind.CompoundK:
        # NO abrimos scope; ya fue abierto por la función
        for i in range(MAXCHILDREN):
            traverseSymbols(t.child[i])
        # NO cerramos scope aquí (lo cerrará la función)
        traverseSymbols(t.sibling)
        return
    traverseSymbols(t)

def tabla(tree, imprime=True):
    global scopeStack, allScopes, location, error
    scopeStack = []
    allScopes  = []
    location   = 0
    error    = False

    enterScope()
    traverseSymbols(tree)
    exitScope('global')

    if imprime:
        printAllScopes()

    return error

funStack = []  


def checkNode(t):
    if t is None:
        return

    if t.nodekind == NodeKind.ExpK:

        # [T-CONST]
        if t.exp == ExpKind.ConstK:
            t.type = ExpType.Integer

        # [T-ID-INT / T-ID-ARR]
        elif t.exp == ExpKind.IdK:
            sym = lookupSymbol(t.name)
            if sym is None:
                t.type = ExpType.Integer
            else:
                t.type = sym['type']
                if sym['isArray'] and t.child[0] is not None:
                    if t.child[0].type != ExpType.Integer:
                        semanticError(t.child[0].lineno, '',
                                       "el índice del arreglo debe ser de tipo int")
                    t.type = ExpType.Integer

        # [T-ARITH / T-REL]
        elif t.exp == ExpKind.OpK:
            left  = t.child[0]
            right = t.child[1]
            lType = left.type  if left  else ExpType.Void
            rType = right.type if right else ExpType.Void

            _RELOPS = {TokenType.MENORQ,    TokenType.MENORIGUALQ,
                       TokenType.MAYORQ,    TokenType.MAYORIGUALQ,
                       TokenType.EQUIV,     TokenType.NEGACION}
            _ARITH  = {TokenType.SUMA, TokenType.RESTA,
                       TokenType.MULT, TokenType.DIV}

            if t.op in _ARITH:
                if lType != ExpType.Integer:
                    semanticError((left.lineno if left else t.lineno), '',
                                   "operando izquierdo no es de tipo int")
                if rType != ExpType.Integer:
                    semanticError((right.lineno if right else t.lineno), '',
                                   "operando derecho no es de tipo int")
                t.type = ExpType.Integer
            elif t.op in _RELOPS:
                if lType != ExpType.Integer:
                    semanticError((left.lineno if left else t.lineno), '',
                                   "operando izquierdo de relación no es de tipo int")
                if rType != ExpType.Integer:
                    semanticError((right.lineno if right else t.lineno), '',
                                   "operando derecho de relación no es de tipo int")
                t.type = ExpType.Boolean
            else:
                t.type = ExpType.Integer

        # [T-ASSIGN]
        elif t.exp == ExpKind.AssignK:
            exprType = t.child[0].type if t.child[0] else ExpType.Void
            if t.child[1] is not None:   # índice de arreglo
                if t.child[1].type != ExpType.Integer:
                    semanticError(t.child[1].lineno, t.name,
                                   "índice de arreglo en asignación no es int")
            if exprType != ExpType.Integer:
                errLine = t.child[0].lineno if t.child[0] else t.lineno
                semanticError(errLine, t.name,
                               f"asignación de valor no-int a '{t.name}'")
            sym = lookupSymbol(t.name)
            t.type = sym['type'] if sym else ExpType.Integer

        # [T-CALL-I / T-CALL-V / T-ARGS]
        elif t.exp == ExpKind.CallK:
            sym = lookupSymbol(t.name)
            if sym is None:
                t.type = ExpType.Integer   # recuperación
            else:
                t.type = sym['type']
                formalParams = sym.get('params') or []
                actualArgs   = []
                a = t.child[0]
                while a is not None:
                    actualArgs.append(a)
                    a = a.sibling
                if len(actualArgs) != len(formalParams):
                    semanticError(t.lineno, t.name,
                                   f"'{t.name}' esperaba {len(formalParams)} "
                                   f"argumento(s), se pasaron {len(actualArgs)}")
                else:
                    for i, (arg, fp) in enumerate(zip(actualArgs, formalParams)):
                        # Verificar tipo base del argumento
                        if arg.type != fp['type'] and not (
                                fp['isArray'] and arg.type == ExpType.Integer):
                            semanticError(arg.lineno, t.name,
                                           f"argumento {i+1} de '{t.name}': "
                                           f"se esperaba {fp['type'].name}, "
                                           f"se recibió {arg.type.name}")
                        if fp['isArray']:
                            arg_sym = lookupSymbol(arg.name) if hasattr(arg, 'name') and arg.name else None
                            arg_is_array_var = (
                                arg.exp == ExpKind.IdK          # es un identificador simple
                                and arg.child[0] is None        # sin subíndice (no a[i])
                                and arg_sym is not None
                                and arg_sym['isArray']           # declarado como arreglo
                            ) if hasattr(arg, 'exp') else False
                            if not arg_is_array_var:
                                semanticError(arg.lineno, t.name,
                                               f"argumento {i+1} de '{t.name}': "
                                               f"se esperaba una variable de arreglo "
                                               f"(sin subíndice)")

    # Sentencias
    elif t.nodekind == NodeKind.StmtK:

        # [T-IF]
        if t.stmt == StmtKind.IfK:
            cond = t.child[0]
            if cond and cond.type not in (ExpType.Integer, ExpType.Boolean):
                semanticError(cond.lineno, '',
                               "la condición del if debe ser de tipo int o booleana")

        # [T-WHILE]
        elif t.stmt == StmtKind.WhileK:
            cond = t.child[0]
            if cond and cond.type not in (ExpType.Integer, ExpType.Boolean):
                semanticError(cond.lineno, '',
                               "la condición del while debe ser de tipo int o booleana")

        # [T-RET-I / T-RET-V]
        elif t.stmt == StmtKind.ReturnK:
            if funStack:
                funName, funRetType = funStack[-1]
                expr = t.child[0]
                if funRetType == ExpType.Void:
                    if expr is not None and expr.type != ExpType.Void:
                        semanticError(t.lineno, 'return',
                                       f"función void '{funName}' no debe retornar un valor")
                else:   # int
                    if expr is None:
                        semanticError(t.lineno, 'return',
                                       f"función int '{funName}' debe retornar un valor int")
                    elif expr.type != ExpType.Integer:
                        semanticError(expr.lineno, 'return',
                                       f"función int '{funName}' debe retornar int, "
                                       f"se encontró {expr.type.name}")

    # Declaraciones
    elif t.nodekind == NodeKind.DeclK:
        if t.decl == DeclKind.VarK and t.typeSpec == TokenType.VOID:
            semanticError(t.lineno, t.name,
                           f"variable '{t.name}' no puede ser de tipo void")


def traverseTypes(t):
    if t is None:
        return

    if t.nodekind == NodeKind.DeclK and t.decl == DeclKind.FunK:
        retType = ExpType.Integer if t.typeSpec == TokenType.INT else ExpType.Void
        funStack.append((t.name, retType))
        enterScope()
        p = t.child[0]
        while p is not None:
            pType = ExpType.Integer if p.typeSpec == TokenType.INT else ExpType.Void
            if not (pType == ExpType.Void and p.name is None):
                insertSymbol(p.name, 'param', pType, p.isArray, 0, None,
                              p.lineno, silent=True)
            p = p.sibling
        traverseBodyTypes(t.child[1])
        exitScope(t.name)
        funStack.pop()
        traverseTypes(t.sibling)
        return

    # Bloque compuesto: abrir scope
    if t.nodekind == NodeKind.StmtK and t.stmt == StmtKind.CompoundK:
        enterScope()
        insertLocalDecls(t.child[0])
        for i in range(MAXCHILDREN):
            traverseTypes(t.child[i])
        checkNode(t)
        exitScope(save=False)
        traverseTypes(t.sibling)
        return

    # Declaración de variable
    if t.nodekind == NodeKind.DeclK and t.decl == DeclKind.VarK:
        expType = ExpType.Integer if t.typeSpec == TokenType.INT else ExpType.Void
        insertSymbol(t.name, 'var', expType,
                      t.isArray, t.arraySize if t.isArray else 0,
                      None, t.lineno, silent=True)

    for i in range(MAXCHILDREN):
        traverseTypes(t.child[i])
    checkNode(t)
    traverseTypes(t.sibling)


def traverseBodyTypes(t):
    if t is None:
        return
    if t.nodekind == NodeKind.StmtK and t.stmt == StmtKind.CompoundK:
        insertLocalDecls(t.child[0])
        for i in range(MAXCHILDREN):
            traverseTypes(t.child[i])
        traverseTypes(t.sibling)
        return
    traverseTypes(t)


def insertLocalDecls(t):
    while t is not None:
        if t.nodekind == NodeKind.DeclK and t.decl == DeclKind.VarK:
            expType = ExpType.Integer if t.typeSpec == TokenType.INT else ExpType.Void
            insertSymbol(t.name, 'var', expType,
                          t.isArray, t.arraySize if t.isArray else 0,
                          None, t.lineno, silent=True)
        t = t.sibling

def insertGlobalDecls(t):
    while t is not None:
        if t.nodekind == NodeKind.DeclK and t.decl == DeclKind.VarK:
            expType = ExpType.Integer if t.typeSpec == TokenType.INT else ExpType.Void
            insertSymbol(t.name, 'var', expType,
                          t.isArray, t.arraySize if t.isArray else 0,
                          None, t.lineno, silent=True)
        elif t.nodekind == NodeKind.DeclK and t.decl == DeclKind.FunK:
            retType = ExpType.Integer if t.typeSpec == TokenType.INT else ExpType.Void
            paramList = []
            p = t.child[0]
            while p is not None:
                pType = ExpType.Integer if p.typeSpec == TokenType.INT else ExpType.Void
                paramList.append({'name': p.name, 'type': pType, 'isArray': p.isArray})
                p = p.sibling
            insertSymbol(t.name, 'fun', retType, False, 0, paramList,
                          t.lineno, silent=True)
        t = t.sibling


def checkMainDeclaration(tree):
    last = None
    t = tree
    while t is not None:
        last = t
        t = t.sibling

    if last is None:
        semanticError(0, 'main', "el programa está vacío; se esperaba función 'main'")
        return

    if not (last.nodekind == NodeKind.DeclK
            and last.decl == DeclKind.FunK
            and last.name == 'main'):
        semanticError(last.lineno, last.name,
                       "la última declaración del programa debe ser la función 'main'")

def semantica(tree, imprime=True):
    global scopeStack, allScopes, location, funStack, error

    tabla(tree, imprime)

    scopeStack = []
    allScopes  = []
    location   = 0
    funStack   = []

    checkMainDeclaration(tree)

    enterScope()
    insertGlobalDecls(tree)
    traverseTypes(tree)
    exitScope('global')

    if imprime:
        if error:
            print("\nAnálisis semántico completado con errores.")
        else:
            print("\nAnálisis semántico completado sin errores.")

    return error