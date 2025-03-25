#Vale verga mi vida y este codigo 
from DHParser import compile_ebnf

# Definir una gramática EBNF simple
ebnf_grammar = """
expression = term ("+" term | "-" term)* ;
term       = factor ("*" factor | "/" factor)* ;
factor     = /\d+/ ;
"""

# Compilar la gramática usando DHParser
parser_factory = compile_ebnf(ebnf_grammar, start_symbol="expression")

# Crear el parser a partir de la gramática compilada
parser = parser_factory()

# Código de prueba
codigo_prueba = "3 + 5 * 2"

# Analizar el código
resultado = parser.parse(codigo_prueba)

# Verificar si hay errores
if resultado.errors:
    print("\nSe encontraron errores en el análisis sintáctico:\n")
    for error in resultado.errors:
        print(f"Error: {error.message} en línea {error.line}, columna {error.col}")
else:
    print("\n✅ Análisis sintáctico exitoso. Árbol generado:\n")
    print(resultado.as_xml())
