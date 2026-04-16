from globalTypes import *
from lexer import *

f = open('sample2.c-', 'r')
programa = f.read() # lee el programa completo en un string
progLong = len(programa) # longitud del programa
programa = programa + '$' #agrega end of file caracter 
posicion = 0 #empieza en cero
f.close()

# pasa variables globales iniciales al lexer
globales(programa, posicion, progLong)

token, tokenString = getToken(True)
while token != TokenType.ENDFILE:
    token, tokenString = getToken(True)
