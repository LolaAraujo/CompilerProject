# Autores:
# Maria Dolores Cervantes Araujo
# Fabian Gutierrez Gachuz
# Fernando de Jesus Rivera Reos
# Update: 10/04/2025

import tkinter as tk
from tkinter import *
from PIL import Image, ImageTk
from lark import Lark, Tree, Token
from lark.exceptions import UnexpectedInput
import re
from tkinter import Toplevel
from tkinter import messagebox
import sys
import json
from lark.tree import pydot__tree_to_png
from collections import defaultdict


# Ejemplo de código para analizar
# func suma(int a, int b) -> int {
#     return a + b;
# }

# Variable global para almacenar tokens
tokens_list = []
global_tracker = None
parse_tree = None

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

class SymbolTracker:
    def __init__(self):
        self.declarations = {}  # {name: {line, type, scope}}
        self.usages = defaultdict(list)  # {name: [line1, line2,...]}
        self.current_scope = "global"
        self.scope_level = 0
        self.current_function = None
        self.symbols = {}
    
    def add_declaration(self, name, line, symbol_type, is_pointer=False, is_struct=False):
        name = name.replace('*', '').strip()  # Limpiar nombre si es puntero
        scope = f"{self.current_scope}:{self.scope_level}"
        if self.current_function:
            scope = f"{self.current_function}:{scope}"
            
        self.symbols[name] = {
            'type': symbol_type,
            'line': line,
            'scope': scope,
            'is_pointer': is_pointer,
            'is_struct': is_struct,
            'is_function': False
        }
    
    def add_usage(self, name, line):
        self.usages[name].append(line)
    
    def enter_scope(self):
        self.scope_level += 1
        self.current_scope = "local"
    
    def exit_scope(self):
        self.scope_level -= 1
        if self.scope_level == 0:
            self.current_scope = "global"
            self.current_function = None
    
    def set_function(self, name, line):
        self.current_function = name
        if name not in self.symbols:
            self.add_declaration(name, line, 'function')
        self.symbols[name]['is_function'] = True
        self.symbols[name]['params'] = []
        self.symbols[name]['return_type'] = 'void'
    
    def get_full_type(self, name):
        info = self.declarations.get(name, {})
        if not info:
            return "desconocido"
        
        type_str = info["type"]
        if info.get("is_pointer"):
            type_str = f"puntero a {type_str}"
        if info.get("is_struct"):
            type_str = f"estructura {type_str}"
        
        return type_str
    
    def get_scope_info(self, name):
        info = self.declarations.get(name, {})
        if not info:
            return "global:0"
        return info["scope"]
    
    def get_declaration_line(self, name):
        return self.declarations.get(name, {}).get("line", None)
    
    def get_usage_lines(self, name):
        return len(self.usages.get(name, []))
    
    def get_symbol_type(self, name):
        return self.declarations.get(name, {}).get("type", None)
    
    def get_symbol_scope(self, name):
        return self.declarations.get(name, {}).get("scope", "local")

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
        self.last_analysis = {}
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
    
    def save_analysis(self, tracker):
        """Guarda el último análisis completo"""
        self.last_analysis = {
            'symbols': tracker.symbols if hasattr(tracker, 'symbols') else {},
            'usages': tracker.usages if hasattr(tracker, 'usages') else {}
        }
        
    def get_last_analysis(self):
        """Recupera el último análisis"""
        return self.last_analysis

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
    def infer_type(self, token_type, identifier, tracker=None):        
        cache_key = f"{token_type}_{identifier}"
        if cache_key in self.type_cache:
            return self.type_cache[cache_key]
        
        # Usar información del tracker si está disponible
        if tracker and tracker.get_symbol_type(identifier):
            return tracker.get_symbol_type(identifier)
        
        
        # # Para identificadores (variables/funciones)
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
        # Buscar en tokens_list asignaciones directas (x = 5)
        for token in tokens_list:
            if f": ASIGNACION: {identifier} =" in token:
                value_part = token.split("=")[1].split(":")[0].strip()
                return value_part.replace(";", "") if ";" in value_part else value_part
        
        # Buscar inicializaciones en declaraciones (int x = 10)
        for token in tokens_list:
            if ((": INT: " in token or ": FLOAT: " in token or 
                ": BOOL: " in token or ": CHAR: " in token or 
                ": STRING: " in token) and 
                f"{identifier} =" in token):
                return token.split("=")[1].split(":")[0].strip().replace(";", "")
        
        # Para arreglos
        if any(f": ARRAY: {identifier}" in t for t in tokens_list):
            for token in tokens_list:
                if f": ARRAY: {identifier}" in token and "[" in token:
                    size = token.split("[")[1].split("]")[0]
                    return f"array[{size}]"
        
        return "No inicializado"
    
    def determine_state(self, identifier):
        declared = any(
        (f": INT: {identifier}" in token or 
         f": FLOAT: {identifier}" in token or
         f": BOOL: {identifier}" in token or
         f": CHAR: {identifier}" in token or
         f": STRING: {identifier}" in token)
        for token in tokens_list
        )
        
        initialized = any(
            f"{identifier} =" in token 
            for token in tokens_list
        )
        
        used = any(
            f": IDENTIFICADOR: {identifier}" in token 
            for token in tokens_list
        ) and not any(
            f": FUNCION: {identifier}" in token 
            for token in tokens_list
        )
        
        if not declared and used:
            return "Usado (no declarado)"
        elif declared and not initialized and not used:
            return "Declarado"
        elif declared and initialized and not used:
            return "Declarado e inicializado"
        elif declared and used:
            return "Completo (decl+init+uso)"
        else:
            return "No usado"
        
    def get_structure_info(self, identifier, token_type=None):
        # Para funciones
        for token in tokens_list:
            if f": FUNCION: {identifier}" in token:
                params = []
                if "(" in token and ")" in token:
                    params_part = token.split("(")[1].split(")")[0]
                    params = [p.split(":")[0].strip() for p in params_part.split(",") if p.strip()]
                return f"Función({len(params)} params)"
        
        # Para arreglos
        for token in tokens_list:
            if f": ARRAY: {identifier}" in token and "[" in token:
                size = token.split("[")[1].split("]")[0]
                return f"Array[{size}]"
        
        # Para estructuras
        if any(f": STRUCT: {identifier}" in t for t in tokens_list):
            fields = []
            for token in tokens_list:
                if f": STRUCT_FIELD: {identifier}." in token:
                    field = token.split(".")[1].split(":")[0]
                    fields.append(field)
            if fields:
                return f"Struct({', '.join(fields)})"
            return "Struct"
        
        return "Variable simple"

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

# const float PI = 3.1416;

# func suma(int a, int b) -> int {
#     return a + b;
# }

# func main() -> void {
#     int x = 5;
#     int y = 10;
#     int resultado;
    
#     resultado = suma(x, y);
#     print(resultado);
    
#     if (resultado > 10) {
#         float temp = resultado * PI;
#         print(temp);
#     }
# }

# ==================== VISUALIZACIONES ====================

def show_symbol_table():
    """Creates a pop-up window for the symbol table"""
    if not global_tracker or not global_tracker.symbols:  # Verifica si hay símbolos
        messagebox.showinfo("Información", "No hay datos de análisis disponibles. Compile primero.")
        return

    pop_up = tk.Toplevel(root)
    pop_up.title("Tabla de Símbolos")
    pop_up.geometry("1300x600")


    label = tk.Label(pop_up, text="Tabla de Símbolos", font=("Arial", 11))
    label.pack()

    symbol_table_popup = tk.Text(pop_up, bg='lightgray', fg='black', font=("Consolas", 10))
    symbol_table_popup.pack(expand=True, fill="both")

    # Headers
    headers = ["Identificador", "Categoría", "Tipo", "Ámbito", "Dirección" ,"Línea", "Valor","Estado", "Estructura", "Uso"]
    header_format = "{:<20} {:<20} {:<15} {:<15} {:<18} {:<12} {:20} {:20} {:20} {:10}\n".format(*headers)
    symbol_table_popup.insert("end", header_format)
    symbol_table_popup.insert("end", "-" * 170 + "\n")
    
   
    # Procesamos los símbolos del último análisis
    for identifier, symbol_info in global_tracker.symbols.items():
        # Obtener información de usos
        usage_count = len(global_tracker.usages.get(identifier, []))
        
        # Determinar categoría
        if identifier in ["main", "print", "void", "read", "func"] or symbol_info.get('is_function', False):
            category = "FUNCIÓN"
        else:
            # Buscar el tipo de token en los tokens originales si es necesario
            token_type = symbol_info.get('type', 'IDENTIFICADOR')
            category = TOKENS_GRAMATICA.get(token_type, "VARIABLE")
        
        # Obtener información de estructura si es aplicable
        structure_info = "Variable simple"
        if symbol_info.get('is_struct', False):
            structure_info = f"Estructura {symbol_info['type']}"
        elif symbol_info.get('is_pointer', False):
            structure_info = f"Puntero a {symbol_info['type']}"
        
        # Determinar estado
        state = "Declarado"
        if symbol_info.get('value') is not None:
            state = "Inicializado"
        if usage_count > 0:
            state += " + Usado"
        
        # Construir detalles del símbolo
        symbol_details = {
            "Identificador": identifier,
            "Categoría": category,
            "Tipo": symbol_info.get('type', 'desconocido'),
            "Ámbito": symbol_info.get('scope', 'global'),
            "Dirección": f"0x{abs(hash(identifier)):08X}",
            "Línea": str(symbol_info.get('line', '')),
            "Valor": symbol_info.get('value', 'No inicializado'),
            "Estado": state,
            "Estructura": structure_info,
            "Uso": str(usage_count),
        }
        
        # Mostrar en la tabla
        try: 
            row_format = "{:<20} {:<20} {:<15} {:<15} {:<18} {:<12} {:20} {:20} {:20} {:10}\n".format(
                symbol_details["Identificador"][:20],
                symbol_details["Categoría"][:20],
                symbol_details["Tipo"][:15],
                symbol_details["Ámbito"][:15],
                symbol_details["Dirección"][:18],
                symbol_details["Línea"][:12],
                str(symbol_details["Valor"])[:20],
                symbol_details["Estado"][:20],
                symbol_details["Estructura"][:20],
                symbol_details["Uso"][:10]
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

def show_identificators():
    # Obtenemos el último análisis guardado
    if not global_tracker or not global_tracker.symbols:  # Verifica si hay símbolos
        messagebox.showinfo("Información", "No hay datos de análisis disponibles. Compile primero.")
        return

    pop_up = tk.Toplevel(root)
    pop_up.title("Identificadores")
    pop_up.geometry("950x500")

    label = tk.Label(pop_up, text="Identificadores", font=("Arial", 11))
    label.pack()

    identificator_popup = tk.Text(pop_up, bg='lightgray', fg='black', font=("Consolas", 10))
    identificator_popup.pack(expand=True, fill="both")

    # Headers
    headers = ["Identificador", "Tipo", "Ambito", "Linea", "Estado", "Referencias"]
    header_format = "{:<20} {:<15} {:<20} {:<20} {:<25} {:<25}\n".format(*headers)
    identificator_popup.insert("end", header_format)
    identificator_popup.insert("end", "-" * 130 + "\n")
    
    # Procesamos los símbolos del último análisis
    for name, info in global_tracker.symbols.items():
        usage_lines = global_tracker.usages.get(name, [])
        usage_count = len(usage_lines)
        usage_info = f"{usage_count} usos" + (f" (líneas: {', '.join(map(str, usage_lines))})" if usage_lines else "")
        
        
        row_format = "{:<20} {:<25} {:<20} {:<10} {:<20} {:<20}\n".format(
            name[:20],
            info.get('type', 'desconocido')[:25],
            info.get('scope', 'global')[:20],
            str(info.get('line', ''))[:10],
            "Completo" if usage_count > 0 else "Declarado",
            usage_info[:20]
        )
        identificator_popup.insert("end", row_format)

    identificator_popup.config(state="disabled")
    
def show_variables():
    global global_tracker, tokens_list

    if not global_tracker or not global_tracker.symbols:
        messagebox.showinfo("Información", "No hay variables para mostrar. Compile primero.")
        return

    pop_up = tk.Toplevel(root)
    pop_up.title("Variables")
    pop_up.geometry("900x500")

    label = tk.Label(pop_up, text="Variables", font=("Arial", 11))
    label.pack()

    variable_popup = tk.Text(pop_up, bg='lightgray', fg='black', font=("Consolas", 10))
    variable_popup.pack(expand=True, fill="both")

    # Encabezados
    headers = [
        "Identificador", 
        "Tipo", 
        "Tamaño Memoria", 
        "Dirección Relativa", 
        "Atributos Constante", 
        "Modificabilidad"
    ]
    header_format = "{:<20} {:<15} {:<15} {:<20} {:<25} {:<20}\n".format(*headers)
    variable_popup.insert("end", header_format)
    variable_popup.insert("end", "-" * 110 + "\n")

    # Tamaños por tipo
    def get_size(var_type):
        sizes = {
            "int": 4,
            "float": 4,
            "bool": 1,
            "char": 1,
            "string": 8,
            "array": 8,
            "struct": 8
        }
        return sizes.get(var_type.lower(), 4)

    # Detección de constante usando expresiones regulares
    def get_const_info(name, var_type):
        for i in range(len(tokens_list) - 2):
            if (": CONST: const" in tokens_list[i] and
                f": {var_type.upper()}: " in tokens_list[i + 1] and
                f": IDENTIFICADOR: {name}" in tokens_list[i + 2]):
                return "Constante"
        return "No aplica"

    def get_modifiability(name, var_type, is_const, info):
        if is_const:
            return "No (const)"
        
        if info.get('is_pointer', False):
            return "No (puntero)"

        for i in range(len(tokens_list) - 1):
            if (f": IDENTIFICADOR: {name}" in tokens_list[i] and
                ": ASSIGN: =" in tokens_list[i + 1]):
                # Excluir declaración
                declared = False
                for j in range(max(i - 2, 0), i):
                    if f": {var_type.upper()}:" in tokens_list[j] or ": CONST:" in tokens_list[j]:
                        declared = True
                        break
                if not declared:
                    return "Sí"
    
        return "No (solo lectura)"

    # Mostrar cada variable
    for name, info in global_tracker.symbols.items():
        if info.get('is_function', False):
            continue
        
        var_type = info.get('type', 'desconocido')
        usage_lines = global_tracker.usages.get(name, [])

        const_value = get_const_info(name, var_type)
        is_const = const_value != "No aplica"

        modifiability = get_modifiability(name, var_type, is_const, info)
        address = f"0x{abs(hash(name)) % 65536:04X}"

        row_format = "{:<20} {:<15} {:<15} {:<20} {:<25} {:<20}\n".format(
            name[:20],
            var_type[:15],
            str(get_size(var_type))[:15],
            address[:20],
            const_value[:25],
            modifiability[:20],
        )
        variable_popup.insert("end", row_format)

    variable_popup.config(state="disabled")

def show_functions(parse_tree):
    global tokens_list, symbol_table_instance

    if not tokens_list:
        messagebox.showinfo("Información", "No hay funciones/procedimientos para mostrar.")
        return

    pop_up = tk.Toplevel(root)
    pop_up.title("Funciones y Procedimientos")
    pop_up.geometry("1150x500")
    label = tk.Label(pop_up, text="Funciones", font=("Arial", 11))
    label.pack()
    function_popup = tk.Text(pop_up, bg='lightgray', fg='black', font=("Consolas", 10))
    function_popup.pack(expand=True, fill="both")

    # Headers
    headers = ["Identificador", "Firma", "Lista de Parámetros", "Tipo de Retorno", "Variables Locales", "Estado de Implementación"]
    header_format = "{:<20} {:<30} {:<30} {:<20} {:<30} {:<25}\n".format(*headers)
    function_popup.insert("end", header_format)
    function_popup.insert("end", "-" * 155 + "\n")

    for identifier, symbol_info in global_tracker.symbols.items():
        if symbol_info.get('is_function', False):
            # Obtener firma completa
            params_str = ", ".join([param['name'] for param in symbol_info.get('params', [])])
            firma = f"{symbol_info.get('type', 'desconocido')} {identifier}({params_str})"
            
            # Lista de parámetros
            lista_parametros = ", ".join([f"{param['name']} ({param['type']}, {param['mode']})" for param in symbol_info.get('params', [])])
            
            # Tipo de retorno
            tipo_retorno = symbol_info.get('return_type', 'desconocido')
            
            # Variables locales
            variables_locales = ", ".join(symbol_info.get('local_vars', []))
            
            # Estado de implementación
            estado_implementacion = "Declarada" if symbol_info.get('declared', False) and not symbol_info.get('defined', False) else "Definida"

            row_format = "{:<20} {:<30} {:<30} {:<20} {:<30} {:<25}\n".format(
                identifier[:20],
                firma[:30],
                lista_parametros[:30],
                tipo_retorno[:20],
                variables_locales[:30],
                estado_implementacion[:25]
            )
            function_popup.insert("end", row_format)

    function_popup.config(state="disabled")




def show_definitionsUsers():
    global tokens_list, symbol_table_instance

    if not tokens_list:
        messagebox.showinfo("Información", "No hay estructuras para mostrar.")
        return

    pop_up = tk.Toplevel(root)
    pop_up.title("Estructuras")
    pop_up.geometry("1000x500")
    label = tk.Label(pop_up, text="Estructuras", font=("Arial", 11))
    label.pack()
    structure_popup = tk.Text(pop_up, bg='lightgray', fg='black', font=("Consolas", 10))
    structure_popup.pack(expand=True, fill="both")

    # Headers
    headers = ["Identificador", "Estructura Interna", "Métodos Asociados", "Herencia", "Restricciones"]
    header_format = "{:<20} {:<30} {:<30} {:<30} {:<30}\n".format(*headers)
    structure_popup.insert("end", header_format)
    structure_popup.insert("end", "-" * 140 + "\n")

    for identifier, symbol_info in global_tracker.symbols.items():
        if symbol_info.get('is_struct', False):
            # Estructura interna
            estructura_interna = ", ".join(symbol_info.get('fields', []))
            
            # Métodos asociados
            metodos_asociados = ", ".join(symbol_info.get('methods', []))
            
            # Herencia
            herencia = symbol_info.get('inheritance', 'N/A')
            
            # Restricciones
            restricciones = symbol_info.get('restrictions', 'N/A')

            row_format = "{:<20} {:<30} {:<30} {:<30} {:<30}\n".format(
                identifier[:20],
                estructura_interna[:30],
                metodos_asociados[:30],
                herencia[:30],
                restricciones[:30]
            )
            structure_popup.insert("end", row_format)

    structure_popup.config(state="disabled")


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

    line_numbers.config(state="disabled")

def compile_code():
    global tokens_list, global_tracker
    
    code = input_code.get("1.0", "end-1c").strip()
    if not code:
        console_output.delete("1.0", "end")
        console_output.insert("end", "No hay código para compilar.\n")
        return

    console_output.delete("1.0", "end")
    error_manager.clear_errors()
    
    tracker = SymbolTracker()
    global_tracker = tracker
    tokens_list = []
    
    try:
        # Análisis léxico
        lexer = parser.lex
        tokens = list(lexer(code))
        
        # Procesamiento para rastrear símbolos
        current_function = None
        brace_level = 0
        
        print("=== Tokens encontrados ===")
        for i, token in enumerate(tokens):
            token_str = f"{token.line}: {token.type}: {token.value}"
            tokens_list.append(token_str)

            # Manejo de ámbitos
            if token.type == "LBRACE":
                brace_level += 1
                tracker.enter_scope()
            elif token.type == "RBRACE":
                brace_level -= 1
                tracker.exit_scope()

            # Detección de funciones (MEJORADO++)
            if token.type == "FUNC" and i+1 < len(tokens) and tokens[i+1].type == "IDENTIFICADOR":
                func_name = tokens[i+1].value
                params = []
                return_type = "void"  # Valor por defecto si no se especifica
                local_vars = []

                # Buscar el tipo de retorno y los parámetros
                j = i + 2
                while j < len(tokens):
                    if tokens[j].type == "LPAR":
                        # Procesar parámetros
                        k = j + 1
                        while k < len(tokens) and tokens[k].type != "RPAR":
                            if tokens[k].type in ["INT", "FLOAT", "BOOL", "CHAR", "STRING", "ARRAY", "STRUCT"]:
                                param_type = tokens[k].value
                                if k+1 < len(tokens) and tokens[k+1].type == "IDENTIFICADOR":
                                    param_name = tokens[k+1].value
                                    params.append({"name": param_name, "type": param_type, "mode": "valor"})  # Asumimos modo de paso por valor
                            k += 1
                        j = k
                    elif tokens[j].type == "__ANON_11":
                        # Procesar tipo de retorno
                        if j+1 < len(tokens) and tokens[j+1].type in ["INT", "FLOAT", "BOOL", "CHAR", "STRING", "ARRAY", "STRUCT", "VOID"]:
                            return_type = tokens[j+1].value
                    elif tokens[j].type == "LBRACE":
                        # Procesar variables locales dentro del bloque de la función
                        brace_level = 1
                        k = j + 1
                        while k < len(tokens) and brace_level > 0:
                            if tokens[k].type == "LBRACE":
                                brace_level += 1
                            elif tokens[k].type == "RBRACE":
                                brace_level -= 1
                            elif tokens[k].type in ["INT", "FLOAT", "BOOL", "CHAR", "STRING", "ARRAY", "STRUCT"]:
                                var_type = tokens[k].value
                                if k+1 < len(tokens) and tokens[k+1].type == "IDENTIFICADOR":
                                    var_name = tokens[k+1].value
                                    local_vars.append(var_name)
                            k += 1
                        break
                    j += 1

                tracker.set_function(func_name, token.line)
                tracker.symbols[func_name].update({
                    "params": params,
                    "return_type": return_type,
                    "local_vars": local_vars,
                    "declared": True,
                    "defined": True  # Asumimos que la función está definida si se encuentra el bloque
                })


            # Detección de declaraciones (VERSIÓN CORREGIDA)
            if token.type in ["INT", "FLOAT", "BOOL", "CHAR", "STRING", "ARRAY", "STRUCT"]:
                # Buscar el identificador (puede estar después de =, *, etc.)
                j = i + 1
                while j < len(tokens):
                    if tokens[j].type == "IDENTIFICADOR":
                        var_name = tokens[j].value
                        is_pointer = any(tk.value == '*' for tk in tokens[i:j])
                        tracker.add_declaration(var_name, token.line, token.type, is_pointer)
                        break
                    j += 1

            # Registro de usos (VERSIÓN MEJORADA)
            if token.type == "IDENTIFICADOR":
                # Verificar que no sea parte de una declaración
                is_declaration = False
                for j in range(max(0, i-3), i):
                    if tokens[j].type in ["INT", "FLOAT", "BOOL", "CHAR", "STRING", "ARRAY", "STRUCT"]:
                        is_declaration = True
                        break
                
                if not is_declaration:
                    tracker.add_usage(token.value, token.line)
        
        # Análisis sintáctico
        parser.parse(code)
        global parse_tree  
        parse_tree = parser.parse(code)
        console_output.insert("end", "✅ Análisis completado sin errores\n")
        # pydot__tree_to_png(parse_tree, "tree.png")
        
        print("=== Símbolos registrados ===")
        print(tracker.symbols)
        print(tokens_list)
        # Guardar análisis para uso posterior
        symbol_table_instance.save_analysis({
            'symbols': tracker.symbols,
            'usages': tracker.usages,
            'tokens': tokens_list
        })
        
        show_symbol_table()
        
    except UnexpectedInput as e:
        mostrar_error_sintactico(e, code)
    except Exception as e:
        console_output.insert("end", f"Error inesperado: {str(e)}\n")
        import traceback
        traceback.print_exc()

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
identificator_button = tk.Button(frame_superior, text="Identificadores", command=show_identificators)
identificator_button.pack(side="right", padx=10, pady=5)
variables_button = tk.Button(frame_superior, text="Variables", command=show_variables)
variables_button.pack(side="right", padx=10, pady=5)
functions_button = tk.Button(frame_superior, text="Funciones/Procedimientos", command=lambda: show_functions(parse_tree))
functions_button.pack(side="right", padx=10, pady=5)
definitionUsers_button = tk.Button(frame_superior, text="Definiciones por Usuario", command=show_definitionsUsers)
definitionUsers_button.pack(side="right", padx=10, pady=5)

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