# Autores:
# Maria Dolores Cervantes Araujo
# Fabian Gutierrez Gachuz
# Fernando de Jesus Rivera Reos
# Update: 27/03/2025

import tkinter as tk
from tkinter import *
from PIL import Image, ImageTk
from lark import Lark
from lark.exceptions import UnexpectedInput
import re
from tkinter import Toplevel
from tkinter import messagebox
import sys
import json
from lark.tree import pydot__tree_to_png

# Ejemplo de código para analizar
# func suma(int a, int b) -> int {
#     return a + b;
# }

# Variable global para almacenar tokens
tokens_list = []

#==================== MANEJO DE ERRORES ====================

class ErrorManager:
    def __init__(self):
        self.error_count = 0
        self.errors = []
    
    def add_error(self, line, subject, error_type, solution):
        self.error_count += 1
        error_info = {
            "number": self.error_count,
            "line": line,
            "subject": subject,
            "type": error_type,
            "solution": solution
        }
        self.errors.append(error_info)
        return error_info
    
    def clear_errors(self):
        self.error_count = 0
        self.errors = []
    
    def format_error(self, error_info):
        return (f"ERROR #{error_info['number']}: "
                f"Línea {error_info['line']} - "
                f"'{error_info['subject']}' - "
                f"{error_info['type']}\n"
                f"Posible solución: {error_info['solution']}\n")
    
    def get_all_errors_formatted(self):
        return "\n".join([self.format_error(e) for e in self.errors])

# Instancia global del manejador de errores
error_manager = ErrorManager()

#==================== TABLA DE SÍMBOLOS ====================

class SymbolTable:
    def __init__(self, max_memory_size=100):
        """
        Initialize the Symbol Table with memory management

        Args:
            max_memory_size (int): Maximum memory size in bytes for in-memory storage
        """
        # In-memory storage for symbols
        self.symbols = {}
        self.type_cache = {}

        # Maximum memory size for in-memory storage
        self.max_memory_size = max_memory_size

        # Secondary storage file path
        self.secondary_storage_path = "symbol_table_overflow.json"

        # Ensure the secondary storage file exists
        open(self.secondary_storage_path, 'a').close()

    def _is_memory_available(self, symbol_size):
        """
        Check if there's enough memory to store the symbol

        Args:
            symbol_size (int): Size of the symbol to be stored

        Returns:
            bool: True if memory is available, False otherwise
        """
        current_memory_usage = sum(len(json.dumps(symbol)) for symbol in self.symbols.values())
        return current_memory_usage + symbol_size <= self.max_memory_size

    def add_symbol(self, identifier, details):
        """
        Add a symbol to the table, managing memory automatically

        Args:
            identifier (str): The symbol's identifier
            details (dict): Detailed information about the symbol
        """
        symbol_size = len(json.dumps(details))

        if not self._is_memory_available(symbol_size):
            # If memory is full, move to secondary storage
            self._move_to_secondary_storage(identifier, details)
        else:
            # Store in memory
            self.symbols[identifier] = details

    def _move_to_secondary_storage(self, identifier, details):
        """
        Move symbol to secondary storage

        Args:
            identifier (str): The symbol's identifier
            details (dict): Detailed information about the symbol
        """
        try:
            with open(self.secondary_storage_path, 'r+') as f:
                try:
                    storage = json.load(f)
                except json.JSONDecodeError:
                    storage = {}

                storage[identifier] = details

                # Reset file pointer and truncate
                f.seek(0)
                json.dump(storage, f, indent=2)
                f.truncate()
        except Exception as e:
            print(f"Error in secondary storage: {e}")

    def get_symbol(self, identifier):
        """
        Retrieve a symbol from memory or secondary storage

        Args:
            identifier (str): The symbol's identifier

        Returns:
            dict: Symbol details or None if not found
        """
        # First check in-memory symbols
        if identifier in self.symbols:
            return self.symbols[identifier]

        # If not in memory, check secondary storage
        try:
            with open(self.secondary_storage_path, 'r') as f:
                storage = json.load(f)
                return storage.get(identifier)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def get_all_symbols(self):
        """
        Retrieve all symbols from memory and secondary storage

        Returns:
            dict: All symbols in the table
        """
        all_symbols = dict(self.symbols)

        try:
            with open(self.secondary_storage_path, 'r') as f:
                try:
                    secondary_storage = json.load(f)
                    all_symbols.update(secondary_storage)
                except json.JSONDecodeError:
                    pass
        except FileNotFoundError:
            pass

        return all_symbols
    
    # Funciones locales para inferir tipo y valor
    def infer_type(self, token_type,identifier):
        cache_key = f"{token_type}_{identifier}"
        if cache_key in self.type_cache:
            return self.type_cache[cache_key]
        # Obtenemos la categoría del token
        token_category = TOKENS_GRAMATICA.get(token_type, None)
        
        # Asignación directa de tipos basada en tu gramática
        if token_category in ["ENTERO", "NUMERO"]:
            return "entero"
        elif token_category in ["FLOTANTE", "NUMERO FLOTANTE"]:
            return "real"
        elif token_category == "BOOLEANO":
            return "booleano"
        elif token_category in ["CARACTER", "CADENA"]:
            return "cadena"
        elif token_category == "ARREGLO":
            return "arreglo"
        # Para identificadores (variables/funciones)
        if token_type == "IDENTIFICADOR":
            # Verificamos si es una función conocida
            if identifier in ["void", "read", "func", "main"]:
                return "función"
            elif identifier in ["print"]:
                return "función de salida"
            
            # Inferencia por convenciones de nombre
            lower_id = identifier.lower()
            if lower_id.startswith(('is_', 'has_', 'can_')): 
                return "booleano"
            elif lower_id.endswith(('count', 'total', 'num', 'id', 'index')):
                return "entero"
            elif lower_id.endswith(('price', 'amount', 'value', 'sum', 'avg')):
                return "real"
            elif lower_id.endswith(('name', 'text', 'msg', 'title')):
                return "cadena"
            elif lower_id.endswith(('arr', 'list', 'set')):
                return "arreglo"
        
        inferred_type = "variable"  # Valor por defecto
        self.type_cache[cache_key] = inferred_type
        return inferred_type
    
    def get_value(self, identifier, token_value=None, token_type=None):
        """Obtiene el valor inicial si está disponible"""
        # Si ya tenemos un valor explícito
        if token_value:
            # Para tipos numéricos, formatear adecuadamente
            if token_type in ["ENTERO", "NUMERO"]:
                return str(int(token_value))
            elif token_type in ["FLOTANTE", "NUMERO FLOTANTE"]:
                return str(float(token_value))
            # Para cadenas, mostrar con comillas
            elif token_type in ["CADENA", "CARACTER"]:
                return f'"{token_value}"'
            # Para booleanos, normalizar
            elif token_type == "BOOLEANO":
                return token_value.lower()
            return token_value
        
        # Buscar en los tokens si hay una asignación para este identificador
        for token in tokens_list:
            parts = token.split(": ")
            if len(parts) == 3:
                # Detectar patrones de asignación como "x = 5"
                if "ASIGNACION" in parts[1] and f"{identifier} =" in parts[2]:
                    # Extraer valor después del signo igual
                    value_part = parts[2].split("=")[1].strip()
                    return value_part
        
        return "No inicializado"
    
    def determine_state(self, identifier):
        """Determina el estado de un identificador basado en su uso en el código"""
        declared = False
        initialized = False
        used = False
        
        for token in tokens_list:
            parts = token.split(": ")
            if len(parts) == 3:
                line_number, token_type, token_value = parts
                
                # Detectar declaraciones (int x, float y, etc.)
                if token_value == identifier and any(
                    t for t in tokens_list if t.split(": ")[2].startswith(f"{identifier} :") 
                    or ("DECLARACION" in t and identifier in t)
                ):
                    declared = True
                
                # Detectar inicializaciones (x = 5, etc.)
                if "ASIGNACION" in token_type and token_value.startswith(f"{identifier} ="):
                    initialized = True
                
                # Detectar usos (en expresiones, llamadas, etc.)
                if token_value == identifier and token_type == "IDENTIFICADOR":
                    used = True
        
        # Determinar estado final
        if declared and initialized and used:
            return "Declarado, Inicializado, Usado"
        elif declared and initialized:
            return "Declarado, Inicializado"
        elif declared and used:
            return "Declarado, Usado"
        elif declared:
            return "Solo Declarado"
        elif used:
            return "Usado (sin declarar)"
        else:
            return "Desconocido"
        
    def get_structure_info(self, identifier, token_type=None):
        """Obtiene información de estructura para arreglos o tipos compuestos"""
        # Para arreglos
        if token_type == "ARREGLO":
            # Buscar declaraciones de arreglo
            for token in tokens_list:
                if ": ARREGLO: " in token and identifier in token:
                    # Intentar extraer dimensiones
                    try:
                        dimensions = re.findall(r'\[(\d+)\]', token)
                        if dimensions:
                            return f"Arreglo {len(dimensions)}D: [{' × '.join(dimensions)}]"
                    except:
                        pass
            return "Arreglo"
        
        # Para estructuras/registros
        elif token_type == "STRUCT":
            # Buscar campos de estructura
            struct_def = None
            for i, token in enumerate(tokens_list):
                if ": STRUCT: " in token and identifier in token:
                    struct_def = i
                    break
            
            if struct_def is not None:
                # Buscar campos entre llaves
                fields = []
                brace_level = 0
                for i in range(struct_def, len(tokens_list)):
                    token = tokens_list[i]
                    if ": LLAVE INICIO: " in token:
                        brace_level += 1
                    elif ": LLAVE CIERRE: " in token:
                        brace_level -= 1
                        if brace_level == 0:
                            break
                    elif brace_level > 0 and ": IDENTIFICADOR: " in token:
                        fields.append(token.split(": ")[2])
                
                if fields:
                    return f"Struct con {len(fields)} campos"
            
            return "Struct"
        
        # Para funciones
        elif identifier in ["main", "print", "void", "read", "func"] or token_type == "FUNCIÓN":
            # Buscar parámetros y tipo de retorno
            for token in tokens_list:
                if f": {identifier}(" in token or f": {identifier} (" in token:
                    params = re.search(r'\((.*?)\)', token.split(": ")[2])
                    return_type = re.search(r'-> (.*?)($|\s|{)', token.split(": ")[2])
                    
                    params_str = params.group(1) if params else ""
                    return_str = return_type.group(1) if return_type else "void"
                    
                    param_count = len(params_str.split(",")) if params_str.strip() else 0
                    return f"Función: {param_count} param(s) -> {return_str}"
            
            return "Función"
        
        return "N/A"

    def clear(self):
        """
        Clear all symbols from memory and secondary storage
        """
        self.symbols.clear()

        # Clear secondary storage file
        open(self.secondary_storage_path, 'w').close()

# Instancia global de la tabla de símbolos
symbol_table_instance = SymbolTable()


# ==================== ANALIZADOR SEMANTICO  ====================

#==================== ANALIZADOR SEMANTICO ====================

class TablaSimbolos:
    def __init__(self):
        self.ambitos = [{}]  # Pila de ámbitos

    def entrar_ambito(self):
        self.ambitos.append({})

    def salir_ambito(self):
        self.ambitos.pop()

    def declarar(self, nombre, tipo, linea, constante=False):
        ambito_actual = self.ambitos[-1]
        if nombre in ambito_actual:
            return f"Error semántico en línea {linea}: La variable '{nombre}' ya fue declarada en este ámbito."
        for ambito in reversed(self.ambitos[:-1]):
            if nombre in ambito:
                return f"Error semántico en línea {linea}: La variable local '{nombre}' oculta una variable del ámbito superior."
        ambito_actual[nombre] = {
            "tipo": tipo,
            "linea": linea,
            "inicializado": False,
            "referencias": 0,
            "constante": constante,
            "modificable": not constante
        }

    def obtener(self, nombre):
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                return ambito[nombre]
        return None


class AnalizadorSemantico:
    def __init__(self):
        self.tabla = TablaSimbolos()
        self.errores = []
        self.funciones = {}
        self.funcion_actual = None
        self.codigo_inalcanzable = False  # Bandera para detectar código inalcanzable

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

    def declarar_funcion(self, nombre, parametros, tipo_retorno, linea):
        if nombre in self.funciones:
            self.errores.append(f"Error en línea {linea}: La función '{nombre}' ya fue definida.")
        else:
            self.funciones[nombre] = {
                "parametros": parametros,
                "retorno": tipo_retorno,
                "linea": linea,
                "tiene_retorno": False,
                "tiene_caso_base": False  # Para controlar la recursión sin caso base
            }

    def entrar_funcion(self, nombre):
        self.funcion_actual = self.funciones[nombre]
        self.tabla.entrar_ambito()
        for tipo, nombre_param in self.funcion_actual["parametros"]:
            self.tabla.declarar(nombre_param, tipo, self.funcion_actual["linea"])

    def salir_funcion(self):
        if self.funcion_actual["retorno"] != "void" and not self.funcion_actual["tiene_retorno"]:
            self.errores.append(f"Error: La función '{self.funcion_actual}' no contiene una sentencia de retorno.")
        if self.funcion_actual["retorno"] != "void" and not self.funcion_actual["tiene_caso_base"]:
            self.errores.append(f"Advertencia: La función '{self.funcion_actual}' es recursiva pero no tiene un caso base detectado.")
        self.funcion_actual = None
        self.tabla.salir_ambito()

    def llamada_funcion(self, nombre, argumentos, linea):
        if nombre not in self.funciones:
            self.errores.append(f"Error en línea {linea}: La función '{nombre}' no está definida.")
        else:
            f = self.funciones[nombre]
            if len(argumentos) != len(f["parametros"]):
                self.errores.append(
                    f"Error en línea {linea}: La función '{nombre}' espera {len(f['parametros'])} argumentos pero se pasaron {len(argumentos)}."
                )
            else:
                for (arg_tipo, (param_tipo, _)) in zip(argumentos, f["parametros"]):
                    if arg_tipo != param_tipo:
                        self.errores.append(
                            f"Error en línea {linea}: Se esperaba un argumento de tipo '{param_tipo}' pero se recibió '{arg_tipo}'."
                        )

    def retorno_funcion(self, tipo_retorno, linea):
        if not self.funcion_actual:
            self.errores.append(f"Error en línea {linea}: Sentencia 'return' fuera de función.")
        elif tipo_retorno != self.funcion_actual["retorno"]:
            self.errores.append(
                f"Error en línea {linea}: Se retorna tipo '{tipo_retorno}', pero la función espera '{self.funcion_actual['retorno']}'."
            )
        else:
            self.funcion_actual["tiene_retorno"] = True

    def registrar_llamada_en_funcion(self, nombre_funcion_llamada, linea):
        if self.funcion_actual and nombre_funcion_llamada == self.funcion_actual:
            # Si la función se llama a sí misma sin caso base
            if not self.funcion_actual.get("tiene_caso_base", False):
                self.errores.append(
                    f"Advertencia en línea {linea}: La función '{nombre_funcion_llamada}' parece recursiva sin un caso base detectado."
                )

    def registrar_caso_base(self):
        if self.funcion_actual:
            self.funcion_actual["tiene_caso_base"] = True

    def verificar_division(self, operando_derecho, linea):
        if isinstance(operando_derecho, (int, float)) and operando_derecho == 0:
            self.errores.append(f"Error en línea {linea}: División por cero detectada en tiempo de compilación.")

    def acceso_array(self, nombre, indice, longitud, linea):
        if isinstance(indice, int) and (indice < 0 or indice >= longitud):
            self.errores.append(f"Error en línea {linea}: Índice {indice} fuera de rango para arreglo '{nombre}' de longitud {longitud}.")

    def operacion_binaria(self, tipo1, tipo2, operador, linea):
        compatibles = {
            '+': [('int', 'int'), ('float', 'float'), ('int', 'float'), ('float', 'int'), ('string', 'string')],
            '-': [('int', 'int'), ('float', 'float'), ('int', 'float'), ('float', 'int')],
            '*': [('int', 'int'), ('float', 'float'), ('int', 'float'), ('float', 'int')],
            '/': [('int', 'int'), ('float', 'float'), ('int', 'float'), ('float', 'int')],
            '%': [('int', 'int')],
        }
        if (tipo1, tipo2) not in compatibles.get(operador, []):
            self.errores.append(
                f"Error de tipo en línea {linea}: Operador '{operador}' no es compatible con tipos '{tipo1}' y '{tipo2}'."
            )

    def analizar_sentencia(self, tipo_sentencia, linea):
        if tipo_sentencia == "return" or tipo_sentencia == "break" or tipo_sentencia == "continue":
            self.codigo_inalcanzable = True
        elif self.codigo_inalcanzable:
            self.errores.append(f"Advertencia en línea {linea}: Bloque de código inalcanzable detectado.")

    def reiniciar_codigo_inalcanzable(self):
        self.codigo_inalcanzable = False  # Reinicia cuando se sale de un bloque de control

    def reportar_errores(self):
        if not self.errores:
            print("✅ Programa válido (análisis semántico sin errores).")
        else:
            print("🔍 Errores semánticos detectados:\n")
            for i, error in enumerate(self.errores, start=1):
                print(f"**ERROR {i}:** {error}")


# ==================== VISUALIZACIONES ====================

def show_symbol_table():
    """Creates a pop-up window for the symbol table"""
    global tokens_list, symbol_table_instance

    if not tokens_list:
        messagebox.showinfo("Información", "No hay tokens para mostrar.")
        return

    pop_up = tk.Toplevel(root)
    pop_up.title("Tabla de Símbolos")
    pop_up.geometry("1090x550")


    label = tk.Label(pop_up, text="Tabla de Símbolos", font=("Arial", 11))
    label.pack()

    symbol_table_popup = tk.Text(pop_up, bg='lightgray', fg='black', font=("Consolas", 10))
    symbol_table_popup.pack(expand=True, fill="both")

    # Headers
    headers = ["Identificador", "Categoría", "Tipo", "Ámbito", "Dirección" ,"Línea", "Valor","Estado", "Estructura", "Uso"]
    header_format = "{:<20} {:<20} {:<15} {:<15} {:<18} {:<10} {:20} {:20} {:15} {:10}\n".format(*headers)
    symbol_table_popup.insert("end", header_format)
    symbol_table_popup.insert("end", "-" * 170 + "\n")
    
    print("Tokens List: ", tokens_list)
    # Count the usage of each identifier
    usage_count = {}
    for token in tokens_list:
        parts = token.split(": ")
        if len(parts) == 3 and parts[1] == "IDENTIFICADOR":
            identifier = parts[2]
            usage_count[identifier] = usage_count.get(identifier, 0) + 1
            
    print("Usage Count: ", usage_count)

    # Initialize a set to keep track of processed identifiers
    processed_identifiers = set()
    for token in tokens_list:
        try:
            parts = token.split(": ")
            if len(parts) == 3:
                line_number, token_type, identifier = parts[0], parts[1], parts[2]
                
                # Solo procesamos identificadores no vistos
                if token_type == "IDENTIFICADOR" and identifier not in processed_identifiers:
                    
                    # Determinar categoría basada en el token
                    if identifier in ["main", "print", "void", "read", "func"]:
                        category = "FUNCIÓN"
                    else:
                        category = TOKENS_GRAMATICA.get(token_type, "VARIABLE")
                        
                    # Detección básica de declaraciones (mejorable)
                    is_declaration = any(
                        t for t in tokens_list 
                        if f"{identifier}:" in t and "DECLARACION" in t
                    )
                    
                    symbol_details = {
                        "Identificador": identifier,
                        "Categoría": category,
                        "Tipo": symbol_table_instance.infer_type(token_type, identifier),
                        "Ámbito": "Global" if identifier == "global" else "Local",
                        "Dirección": f"0x{abs(hash(identifier)):08X}",
                        "Línea": line_number,
                        "Valor": symbol_table_instance.get_value(identifier, None, token_type),  # Pasamos token_type
                        "Estado": symbol_table_instance.determine_state(identifier),
                        "Estructura": symbol_table_instance.get_structure_info(identifier, token_type),
                        "Uso": usage_count.get(identifier, 1)
                    }

                    symbol_table_instance.add_symbol(identifier, symbol_details)
        except Exception as e:
            print(f"Error procesando token {token}: {str(e)}")
            continue
   
    all_symbols = symbol_table_instance.get_all_symbols()
    for identifier, symbol in all_symbols.items():
        try: 
            row_format = "{:<20} {:<20} {:<15} {:<15} {:<18} {:<10} {:20} {:20} {:15} {:10}\n".format(
                symbol.get("Identificador", "")[:20],
                symbol.get("Categoría", "")[:20],
                symbol.get("Tipo", "")[:15],
                symbol.get("Ámbito", "")[:15],
                symbol.get("Dirección", "0x0000")[:15],
                symbol.get("Línea", "")[:10],
                symbol.get("Valor", "")[:20],
                symbol.get("Estado", "")[:20],
                symbol.get("Estructura", "")[:15],
                str(symbol.get("Uso", 0))[:10]  # Aseguramos que sea string para el formato
            )
            symbol_table_popup.insert("end", row_format)
        except Exception as e:
            print(f"Error mostrando símbolo {identifier}: {str(e)}")
            continue

    symbol_table_popup.config(state="disabled")

def show_ats_tree():
    global parser
    
    if parser is None:
        messagebox.showerror("Error", "El parser no ha sido inicializado correctamente")
        return

    code = input_code.get("1.0", "end-1c").strip()
    if not code:
        messagebox.showinfo("Información", "No hay código para analizar.")
        return

    try:
        # Parsear el código para obtener el AST
        tree = parser.parse(code)
        
        # Crear ventana emergente
        tree_window = tk.Toplevel(root)
        tree_window.title("Árbol de Análisis Sintáctico Jerárquico")
        tree_window.geometry("1000x700")
        
        # Frame principal con scrollbars
        main_frame = tk.Frame(tree_window)
        main_frame.pack(expand=True, fill="both")
        
        # Canvas para dibujar el árbol
        canvas = tk.Canvas(main_frame, bg="white")
        scroll_y = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scroll_x = tk.Scrollbar(main_frame, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        canvas.pack(expand=True, fill="both")
        
        # Frame interno para los nodos del árbol
        tree_frame = tk.Frame(canvas, bg="white")
        canvas.create_window((0, 0), window=tree_frame, anchor="nw")
        
        # Variables para el diseño del árbol
        node_width = 120
        node_height = 40
        h_spacing = 50
        v_spacing = 80
        
        # Función para dibujar un nodo
        def draw_node(parent_frame, text, x, y, width, height, is_root=False):
            color = "#4CAF50" if is_root else "#2196F3"
            node = tk.Frame(parent_frame, bg=color, bd=2, relief="raised")
            node.place(x=x, y=y, width=width, height=height)
            
            label = tk.Label(node, text=text, bg=color, fg="white", 
                           font=("Arial", 9, "bold"), wraplength=width-10)
            label.place(relx=0.5, rely=0.5, anchor="center")
            return node
        
        # Función recursiva para dibujar el árbol
        def draw_tree(parent_frame, node, x, y, level=0, parent_coords=None):
            node_text = node.data if hasattr(node, 'data') else str(node)
            current_node = draw_node(
                parent_frame, 
                node_text, 
                x, y, 
                node_width, 
                node_height,
                is_root=(level == 0)
            )
            
            current_coords = (x + node_width/2, y + node_height)
            
            # Dibujar línea al padre si no es la raíz
            if parent_coords:
                canvas.create_line(
                    parent_coords[0], parent_coords[1],
                    current_coords[0], y,
                    fill="#757575", width=2
                )
            
            # Procesar hijos
            if hasattr(node, 'children'):
                num_children = len(node.children)
                total_width = num_children * node_width + (num_children - 1) * h_spacing
                start_x = x + node_width/2 - total_width/2
                
                for i, child in enumerate(node.children):
                    child_x = start_x + i * (node_width + h_spacing)
                    child_y = y + v_spacing
                    draw_tree(
                        parent_frame, 
                        child, 
                        child_x, 
                        child_y, 
                        level + 1, 
                        current_coords
                    )
        
        # Calcular tamaño necesario
        def calculate_tree_size(node):
            if not hasattr(node, 'children') or not node.children:
                return (1, 1)
            
            width = 0
            max_depth = 0
            for child in node.children:
                child_width, child_depth = calculate_tree_size(child)
                width += child_width
                max_depth = max(max_depth, child_depth)
            
            return (max(width, len(node.children)), max_depth + 1)
        
        tree_width, tree_depth = calculate_tree_size(tree)
        required_width = tree_width * (node_width + h_spacing)
        required_height = tree_depth * (node_height + v_spacing)
        
        # Configurar el canvas
        tree_frame.config(width=max(required_width, 1000), 
                         height=max(required_height, 700))
        canvas.config(scrollregion=(0, 0, required_width, required_height))
        
        # Dibujar el árbol desde la raíz
        start_x = (required_width - node_width) / 2
        draw_tree(tree_frame, tree, start_x, 20)
        
        # Configurar el scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
    except UnexpectedInput as e:
        expected = ", ".join(e.expected) if e.expected else "nada"
        error_msg = f"Error de sintaxis en línea {e.line}:\n"
        error_msg += f"Token inesperado: '{e.token.value}' ({e.token.type})\n"
        error_msg += "Contexto:\n" + e.get_context(code)
        error_msg += f"\nEsperado: {expected}"
        messagebox.showerror("Error de Sintaxis", error_msg)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo construir el árbol: {str(e)}")



#==================== DEFINICIÓN DE TOKENS ====================

TOKENS_GRAMATICA = {
    "INT": "ENTERO",
    "FLOAT": "FLOTANTE",
    "BOOL": "BOOLEANO",
    "CHAR": "CARACTER",
    "STRING": "CADENA",
    "ARRAY": "ARREGLO",
    "STRUCT": "PALABRA RESERVADA",
    "ENUM": "PALABRA RESERVADA",
    "VOID": "PALABRA RESERVADA",
    "READ": "PALABRA RESERVADA",
    "PRINT": "PALABRA RESERVADA",
    "IF": "PALABRA RESERVADA",
    "ELSE": "PALABRA RESERVADA",
    "SWITCH": "PALABRA RESERVADA",
    "CASE": "PALABRA RESERVADA",
    "DEFAULT": "PALABRA RESERVADA",
    "BREAK": "PALABRA RESERVADA",
    "FOR": "PALABRA RESERVADA",
    "WHILE": "PALABRA RESERVADA",
    "DO": "PALABRA RESERVADA",
    "CONTINUE": "PALABRA RESERVADA",
    "RETURN": "PALABRA RESERVADA",
    "FUNC": "PALABRA RESERVADA",
    "TRY": "PALABRA RESERVADA",
    "CATCH": "PALABRA RESERVADA",
    "IMPORT": "PALABRA RESERVADA",
    "EXPORT": "PALABRA RESERVADA",
    "CONST": "PALABRA RESERVADA",
    "IDENTIFICADOR": "IDENTIFICADOR",
    "NUMBER": "NUMERO",
    "FLOAT_NUMBER": "NUMERO FLOTANTE",
    "PLUS": "MAS",
    "MINUS": "MENOS",
    "STAR": "MULTIPLICACION",
    "SLASH": "DIVISION",
    "PERCENT": "MODULO",
    "LESSTHAN": "MENOR",
    "MORETHAN": "MAYOR",
    "LESSEQUAL": "MENOR IGUAL",
    "MOREEQUAL": "MAYOR IGUAL",
    "EQUAL": "IGUAL",
    "NOTEQUAL": "DIFERENTE",
    "AND": "OPERADOR LOGICO AND",
    "OR": "OPERADOR LOGICO OR",
    "NOT": "OPERADOR LOGICO NOT",
    "ASSIGN": "ASIGNACION",
    "PLUSASSIGN": "ASIGNACION MAS",
    "MINUSASSIGN": "ASIGNACION MENOS",
    "STARASSIGN": "ASIGNACION MULTIPLICACION",
    "SLASHASSIGN": "ASIGNACION DIVISION",
    "COMENTARIO_SIMPLE": "COMENTARIO LINEA",
    "COMENTARIO_MULTILINEA": "COMENTARIO MULTILINEA",
    "LPAR": "PARENTESIS INICIO",
    "RPAR": "PARENTESIS CIERRE",
    "LBRACE": "LLAVE INICIO",
    "RBRACE": "LLAVE CIERRE",
    "SEMICOLON": "PUNTO Y COMA",
    "COLON": "DOS PUNTOS",
    "__ANON_1": "NUMERO",
    "__ANON_2": "NUMERO",
    "__ANON_6": "NUMERO",
}

# ==================== FUNCIONES DE ANÁLISIS ====================

def update_line_numbers(event=None):
    line_numbers.config(state="normal")
    line_numbers.delete(1.0, "end")  # Borrar los números anteriores
    lines = input_code.get("1.0", "end-1c").split('\n')
    line_numbers.insert("end", "\n".join(str(i) for i in range(1, len(lines)+1)))
    # line_count = int(input_code.index('end-1c').split('.')[0])  # Número de líneas del Text
    # for i in range(1, line_count + 1):
    #     line_numbers.insert("end", f"{i}\n")  # Insertar los números de línea

    line_numbers.config(state="disabled")

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
    error_manager.clear_errors()  # Limpiar errores previos
    
    console_output.insert("end", "🔍 Analizando código...\n")
    root.update()  # Actualizar la interfaz para mostrar el mensaje

    try:
        # Análisis léxico (capturar tokens para tabla de símbolos)
        tokens_lexicos = list(parser.lex(code))  # <-- Esto obtiene los tokens para la tabla
        tokens_list = [
            f"{t.line}: {TOKENS_GRAMATICA.get(t.type, t.type)}: {t.value}"
            for t in tokens_lexicos  # Usa t.line en lugar de enumerate
        ]
        
        # Análisis sintáctico
        tree = parser.parse(code)
        
        # Análisis semántico
        analizador_semantico = AnalizadorSemantico()
        # Aquí deberías recorrer el árbol sintáctico (tree) y llamar a los métodos del analizador semántico
        # según corresponda (declarar variables, funciones, verificar tipos, etc.)
        
        # Ejemplo simplificado (debes adaptarlo a tu gramática):
        for token in tokens_lexicos:
            if token.type == "INT" or token.type == "FLOAT":
                analizador_semantico.declarar_variable(token.value, token.type, token.line)
            # Añadir más casos según sea necesario
        
        # Mostrar resultados
        if analizador_semantico.errores:
            console_output.insert("end", "❌ Errores semánticos encontrados:\n")
            for error in analizador_semantico.errores:
                console_output.insert("end", f"• {error}\n")
        else:
            console_output.insert("end", "✅ Análisis completado sin errores\n")
        
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

def mostrar_error_lexico(error_msg, code):
    """Muestra errores léxicos con formato específico"""
    # Extraer línea del mensaje de error
    line_match = re.search(r'line (\d+)', error_msg)
    line = line_match.group(1) if line_match else "desconocida"
    
    # Extraer token problemático
    token_match = re.search(r"Token inesperado: '([^']+)'", error_msg)
    token = token_match.group(1) if token_match else "desconocido"
    
    console_output.insert("end", f"🚨 ERROR LÉXICO (Línea {line}):\n")
    console_output.insert("end", f"• Sujeto: '{token}'\n")
    console_output.insert("end", f"• Tipo: Símbolo no reconocido\n")
    console_output.insert("end", f"• Solución: Verificar que el símbolo sea válido\n")
    console_output.insert("end", f"\n📝 Contexto:\n{obtener_contexto(code, int(line) if line.isdigit() else 0)}\n")

def mostrar_error_sintactico(e, code):
    """Muestra errores sintácticos con formato específico"""
    expected = ", ".join(e.expected) if e.expected else "elemento no especificado"
    
    console_output.insert("end", f"🚨 ERROR SINTÁCTICO (Línea {e.line}):\n")
    console_output.insert("end", f"• Sujeto: '{e.token.value}'\n")
    console_output.insert("end", f"• Tipo: Token inesperado\n")
    console_output.insert("end", f"• Solución: Se esperaba {expected}\n")
    console_output.insert("end", f"\n📝 Contexto:\n{e.get_context(code)}\n")

def mostrar_error_general(e):
    """Muestra otros tipos de errores"""
    console_output.insert("end", f"🚨 ERROR INESPERADO:\n")
    console_output.insert("end", f"• Tipo: {type(e).__name__}\n")
    console_output.insert("end", f"• Mensaje: {str(e)}\n")
    console_output.insert("end", f"• Solución: Revisar el código para errores obvios\n")

def mostrar_advertencias(tokens):
    """Detecta y muestra posibles problemas que no son errores sintácticos"""
    warnings = []
    
    # Buscar identificadores sospechosos
    for token in tokens:
        if ": IDENTIFICADOR: " in token:
            _, _, ident = token.split(": ")
            if len(ident) > 20:
                warnings.append(f"Identificador demasiado largo: '{ident}'")
            if ident.lower() != ident and ident.upper() != ident:
                warnings.append(f"Identificador con mezcla de mayúsculas/minúsculas: '{ident}'")
    
    if warnings:
        console_output.insert("end", "\n ADVERTENCIAS:\n")
        for warn in warnings:
            console_output.insert("end", f"• {warn}\n")

def obtener_contexto(codigo, linea):
    """Obtiene las líneas alrededor del error para contexto"""
    lineas = codigo.split('\n')
    inicio = max(0, linea - 2)
    fin = min(len(lineas), linea + 2)
    
    contexto = []
    for i in range(inicio, fin):
        prefix = ">>> " if i == linea - 1 else "    "
        contexto.append(f"{i+1:4}{prefix}{lineas[i]}")
    
    return "\n".join(contexto)

def show_compiling_complete(tokens, code):
    console_output.delete("1.0", "end")
    global tokens_list
    
    if es_error(tokens):
        # Mostrar el primer error encontrado
        console_output.insert("end", tokens[0] + "\n")
    else:
        tokens_list = tokens
        console_output.insert("end", "Compilación completada.\n")
        
        # Mostrar todos los errores encontrados
        if error_manager.errors:
            console_output.insert("end", "\n=== Errores encontrados ===\n")
            console_output.insert("end", error_manager.get_all_errors_formatted())
        else:
            console_output.insert("end", "No se encontraron errores.\n")

def es_error(resultado):
    return resultado and isinstance(resultado, list) and resultado[0].startswith("Error ")

def obtener_lista_tokens(codigo):
    try:
        tokens = list(parser.lex(codigo))
        resultado = []
        
        for token in tokens:
            tipo_token = TOKENS_GRAMATICA.get(token.type, token.type)
            # Usar token.line para el número de línea real
            resultado.append(f"{token.line}: {tipo_token}: {token.value}")
            
            # Manejo especial para tokens complejos
            if token.type == "ERROR":
                handle_lexical_error(token)
                
        return resultado
        
    except UnexpectedInput as e:
        handle_syntax_error(e, codigo)
    
    # try:
    #     tokens = list(parser.lex(codigo))
    #     resultado = []
    #     sentencia_id = 1
        
    #     # Verificar tokens inválidos
    #     for i, token in enumerate(tokens):
    #         if token.type == "ERROR":
    #             error_info = error_manager.add_error(
    #                 line=token.line,
    #                 subject=token.value,
    #                 error_type="Léxico - Símbolo no reconocido",
    #                 solution="Revisar que el símbolo sea válido o esté bien escrito"
    #             )
    #             resultado.append(f"Error en línea {token.line}: Símbolo no reconocido '{token.value}'")
    #         else:
    #             tipo_token = TOKENS_GRAMATICA.get(token.type, token.type)
    #             resultado.append(f"{sentencia_id}: {tipo_token}: {token.value}")
    #             if token.type == "SEMICOLON":
    #                 sentencia_id += 1
    #             # Dentro de obtener_lista_tokens, después de procesar un token normal
    #             # Para detección de arreglos
    #             if token.type == "IDENTIFICADOR" and i+1 < len(tokens) and tokens[i+1].type == "LBRACKET":
    #                 # Buscar dimensiones del arreglo
    #                 j = i + 1
    #                 while j < len(tokens) and tokens[j].type == "LBRACKET":
    #                     j += 1  # Avanzar hasta encontrar el contenido
    #                     while j < len(tokens) and tokens[j].type != "RBRACKET":
    #                         j += 1
    #                     j += 1  # Pasar el RBRACKET
                    
    #                 # Agregar token especial para el arreglo
    #                 resultado.append(f"{token.line}: ARREGLO: {token.value}[]")

    #             # Para detección de estructuras
    #             if token.type == "STRUCT" and i+1 < len(tokens) and tokens[i+1].type == "IDENTIFICADOR":
    #                 resultado.append(f"{token.line}: STRUCT: {tokens[i+1].value}")
        
    #     return resultado
        
    # except UnexpectedInput as e:
    #     # Manejar errores sintácticos
    #     error_line = e.line
    #     error_token = e.token.value if hasattr(e, 'token') else "?"
    #     expected = ", ".join(e.expected) if e.expected else "elemento no especificado"
        
    #     error_info = error_manager.add_error(
    #         line=error_line,
    #         subject=error_token,
    #         error_type=f"Sintáctico - Token inesperado",
    #         solution=f"Se esperaba: {expected}"
    #     )
        
    #     error_msg = (
    #         f"Error en línea {error_line}: Token inesperado '{error_token}'\n"
    #         f"Contexto:\n{e.get_context(codigo)}\n"
    #         f"Se esperaba: {expected}"
    #     )
    #     return [error_msg]
    
    # except Exception as e:
    #     error_info = error_manager.add_error(
    #         line=0,
    #         subject="Desconocido",
    #         error_type="General - Error inesperado",
    #         solution="Revisar el código fuente para errores obvios"
    #     )
    #     return [f"Error en el análisis léxico: {str(e)}"]

#==================== CONFIGURACIÓN DE INTERFAZ ====================
root = tk.Tk()
root.title("Analizador Léxico")
root.geometry("1000x800")
# ------- FRAMES -------
# FRAMA PARA ICONOS

frame_superior = tk.Frame(root, bg="lightgray", height=50, bd=2, relief="sunken")
frame_superior.pack(fill="x")

frame_principal = tk.Frame(root, bg="lightgray")
frame_principal.pack(fill="both", expand=True)

# FRAME DE CÓDIGO
frame_izq = tk.Frame(frame_principal, bg="lightgray", width=550, bd=2, relief="sunken")
frame_izq.pack(side="left", fill="both", expand=True)

# FRAME DE CONSOLA DE ERRORES
frame_inferior = tk.Frame(root, bg="lightgray", height=70)
frame_inferior.pack(fill="x")

# ----- OBJETOS EN FRAMES -----
# ----- Redimensionar imagen -----
original_image = Image.open("compilar.png")  # Cargar imagen
resized_image = original_image.resize((40, 40), Image.LANCZOS)  # Redimensionar a 40x40
imagee = ImageTk.PhotoImage(resized_image)  # Convertir para Tkinter
compile_button = tk.Button(frame_superior, image=imagee, command=compile_code, width=40, height=40, bd=0)
compile_button.pack(pady=5)
symbol_table_button = tk.Button(frame_superior, text="Tabla de Simbolos", command=show_symbol_table)
symbol_table_button.pack(side="right", padx=10, pady=5)
ats_buttun = tk.Button(frame_superior, text="ATS", command=show_ats_tree)
ats_buttun.pack(side="right", padx=10, pady=5)

# Canvas para los números de línea
line_numbers = tk.Text(frame_izq, width=2, bg="lightgray", fg="black", font=("Consolas", 12), padx=5, state="disabled", wrap="none")
line_numbers.pack(side="left", fill="y")

# Entrada de código | frame izq
input_code = tk.Text(frame_izq, bg='lightgray', fg='black', font=("Consolas", 12))
input_code.pack(side="left", fill="both", expand=True)
input_code.bind("<KeyRelease>", update_line_numbers)

# Scrollbar para los números de línea
line_numbers_scrollbar = tk.Scrollbar(frame_izq, orient="vertical", command=line_numbers.yview)
line_numbers_scrollbar.pack(side="right", fill="y")
# Asociamos el scrollbar al Text widget de números de línea
line_numbers.config(yscrollcommand=line_numbers_scrollbar.set)


# Consola de errores | frame inferior
console_output = tk.Text(frame_inferior, bg='black', fg='white', font=("Consolas", 10), height=10)
console_output.pack(side="left", fill="both", expand=True)

label_error = tk.Label(frame_inferior, text="Consola de Errores", bg="black", fg="white", font=("Arial", 10))
label_error.place(x=850, y=5)

error_scrollbar = tk.Scrollbar(frame_inferior, orient="vertical" ,command=console_output.yview)
error_scrollbar.pack(side="right", fill="y")
console_output.config(yscrollcommand=error_scrollbar.set)



# ==================== MANEJO DE GRAMÁTICA ====================

def load_grammar(file_path):
    try:
        with open(file_path, "r") as file:
            grammar = file.read()
        if not grammar.strip():
            raise ValueError("El archivo de gramática está vacío")
        return grammar
    except FileNotFoundError:
        messagebox.showerror("Error", f"No se encontró el archivo de gramática: {file_path}")
        sys.exit(1)
    except Exception as e:
        messagebox.showerror("Error", f"Error al cargar gramática: {str(e)}")
        sys.exit(1)

# Cargar y validar gramática
grammar = load_grammar("Gramatica.ebnf")

try:
    parser = Lark(grammar, parser="lalr", start="start")
    print("✅ La gramática es válida y compatible con Lark")
except Exception as e:
    print("❌ Error en la gramática:", e)
    exit()

update_line_numbers()

root.mainloop()
