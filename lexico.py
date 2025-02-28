from lark import Lark
from lark.exceptions import UnexpectedInput
import re

# 📜 Cargar la gramática desde el archivo
with open("prueba2.ebnf", "r") as file:
    grammar = file.read()

# ✅ Crear el parser con Lark
try:
    parser = Lark(grammar, parser="lalr", start="start")
    print("✅ La gramática es válida y compatible con Lark")
except Exception as e:
    print("❌ Error en la gramática:")
    print(e)

# 🛠 Verificar la sentencia
try:
    sentencia = "x + 0"
    tree = parser.parse(sentencia)
    
    print("✅ Sentencia válida")
    print(tree.pretty())  # Mostrar árbol sintáctico
except Exception as e:
    print("❌ Error en la sentencia:")
    print(e)
