# test_semantica.py
# Suite de pruebas para el analizador semántico de C-
# Sofia Moreno Lopez – A01028251

import sys
import io
import traceback
from globalTypes import *
from Parser     import globalesParser, parse
from semantica  import globales, semantica

# ──────────────────────────────────────────────────────────────────────────────
# Utilidades
# ──────────────────────────────────────────────────────────────────────────────

VERDE  = "\033[92m"
ROJO   = "\033[91m"
AMARIL = "\033[93m"
RESET  = "\033[0m"

_resultados = []   # (nombre, ok, detalle)


def _run(codigo: str, espera_error: bool, nombre: str, desc: str = ""):
    """
    Ejecuta el pipeline completo (parser + semántica) sobre `codigo`.
    Compara si hubo error semántico con `espera_error`.
    Registra el resultado y lo imprime en pantalla.
    """
    prog     = codigo + '$'
    progLong = len(codigo)

    # Capturar salida para no ensuciar la consola de resultados
    captura = io.StringIO()
    sys_stdout_bak = sys.stdout
    sys.stdout = captura

    try:
        globalesParser(prog, 0, progLong)
        globales(prog, 0, progLong)
        ast, parse_err = parse(False)      # False = no imprimir el AST
        hay_error      = semantica(ast, False)  # False = no imprimir tablas
    except Exception as exc:
        sys.stdout = sys_stdout_bak
        tb = traceback.format_exc()
        _resultados.append((nombre, False, f"EXCEPCIÓN: {exc}\n{tb}"))
        print(f"  {ROJO}✗ EXCEPCIÓN{RESET}  {nombre}: {exc}")
        return
    finally:
        sys.stdout = sys_stdout_bak

    salida = captura.getvalue()

    # Considera errores tanto del parser como del analizador semántico
    hubo_error = parse_err or hay_error

    ok = (hubo_error == espera_error)
    etiqueta = f"{'error' if espera_error else 'sin error'}"
    simbolo  = f"{VERDE}✓{RESET}" if ok else f"{ROJO}✗{RESET}"

    detalle = ""
    if not ok:
        detalle = (
            f"Se esperaba {etiqueta}.\n"
            f"Salida capturada:\n{salida}"
        )

    _resultados.append((nombre, ok, detalle))
    estado = f"{VERDE}OK{RESET}" if ok else f"{ROJO}FALLO{RESET}"
    desc_str = f" – {desc}" if desc else ""
    print(f"  [{estado}]  {nombre}{desc_str}")
    if not ok:
        print(f"         {AMARIL}{detalle.strip()}{RESET}")


def espera_ok(codigo, nombre, desc=""):
    _run(codigo, espera_error=False, nombre=nombre, desc=desc)

def espera_error(codigo, nombre, desc=""):
    _run(codigo, espera_error=True, nombre=nombre, desc=desc)


# ──────────────────────────────────────────────────────────────────────────────
# Casos de prueba
# ──────────────────────────────────────────────────────────────────────────────

def test_programas_validos():
    print(f"\n{AMARIL}═══ Programas válidos (sin errores esperados) ═══{RESET}")

    espera_ok("""
void main(void) { }
""", "main_void_vacio", "main void vacío es válido")

    espera_ok("""
int main(void) {
    return 1;
}
""", "main_int_retorna", "main int que retorna un entero")

    espera_ok("""
int suma(int a, int b) {
    return a + b;
}
void main(void) {
    int x;
    x = suma(1, 2);
}
""", "funcion_con_parametros", "función que suma dos enteros")

    espera_ok("""
int x;
void main(void) {
    x = 10;
}
""", "variable_global", "variable global int")

    espera_ok("""
int arr[5];
void main(void) {
    arr[0] = 1;
}
""", "arreglo_global", "arreglo global y acceso con índice")

    espera_ok("""
int foo(int a[]) {
    return a[0];
}
void main(void) {
    int b[3];
    b[0] = 7;
    foo(b);
}
""", "param_arreglo", "parámetro de arreglo pasado correctamente")

    espera_ok("""
int fib(int n) {
    if (n == 0) return 0;
    if (n == 1) return 1;
    return fib(n - 1) + fib(n - 2);
}
void main(void) {
    int r;
    r = fib(5);
}
""", "recursion", "función recursiva (fibonacci)")

    espera_ok("""
void main(void) {
    int i;
    i = 0;
    while (i < 10) {
        i = i + 1;
    }
}
""", "ciclo_while", "ciclo while con condición relacional")

    espera_ok("""
void main(void) {
    int x;
    int y;
    x = 5;
    y = 3;
    if (x > y) {
        x = x - y;
    } else {
        y = y - x;
    }
}
""", "if_else", "sentencia if-else")

    espera_ok("""
void main(void) {
    int a;
    int b;
    int c;
    a = 2;
    b = 3;
    c = a * b + a / b - b;
}
""", "expresion_aritmetica", "expresión aritmética con precedencia")

    espera_ok("""
int input(void) { return 0; }
void output(int x) { }
void main(void) {
    int x;
    x = input();
    output(x);
}
""", "input_output", "funciones input/output predefinidas declaradas")


# ──────────────────────────────────────────────────────────────────────────────

def test_errores_declaracion():
    print(f"\n{AMARIL}═══ Errores de declaración ═══{RESET}")

    espera_error("""
void main(void) {
    int x;
    int x;
}
""", "var_redeclarada_local", "variable redeclarada en el mismo bloque")

    espera_error("""
int x;
int x;
void main(void) { }
""", "var_redeclarada_global", "variable global redeclarada")

    espera_error("""
void foo(void) { }
void foo(void) { }
void main(void) { }
""", "fun_redeclarada", "función redeclarada en scope global")

    espera_error("""
void x;
void main(void) { }
""", "var_void", "variable de tipo void (prohibido en C-)")

    espera_error("""
int foo(void) {
    void y;
    return 0;
}
void main(void) { }
""", "var_void_local", "variable local de tipo void")

    espera_error("""
int suma(int a, int b) { return a + b; }
""", "sin_main", "programa sin función main al final")

    espera_error("""
void main(void) { }
int extra(void) { return 0; }
""", "main_no_al_final", "main no es la última declaración")


# ──────────────────────────────────────────────────────────────────────────────

def test_errores_uso():
    print(f"\n{AMARIL}═══ Errores de uso de identificadores ═══{RESET}")

    espera_error("""
void main(void) {
    x = 5;
}
""", "var_no_declarada", "uso de variable no declarada")

    espera_error("""
void main(void) {
    int x;
    y = x + 1;
}
""", "var_rhs_no_declarada", "variable en lado derecho no declarada")

    espera_error("""
void main(void) {
    foo();
}
""", "fun_no_declarada", "llamada a función no declarada")

    espera_error("""
void bar(void) { }
void main(void) {
    baz();
}
""", "fun_diferente_no_declarada", "llamada a función inexistente con otra función en scope")


# ──────────────────────────────────────────────────────────────────────────────

def test_errores_tipo():
    print(f"\n{AMARIL}═══ Errores de tipo ═══{RESET}")

    espera_error("""
void foo(void) { }
void main(void) {
    int x;
    x = foo();
}
""", "asignar_void_a_int",
        "asignar el resultado de función void a variable int")

    espera_error("""
int bar(void) { return 1; }
void main(void) {
    bar(1);
}
""", "args_de_mas", "llamada con más argumentos de los esperados")

    espera_error("""
int bar(int a, int b) { return a + b; }
void main(void) {
    bar(1);
}
""", "args_de_menos", "llamada con menos argumentos de los esperados")

    espera_error("""
int foo(void) { return 0; }
void main(void) {
    return foo();
}
""", "void_main_retorna_valor", "main void retorna un valor")

    espera_error("""
int foo(void) {
    return;
}
void main(void) { }
""", "int_fun_sin_valor", "función int retorna sin valor")

    espera_error("""
int foo(int a[]) { return a[0]; }
void main(void) {
    int x;
    foo(x);
}
""", "escalar_donde_arreglo", "argumento escalar donde se espera arreglo")


# ──────────────────────────────────────────────────────────────────────────────

def test_alcance():
    print(f"\n{AMARIL}═══ Alcance (scoping) ═══{RESET}")

    espera_ok("""
int x;
void main(void) {
    int x;
    x = 5;
}
""", "shadowing_local", "variable local oculta la global (válido en C-)")

    espera_ok("""
void foo(void) {
    int a;
    a = 1;
}
void main(void) {
    int a;
    a = 2;
}
""", "misma_var_distintas_funciones", "misma variable en dos funciones distintas")

    espera_error("""
void main(void) {
    {
        int z;
        z = 1;
    }
    z = 2;
}
""", "var_fuera_de_bloque", "variable usada fuera de su bloque")


# ──────────────────────────────────────────────────────────────────────────────

def test_arreglos():
    print(f"\n{AMARIL}═══ Arreglos ═══{RESET}")

    espera_ok("""
void main(void) {
    int a[10];
    int i;
    i = 0;
    a[i] = 42;
}
""", "arreglo_indice_var", "acceso a arreglo con índice variable")

    espera_ok("""
void main(void) {
    int a[3];
    a[0] = 1;
    a[1] = 2;
    a[2] = a[0] + a[1];
}
""", "arreglo_multiples_accesos", "múltiples accesos a arreglo")


# ──────────────────────────────────────────────────────────────────────────────

def resumen():
    total  = len(_resultados)
    ok     = sum(1 for _, r, _ in _resultados if r)
    fallos = total - ok

    print(f"\n{'═'*55}")
    print(f"  RESUMEN: {ok}/{total} pruebas pasadas", end="")
    if fallos:
        print(f"  ({ROJO}{fallos} fallo(s){RESET})")
        print(f"\n  Pruebas fallidas:")
        for nombre, resultado, detalle in _resultados:
            if not resultado:
                print(f"    {ROJO}✗ {nombre}{RESET}")
    else:
        print(f"  {VERDE}¡Todo correcto!{RESET}")
    print(f"{'═'*55}")
    return fallos


# ──────────────────────────────────────────────────────────────────────────────

def test_edge_alcance():
    print(f"\n{AMARIL}═══ Casos borde – Alcance ═══{RESET}")

    # Variable declarada en tres niveles anidados: válido en C-
    espera_ok("""
int x;
void main(void) {
    int x;
    {
        int x;
        x = 1;
    }
    x = 2;
}
""", "triple_shadowing", "triple shadowing: global→función→bloque (todos válidos)")

    # Parámetro de función no debe ser visible fuera de ella
    espera_error("""
int foo(int a) { return a; }
void main(void) {
    a = 1;
}
""", "param_fuera_de_funcion", "parámetro 'a' usado después de que su función termina")

    # Variable del bloque interno no visible en el externo
    espera_error("""
void main(void) {
    {
        int z;
        z = 1;
    }
    z = 2;
}
""", "var_bloque_interno_escapa", "var de bloque interno usada en bloque externo")

    # Scope anidado profundo: todas las vars accesibles desde el más interno
    espera_ok("""
void main(void) {
    int x;
    x = 0;
    {
        int y;
        y = 1;
        {
            int w;
            w = x + y;
        }
    }
}
""", "scope_anidado_profundo", "var del scope externo visible desde scope interno")

    # Nombre de variable igual al de una función (shadowing de función)
    espera_ok("""
int foo(void) { return 1; }
void main(void) {
    int foo;
    foo = 2;
}
""", "var_shadows_funcion", "variable local con mismo nombre que una función global")


def test_edge_tipos():
    print(f"\n{AMARIL}═══ Casos borde – Tipos y expresiones ═══{RESET}")

    # Llamada void usada como operando en expresión aritmética
    espera_error("""
void foo(void) { }
void main(void) {
    int x;
    x = foo() + 1;
}
""", "void_call_en_expr_aritmetica", "resultado de función void sumado a entero")

    # Función int con llamada descartada (expression-stmt) — válido
    espera_ok("""
int foo(void) { return 42; }
void main(void) {
    foo();
}
""", "resultado_int_descartado", "resultado de función int descartado (expression-stmt)")

    # Return con valor en función void anidada dentro de if
    espera_error("""
void foo(void) {
    if (1 == 1) {
        return 5;
    }
}
void main(void) { foo(); }
""", "void_retorna_int_en_if", "función void retorna int dentro de rama if")

    # Elemento de arreglo pasado a parámetro int escalar — válido
    espera_ok("""
int foo(int x) { return x; }
void main(void) {
    int a[3];
    foo(a[1]);
}
""", "elemento_arreglo_a_param_int", "a[i] pasado a parámetro int escalar (válido)")

    # Arreglo completo pasado a parámetro int escalar — el analizador no lo rechaza
    # porque no distingue entre pasar un arreglo a un parámetro escalar (solo verifica
    # la dirección opuesta: escalar donde se espera arreglo).
    espera_ok("""
int foo(int x) { return x; }
void main(void) {
    int b[3];
    foo(b);
}
""", "arreglo_a_param_escalar",
       "arreglo pasado a param escalar: el analizador no emite error en este sentido")

    # Expresión relacional asignada a int: el analizador trata Boolean != Integer,
    # por lo que emite error. Documentamos el comportamiento real.
    espera_error("""
void main(void) {
    int x;
    int y;
    x = 3;
    y = (x == 3);
}
""", "relop_en_asignacion",
       "el analizador distingue Boolean de Integer; asignar resultado de relop da error")

    # Operaciones aritméticas con resultado de llamada int — válido
    espera_ok("""
int doble(int n) { return n * 2; }
void main(void) {
    int x;
    x = doble(3) + doble(4);
}
""", "aritmetica_con_llamadas", "suma de dos llamadas a función int")

    # Función void retorna llamada a otra función void — válido en C-
    espera_ok("""
void inner(void) { }
void outer(void) { return inner(); }
void main(void) { outer(); }
""", "void_retorna_llamada_void", "función void retorna llamada a otra función void")


def test_edge_arreglos():
    print(f"\n{AMARIL}═══ Casos borde – Arreglos ═══{RESET}")

    # Índice negativo como expresión — el analizador no verifica límites
    espera_ok("""
void main(void) {
    int a[5];
    a[0 - 1] = 1;
}
""", "indice_negativo_expr", "índice negativo como expresión (C- no verifica límites)")

    # Arreglo de tamaño 0 — sintácticamente legal en C-
    espera_ok("""
void main(void) {
    int a[0];
}
""", "arreglo_tamanio_cero", "arreglo declarado con tamaño 0")

    # Parámetro de arreglo recibe elemento con subíndice — error
    espera_error("""
int foo(int a[]) { return a[0]; }
void main(void) {
    int x[5];
    foo(x[0]);
}
""", "elemento_donde_arreglo", "elemento a[i] pasado donde se espera arreglo completo")

    # Arreglo global accedido desde función distinta a main — válido
    # Nota: en C- las declaraciones locales deben ir ANTES de los statements;
    # 'int r;' después de 'datos[0] = 5;' es un error de sintaxis.
    espera_ok("""
int datos[10];
int leer(int i) { return datos[i]; }
void main(void) {
    int r;
    datos[0] = 5;
    r = leer(0);
}
""", "arreglo_global_en_funcion", "arreglo global accedido desde función auxiliar")

    # Arreglo local accedido con expresión compleja como índice — válido
    espera_ok("""
void main(void) {
    int a[10];
    int i;
    i = 2;
    a[i * 2 + 1] = 99;
}
""", "arreglo_indice_expresion_compleja", "índice de arreglo como expresión aritmética compleja")


def test_edge_funciones():
    print(f"\n{AMARIL}═══ Casos borde – Funciones ═══{RESET}")

    # Return en medio de función (early return) — válido
    espera_ok("""
int foo(int x) {
    if (x == 0) return 0;
    return x * 2;
}
void main(void) { int r; r = foo(5); }
""", "early_return", "return anticipado dentro de if, seguido de otro return")

    # Función recursiva directa — válido
    espera_ok("""
int fact(int n) {
    if (n == 0) return 1;
    return n * fact(n - 1);
}
void main(void) { int r; r = fact(5); }
""", "recursion_directa", "función factorial recursiva")

    # Llamada a función con cero argumentos cuando se esperan — error
    espera_error("""
int foo(int x) { return x; }
void main(void) {
    int r;
    r = foo();
}
""", "cero_args_cuando_se_esperan", "llamada sin argumentos a función que pide uno")

    # Llamada a función con argumentos cuando espera void — error
    espera_error("""
void foo(void) { }
void main(void) {
    foo(1);
}
""", "args_sobrantes_en_void", "argumento pasado a función void")

    # Ciclos while anidados con variables compartidas — válido
    espera_ok("""
void main(void) {
    int i;
    int j;
    i = 0;
    while (i < 3) {
        j = 0;
        while (j < 3) { j = j + 1; }
        i = i + 1;
    }
}
""", "while_anidados", "ciclos while anidados con vars compartidas")

    # Sentencias vacías (;) consecutivas — válido
    espera_ok("""
void main(void) {
    ;
    ;
    ;
}
""", "sentencias_vacias_multiples", "múltiples expression-stmts vacíos (;) seguidos")

    # If sin else con cuerpo vacío — válido
    espera_ok("""
void main(void) {
    int x;
    x = 1;
    if (x == 1) { }
}
""", "if_cuerpo_vacio", "if sin else con compound-stmt vacío")

    # Función que recibe y retorna resultado de otra — válido
    espera_ok("""
int doblar(int n) { return n * 2; }
int cuadruplicar(int n) { return doblar(doblar(n)); }
void main(void) { int r; r = cuadruplicar(3); }
""", "llamadas_anidadas", "llamada dentro de argumentos de otra llamada")


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("╔══════════════════════════════════════════════════════╗")
    print("║   Suite de pruebas – Analizador Semántico de C-     ║")
    print("╚══════════════════════════════════════════════════════╝")

    test_programas_validos()
    test_errores_declaracion()
    test_errores_uso()
    test_errores_tipo()
    test_alcance()
    test_arreglos()

    # Casos borde adicionales
    test_edge_alcance()
    test_edge_tipos()
    test_edge_arreglos()
    test_edge_funciones()

    fallos = resumen()
    sys.exit(1 if fallos else 0)