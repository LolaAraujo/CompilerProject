from lark import Lark

with open ("EBNF.ebnf", "r") as file:
        grammar = file.read()

try:
    parser = Lark(grammar, parser="lair")
    print("La gramatica es valida")

except Exception:
    print("La gramatica es no valida")

