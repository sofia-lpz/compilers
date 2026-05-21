# Sofia Moreno Lopez
# A01028251

from globalTypes import *

programa  = ''
posicion  = 0
progLong  = 0
hayError  = False


def globales(prog, pos, long):
    global programa, posicion, progLong
    programa = prog
    posicion = pos
    progLong = long

_scopeStack = []
_allScopes  = []
_location   = 0    # contador de posiciones de memoria


def _enterScope():
    _scopeStack.append({})


def _exitScope(name='', save=True):
# cierra el scope actual
    if _scopeStack:
        scope = _scopeStack.pop()
        if save:
            _allScopes.append((name, scope))


def _currentScope():
    return _scopeStack[-1] if _scopeStack else {}


def _insertSymbol(name, kind, expType, isArray, arraySize, params, lineno,
                  silent=False):
    global _location, hayError
    scope = _currentScope()
    if name in scope:
        if not silent:
            _semanticError(lineno, name,
                           f"'{name}' ya fue declarado en este alcance")
        return False
    scope[name] = {
        'kind'     : kind,
        'type'     : expType,
        'isArray'  : isArray,
        'arraySize': arraySize,
        'params'   : params,
        'loc'      : _location,
        'lines'    : [lineno],
    }
    _location += 1
    return True


def _addLineRef(name, lineno):
    for scope in reversed(_scopeStack):
        if name in scope:
            scope[name]['lines'].append(lineno)
            return


def _lookupSymbol(name):
    for scope in reversed(_scopeStack):
        if name in scope:
            return scope[name]
    return None


def _printAllScopes():
    for (scopeName, scope) in _allScopes:
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

def _semanticError(lineno, tokenName, message):
    global hayError
    hayError = True

    lines    = programa.split('\n')
    lineText = lines[lineno - 1] if 0 < lineno <= len(lines) else ''

    col = lineText.find(str(tokenName)) if tokenName else 0
    col = max(col, 0)
    arrow = ' ' * col + '^'

    print(f"\nLínea {lineno}: Error semántico – {message}")
    print(f"  {lineText}")
    print(f"  {arrow}")

_currentFun     = None   # nombre de la función actual (para imprimir scope)
_currentFunType = None   # tipo de retorno de la función actual


def _traverseSymbols(t):
    global _currentFun, _currentFunType

    if t is None:
        return

    if t.nodekind == NodeKind.DeclK and t.decl == DeclKind.VarK:
        expType = ExpType.Integer if t.typeSpec == TokenType.INT else ExpType.Void
        if expType == ExpType.Void:
            _semanticError(t.lineno, t.name,
                           f"variable '{t.name}' no puede ser de tipo void")
        else:
            _insertSymbol(t.name, 'var', expType,
                          t.isArray, t.arraySize if t.isArray else 0,
                          None, t.lineno)
        for i in range(MAXCHILDREN):
            _traverseSymbols(t.child[i])
        _traverseSymbols(t.sibling)
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
        _insertSymbol(t.name, 'fun', retType, False, 0, paramList, t.lineno)
        # Guardar contexto
        prevFun     = _currentFun
        prevFunType = _currentFunType
        _currentFun     = t.name
        _currentFunType = retType
        # Abrir scope 
        _enterScope()
        p = t.child[0]
        while p is not None:
            pType = ExpType.Integer if p.typeSpec == TokenType.INT else ExpType.Void
            if not (pType == ExpType.Void and p.name is None):
                _insertSymbol(p.name, 'param', pType, p.isArray, 0, None, p.lineno)
            p = p.sibling
        _traverseBodyOnly(t.child[1])
        _exitScope(t.name)
        _currentFun     = prevFun
        _currentFunType = prevFunType
        _traverseSymbols(t.sibling)
        return

    if t.nodekind == NodeKind.ExpK and t.exp in (ExpKind.IdK, ExpKind.AssignK):
        sym = _lookupSymbol(t.name)
        if sym is None:
            _semanticError(t.lineno, t.name,
                           f"identificador '{t.name}' no declarado")
        else:
            _addLineRef(t.name, t.lineno)

    elif t.nodekind == NodeKind.ExpK and t.exp == ExpKind.CallK:
        sym = _lookupSymbol(t.name)
        if sym is None:
            _semanticError(t.lineno, t.name,
                           f"función '{t.name}' no declarada")
        else:
            _addLineRef(t.name, t.lineno)

    elif t.nodekind == NodeKind.StmtK and t.stmt == StmtKind.CompoundK:
        _enterScope()
        for i in range(MAXCHILDREN):
            _traverseSymbols(t.child[i])
        _exitScope(save=False)
        _traverseSymbols(t.sibling)
        return

    for i in range(MAXCHILDREN):
        _traverseSymbols(t.child[i])
    _traverseSymbols(t.sibling)


def _traverseBodyOnly(t):
    if t is None:
        return
    if t.nodekind == NodeKind.StmtK and t.stmt == StmtKind.CompoundK:
        # NO abrimos scope; ya fue abierto por la función
        for i in range(MAXCHILDREN):
            _traverseSymbols(t.child[i])
        # NO cerramos scope aquí (lo cerrará la función)
        _traverseSymbols(t.sibling)
        return
    _traverseSymbols(t)

def tabla(tree, imprime=True):
    global _scopeStack, _allScopes, _location, hayError
    _scopeStack = []
    _allScopes  = []
    _location   = 0
    hayError    = False

    _enterScope()
    _traverseSymbols(tree)
    _exitScope('global')

    if imprime:
        _printAllScopes()

    return hayError

_funStack = []  


def _checkNode(t):
    """Post-orden: asigna t.type y reporta errores de tipo."""
    if t is None:
        return

    if t.nodekind == NodeKind.ExpK:

        # [T-CONST]
        if t.exp == ExpKind.ConstK:
            t.type = ExpType.Integer

        # [T-ID-INT / T-ID-ARR]
        elif t.exp == ExpKind.IdK:
            sym = _lookupSymbol(t.name)
            if sym is None:
                t.type = ExpType.Integer
            else:
                t.type = sym['type']
                if sym['isArray'] and t.child[0] is not None:
                    if t.child[0].type != ExpType.Integer:
                        _semanticError(t.child[0].lineno, '',
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
                    _semanticError((left.lineno if left else t.lineno), '',
                                   "operando izquierdo no es de tipo int")
                if rType != ExpType.Integer:
                    _semanticError((right.lineno if right else t.lineno), '',
                                   "operando derecho no es de tipo int")
                t.type = ExpType.Integer
            elif t.op in _RELOPS:
                if lType != ExpType.Integer:
                    _semanticError((left.lineno if left else t.lineno), '',
                                   "operando izquierdo de relación no es de tipo int")
                if rType != ExpType.Integer:
                    _semanticError((right.lineno if right else t.lineno), '',
                                   "operando derecho de relación no es de tipo int")
                t.type = ExpType.Boolean
            else:
                t.type = ExpType.Integer

        # [T-ASSIGN]
        elif t.exp == ExpKind.AssignK:
            exprType = t.child[0].type if t.child[0] else ExpType.Void
            if t.child[1] is not None:   # índice de arreglo
                if t.child[1].type != ExpType.Integer:
                    _semanticError(t.child[1].lineno, t.name,
                                   "índice de arreglo en asignación no es int")
            if exprType != ExpType.Integer:
                errLine = t.child[0].lineno if t.child[0] else t.lineno
                _semanticError(errLine, t.name,
                               f"asignación de valor no-int a '{t.name}'")
            sym = _lookupSymbol(t.name)
            t.type = sym['type'] if sym else ExpType.Integer

        # [T-CALL-I / T-CALL-V / T-ARGS]
        elif t.exp == ExpKind.CallK:
            sym = _lookupSymbol(t.name)
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
                    _semanticError(t.lineno, t.name,
                                   f"'{t.name}' esperaba {len(formalParams)} "
                                   f"argumento(s), se pasaron {len(actualArgs)}")
                else:
                    for i, (arg, fp) in enumerate(zip(actualArgs, formalParams)):
                        if arg.type != fp['type']:
                            _semanticError(arg.lineno, t.name,
                                           f"argumento {i+1} de '{t.name}': "
                                           f"se esperaba {fp['type'].name}, "
                                           f"se recibió {arg.type.name}")

    # Sentencias
    elif t.nodekind == NodeKind.StmtK:

        # [T-IF]
        if t.stmt == StmtKind.IfK:
            cond = t.child[0]
            if cond and cond.type != ExpType.Boolean:
                _semanticError(cond.lineno, '',
                               "la condición del if debe ser booleana "
                               "(usa <, <=, >, >=, ==, !=)")

        # [T-WHILE]
        elif t.stmt == StmtKind.WhileK:
            cond = t.child[0]
            if cond and cond.type != ExpType.Boolean:
                _semanticError(cond.lineno, '',
                               "la condición del while debe ser booleana "
                               "(usa <, <=, >, >=, ==, !=)")

        # [T-RET-I / T-RET-V]
        elif t.stmt == StmtKind.ReturnK:
            if _funStack:
                funName, funRetType = _funStack[-1]
                expr = t.child[0]
                if funRetType == ExpType.Void:
                    if expr is not None and expr.type != ExpType.Void:
                        _semanticError(t.lineno, 'return',
                                       f"función void '{funName}' no debe retornar un valor")
                else:   # int
                    if expr is None:
                        _semanticError(t.lineno, 'return',
                                       f"función int '{funName}' debe retornar un valor int")
                    elif expr.type != ExpType.Integer:
                        _semanticError(expr.lineno, 'return',
                                       f"función int '{funName}' debe retornar int, "
                                       f"se encontró {expr.type.name}")

    # Declaraciones
    elif t.nodekind == NodeKind.DeclK:
        if t.decl == DeclKind.VarK and t.typeSpec == TokenType.VOID:
            _semanticError(t.lineno, t.name,
                           f"variable '{t.name}' no puede ser de tipo void")


def _traverseTypes(t):
    if t is None:
        return

    # Manejo especial de declaraciones de función
    if t.nodekind == NodeKind.DeclK and t.decl == DeclKind.FunK:
        retType = ExpType.Integer if t.typeSpec == TokenType.INT else ExpType.Void
        _funStack.append((t.name, retType))
        _enterScope()
        p = t.child[0]
        while p is not None:
            pType = ExpType.Integer if p.typeSpec == TokenType.INT else ExpType.Void
            if not (pType == ExpType.Void and p.name is None):
                _insertSymbol(p.name, 'param', pType, p.isArray, 0, None,
                              p.lineno, silent=True)
            p = p.sibling
        _traverseBodyTypes(t.child[1])
        _exitScope(t.name)
        _funStack.pop()
        _traverseTypes(t.sibling)
        return

    # Bloque compuesto: abrir scope
    if t.nodekind == NodeKind.StmtK and t.stmt == StmtKind.CompoundK:
        _enterScope()
        _insertLocalDecls(t.child[0])
        for i in range(MAXCHILDREN):
            _traverseTypes(t.child[i])
        _checkNode(t)
        _exitScope(save=False)
        _traverseTypes(t.sibling)
        return

    # Declaración de variable
    if t.nodekind == NodeKind.DeclK and t.decl == DeclKind.VarK:
        expType = ExpType.Integer if t.typeSpec == TokenType.INT else ExpType.Void
        _insertSymbol(t.name, 'var', expType,
                      t.isArray, t.arraySize if t.isArray else 0,
                      None, t.lineno, silent=True)

    for i in range(MAXCHILDREN):
        _traverseTypes(t.child[i])
    _checkNode(t)
    _traverseTypes(t.sibling)


def _traverseBodyTypes(t):
    if t is None:
        return
    if t.nodekind == NodeKind.StmtK and t.stmt == StmtKind.CompoundK:
        _insertLocalDecls(t.child[0])
        for i in range(MAXCHILDREN):
            _traverseTypes(t.child[i])
        _traverseTypes(t.sibling)
        return
    _traverseTypes(t)


def _insertLocalDecls(t):
    while t is not None:
        if t.nodekind == NodeKind.DeclK and t.decl == DeclKind.VarK:
            expType = ExpType.Integer if t.typeSpec == TokenType.INT else ExpType.Void
            _insertSymbol(t.name, 'var', expType,
                          t.isArray, t.arraySize if t.isArray else 0,
                          None, t.lineno, silent=True)
        t = t.sibling

def _insertGlobalDecls(t):
    while t is not None:
        if t.nodekind == NodeKind.DeclK and t.decl == DeclKind.VarK:
            expType = ExpType.Integer if t.typeSpec == TokenType.INT else ExpType.Void
            _insertSymbol(t.name, 'var', expType,
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
            _insertSymbol(t.name, 'fun', retType, False, 0, paramList,
                          t.lineno, silent=True)
        t = t.sibling


#  FUNCION PRINCIPAL

def semantica(tree, imprime=True):
    """
    Análisis semántico completo de C-.
    1. Construye la(s) tabla(s) de símbolos (fase 1).
    2. Verifica tipos sobre el AST (fase 2).
    Devuelve True si hubo errores, False si todo está bien.
    """
    global _scopeStack, _allScopes, _location, _funStack, hayError

    tabla(tree, imprime)

    _scopeStack = []
    _allScopes  = []
    _location   = 0
    _funStack   = []

    _enterScope()
    _insertGlobalDecls(tree)
    _traverseTypes(tree)
    _exitScope('global')

    if imprime:
        if hayError:
            print("\nAnálisis semántico completado con errores.")
        else:
            print("\nAnálisis semántico completado sin errores.")

    return hayError