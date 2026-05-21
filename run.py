from globalTypes import *
from Parser import *
from semantica import *

f = open('test5_errores_declaracion.cm', 'r')
programa = f.read()
f.close()

progLong = len(programa)
programa = programa + '$'
posicion = 0

# THIS LINE IS REQUIRED before calling parse()
globalesParser(programa, posicion, progLong)

# Also required before calling semantica()
globales(programa, posicion, progLong)

AST, Error = parse(True)
semantica(AST, True)