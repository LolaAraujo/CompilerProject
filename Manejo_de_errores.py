from lark import Lark, UnexpectedInput

# Cargar la gramática desde un archivo externo
with open("Gramatica.ebnf", "r") as file:
    grammar = file.read()

# Crear el parser léxico con Lark
try:
    lexer = Lark(grammar, parser="lalr", start="start")
except Exception as e:
    print("❌ Error en la gramática:", e)
    exit()

# Obtener tokens desde Lark
def obtener_tokens(codigo):
    try:
        tokens = list(lexer.lex(codigo))
        return [{"type": t.type, "value": t.value, "line": t.line, "column": t.column} for t in tokens]
    except UnexpectedInput as e:
        return [{"error": True, "line": e.line, "column": e.column, "context": e.get_context(codigo)}]
    except Exception as e:
        return [{"error": True, "message": str(e)}]

# Parser manual basado en pilas
class ParserManual:
    def __init__(self, tokens):
        self.tokens = tokens
        self.errors = []
        self.stack = []  # Pila para verificar paréntesis y llaves

    def parse(self):
        last_token = None
        for token in self.tokens:
            if "error" in token:
                # Detectar error de sintaxis
                self.errors.append({
                    "ERROR #": len(self.errors) + 1,
                    "ubicación": f"línea {token['line']}, columna {token['column']}",
                    "sujeto": token["value"],
                    "tipo": "Error sintáctico",
                    "posible solución": "Revisar la construcción del código."
                })
                continue

            token_type = token["type"]
            token_value = token["value"]

            # Verificar errores en operadores mal ubicados
            if token_type in ["PLUS", "MINUS", "STAR", "SLASH"]:
                if last_token is None or last_token in ["PLUS", "MINUS", "STAR", "SLASH", "LPAR"]:
                    self.errors.append({
                        "ERROR #": len(self.errors) + 1,
                        "ubicación": f"línea {token['line']}, columna {token['column']}",
                        "sujeto": token_value,
                        "tipo": "Error sintáctico",
                        "posible solución": "Un operador debe seguir a un número o variable."
                    })

            # Manejo de paréntesis y llaves con pila
            if token_type in ["LPAR", "LBRACE"]:
                self.stack.append((token_type, token["line"], token["column"]))
            elif token_type in ["RPAR", "RBRACE"]:
                if not self.stack:
                    self.errors.append({
                        "ERROR #": len(self.errors) + 1,
                        "ubicación": f"línea {token['line']}, columna {token['column']}",
                        "sujeto": token_value,
                        "tipo": "Error sintáctico",
                        "posible solución": "Asegurar que cada '(' o '{' tenga su cierre correspondiente."
                    })
                else:
                    self.stack.pop()

            last_token = token_type

        # Verificar paréntesis o llaves sin cerrar
        while self.stack:
            unclosed, line, column = self.stack.pop()
            self.errors.append({
                "ERROR #": len(self.errors) + 1,
                "ubicación": f"línea {line}, columna {column}",
                "sujeto": unclosed,
                "tipo": "Error sintáctico",
                "posible solución": "Asegurar que cada '(' y '{' tenga su cierre correspondiente."
            })

    def report(self):
        if self.errors:
            for error in self.errors:
                print(f"ERROR #{error['ERROR #']}: ubicación ({error['ubicación']}) sujeto ({error['sujeto']}) tipo ({error['tipo']}) posible solución: {error['posible solución']}")
        else:
            print("✅ Programa válido")

# ------------ PRUEBAS ------------

codigo_prueba = """
int x = 5;
if (x > 3) {
    print("Falta cierre");
"""

# Tokenizar y analizar
tokens = obtener_tokens(codigo_prueba)
parser_manual = ParserManual(tokens)
parser_manual.parse()
parser_manual.report()
