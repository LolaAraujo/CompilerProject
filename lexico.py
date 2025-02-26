from lark import Lark
from lark.exceptions import UnexpectedInput
import re


with open("prueba.ebnf", "r") as file:
    grammar = file.read()

try:
    parser = Lark(grammar, parser="lalr")
    print("✅ La gramática es válida y compatible con Lark")
except Exception as e:
    print("❌ Error en la gramática:")
    print(e)

