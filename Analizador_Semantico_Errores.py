# Agregar al inicio del archivo, después de los imports
class TablaSimbolos:
    def __init__(self):
        self.ambitos = {"global": {}}
        self.ambito_actual = "global"

    def entrar_ambito(self, nombre):
        self.ambitos[nombre] = {}
        self.ambito_actual = nombre

    def salir_ambito(self):
        self.ambito_actual = "global"

    def declarar(self, nombre, tipo, linea, constante=False):
        ambito = self.ambitos[self.ambito_actual]
        if nombre in ambito:
            return f"Error semántico en línea {linea}: La variable '{nombre}' ya fue declarada en este ámbito."
        ambito[nombre] = {
            "tipo": tipo,
            "linea": linea,
            "inicializado": False,
            "referencias": 0,
            "constante": constante,
            "modificable": not constante
        }

    def obtener(self, nombre):
        if nombre in self.ambitos[self.ambito_actual]:
            return self.ambitos[self.ambito_actual][nombre]
        elif nombre in self.ambitos["global"]:
            return self.ambitos["global"][nombre]
        return None

    def esta_declarada(self, nombre):
        return self.obtener(nombre) is not None


class AnalizadorSemantico:
    def __init__(self):
        self.tabla = TablaSimbolos()
        self.errores = []

    def declarar_variable(self, nombre, tipo, linea, constante=False):
        error = self.tabla.declarar(nombre, tipo, linea, constante)
        if error:
            self.errores.append(error)

    def asignar_variable(self, nombre, tipo_valor, linea):
        simbolo = self.tabla.obtener(nombre)
        if not simbolo:
            self.errores.append(f"Error semántico en línea {linea}: La variable '{nombre}' no ha sido declarada.")
        else:
            if not simbolo["modificable"]:
                self.errores.append(f"Error semántico en línea {linea}: No se puede modificar la constante '{nombre}'.")
            elif simbolo["tipo"] != tipo_valor:
                self.errores.append(
                    f"Error de tipo en línea {linea}: No se puede asignar un valor de tipo '{tipo_valor}' a una variable de tipo '{simbolo['tipo']}'."
                )
            else:
                simbolo["inicializado"] = True

    def usar_variable(self, nombre, linea):
        simbolo = self.tabla.obtener(nombre)
        if not simbolo:
            self.errores.append(f"Error semántico en línea {linea}: La variable '{nombre}' no ha sido declarada.")
        else:
            simbolo["referencias"] += 1
            if not simbolo["inicializado"]:
                self.errores.append(f"Error semántico en línea {linea}: La variable '{nombre}' se usa sin ser inicializada.")

    def reportar_errores(self):
        if not self.errores:
            return ["✅ Programa válido (análisis semántico sin errores)."]
        else:
            return [f"🔍 Errores semánticos detectados:\n"] + [f"**ERROR {i}:** {error}" for i, error in enumerate(self.errores, start=1)]


# Modificar la función compile_code para incluir el análisis semántico
def compile_code():
    global tokens_list, symbol_table_instance
    
    code = input_code.get("1.0", "end-1c").strip()
    if not code:
        console_output.delete("1.0", "end")
        console_output.insert("end", "No hay código para compilar.\n")
        return

    # Limpiar resultados anteriores
    console_output.delete("1.0", "end")
    symbol_table_instance.clear()
    tokens_list.clear()
    error_manager.clear_errors()
    
    console_output.insert("end", "🔍 Analizando código...\n")
    root.update()  # Actualizar la interfaz para mostrar el mensaje

    try:
        # Análisis léxico (capturar tokens para tabla de símbolos)
        tokens_lexicos = list(parser.lex(code))  # <-- Esto obtiene los tokens para la tabla
        tokens_list = [
            f"{i+1}: {TOKENS_GRAMATICA.get(t.type, t.type)}: {t.value}"
            for i, t in enumerate(tokens_lexicos)
        ]
        
        # Análisis sintáctico
        tree = parser.parse(code)
        console_output.insert("end", "✅ Análisis sintáctico completado sin errores\n")
        
        # Análisis semántico
        sem = AnalizadorSemantico()
        # Simular el análisis semántico basado en los tokens
        for token in tokens_list:
            parts = token.split(": ")
            if len(parts) == 3:
                line_number, token_type, token_value = parts
                line_number = int(line_number)
                
                # Detectar declaraciones de variables (ejemplo: "int x;")
                if token_type == "PALABRA RESERVADA" and token_value in ["int", "float", "bool", "char", "string"]:
                    # Buscar el identificador en el siguiente token
                    next_token = next((t for t in tokens_list if t.startswith(f"{line_number}:") and "IDENTIFICADOR" in t), None)
                    if next_token:
                        ident = next_token.split(": ")[2]
                        sem.declarar_variable(ident, token_value, line_number)
                
                # Detectar asignaciones (ejemplo: "x = 5;")
                elif token_type == "IDENTIFICADOR" and "=" in token_value:
                    ident, value = token_value.split("=", 1)
                    ident = ident.strip()
                    value = value.strip()
                    
                    # Inferir el tipo del valor (simplificado)
                    tipo_valor = "int" if value.isdigit() else "float" if "." in value else "string"
                    sem.asignar_variable(ident, tipo_valor, line_number)
                
                # Detectar usos de variables (ejemplo: "print(x);")
                elif token_type == "IDENTIFICADOR":
                    sem.usar_variable(token_value, line_number)
        
        # Mostrar resultados del análisis semántico
        errores_semanticos = sem.reportar_errores()
        for error in errores_semanticos:
            console_output.insert("end", f"{error}\n")
        
        # Mostrar advertencias si hay tokens sospechosos
        mostrar_advertencias(tokens_list)
        
    except UnexpectedInput as e:
        # Si hay error, igual guardamos los tokens capturados hasta el error
        tokens_lexicos = list(parser.lex(code))
        tokens_list = [
            f"{i+1}: {TOKENS_GRAMATICA.get(t.type, t.type)}: {t.value}"
            for i, t in enumerate(tokens_lexicos)
        ]
        mostrar_error_sintactico(e, code)
    except Exception as e:
        mostrar_error_general(e)
    finally:
        # Mostrar tabla de símbolos si hay tokens capturados
        if tokens_list:
            show_symbol_table()