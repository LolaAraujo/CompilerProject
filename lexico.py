from lark import Lark
from lark.exceptions import UnexpectedInput
import re

# Cargar la gramática desde el archivo
with open("prueba2.ebnf", "r") as file:
    grammar = file.read()

# Imprimir las palabras reservadas
symbols = set(re.findall(r'"(.*?)"', grammar))
reserved_words = [item for item in symbols if item.isalpha() ]

print("Palabras reservadas:", sorted(reserved_words))


#  Crear el parser con Lark
try:
    parser = Lark(grammar, parser="lalr", start="start")
    print("✅ La gramática es válida y compatible con Lark")
except Exception as e:
    print("❌ Error en la gramática:")
    print(e)

#  Verificar la sentencia
try:
    sentencia = """
    int x = 10 + 5 
    float y = x * 3.14
    z = y - 2 / 4
    """
    tree = parser.parse(sentencia)
    
    print("✅ Sentencia válida")
    print(tree.pretty())  # Mostrar árbol sintáctico
except Exception as e:
    print("❌ Error en la sentencia:")
    print(e)
