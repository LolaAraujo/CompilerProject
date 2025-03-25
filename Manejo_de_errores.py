import os
import sys
from DHParser.parse import compile_ebnf
from DHParser.testing import ParsingTester

#  Cargar la gramática desde el archivo EBNF
GRAMATICA_ARCHIVO = "gramatica.ebnf"

# Verificar si el archivo de gramática existe
if not os.path.exists(GRAMATICA_ARCHIVO):
    print(f" Error: No se encontró el archivo {GRAMATICA_ARCHIVO}")
    sys.exit(1)

# Compilar la gramática desde el archivo
with open(GRAMATICA_ARCHIVO, "r", encoding="utf-8") as file:
    gramatica_texto = file.read()

parser_factory = compile_ebnf(gramatica_texto, start_symbol="start")

#  Función para analizar código y detectar errores
def analizar_codigo(codigo_fuente):
    parser = parser_factory()
    result = parser.parse(codigo_fuente)

    if result.errors:
        print("\n Se encontraron errores sintácticos:\n")
        mostrar_errores(result.errors, codigo_fuente)
    else:
        print("\n Código analizado correctamente. No hay errores.")

#  Mostrar errores con formato personalizado
def mostrar_errores(errors, codigo_fuente):
    lineas = codigo_fuente.split("\n")

    for i, error in enumerate(errors, start=1):
        linea_error = error.line
        columna_error = error.col
        mensaje = error.message
        palabra_erronea = error.symbol  # Token problemático

        # Obtener la línea de código con el error
        linea_codigo = lineas[linea_error - 1] if 0 < linea_error <= len(lineas) else ""

        # Crear un puntero visual para el error
        puntero = " " * (columna_error - 1) + "^"

        # Generar sugerencias
        sugerencias = generar_sugerencias(mensaje)

        # Mostrar error con formato personalizado
        print(f"ERROR {i}:")
        print(f"    Ubicación: Línea {linea_error}, Columna {columna_error}")
        print(f"    Sujeto: '{palabra_erronea}'")
        print(f"    Tipo: {mensaje}")
        print(f"    Línea {linea_error}: {linea_codigo.strip()}")
        print(f"    {puntero}")
        print(f"    Posible solución: {sugerencias}\n")

#  Generar sugerencias de solución
def generar_sugerencias(mensaje):
    sugerencias_generales = [
        "Revisa la sintaxis de la estructura.",
        "Verifica si falta un punto y coma ';' al final.",
        "Asegúrate de que las llaves '{ }' estén balanceadas.",
        "Confirma que el nombre de variables y funciones esté bien escrito.",
        "Mira si falta un paréntesis '()' o una comilla '\"'."
    ]

    if "expected" in mensaje:
        sugerencia = f"Se esperaba: {mensaje.split('expected')[-1].strip()}."
    elif "unexpected" in mensaje:
        sugerencia = "Revisa si hay caracteres extraños o mal escritos."
    else:
        sugerencia = sugerencias_generales[0]

    return f"{sugerencia} Otra posible solución: {sugerencias_generales[1:]}"

#  Código de prueba
codigo_prueba = """
int a = 10
float b = 3.14
string nombre = "Juan;
"""

#  Ejecutar análisis sintáctico
analizar_codigo(codigo_prueba)
