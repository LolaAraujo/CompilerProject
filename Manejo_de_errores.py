from dhparser import parse

# Función para obtener y mostrar los errores
def obtener_errores(codigo):
    try:
        # Analizar el código con DHParser usando la gramática EBNF
        ast = parse(codigo, grammar="Gramatica.ebnf")
        print("Árbol de análisis sintáctico:", ast)
        return None  # No hay errores
    except Exception as e:
        # En caso de error, se captura el mensaje de error
        return f"Error: {str(e)}"

# Código de prueba
codigo_prueba = """
int a = 10;
int b = 3;
a = b;
"""

# Obtener los errores
errores = obtener_errores(codigo_prueba)

# Mostrar errores o el árbol de análisis sintáctico
if errores:
    print(errores)
else:
    print("Análisis sintáctico exitoso.")
