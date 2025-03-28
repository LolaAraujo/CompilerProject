# Analizador Sintáctico con Interfaz Gráfica para Compiladores
# Equipo:
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
import os
import json

tokens_list =[]

class SymbolTable:
    def __init__(self, max_memory_size=100):
        """
        Initialize the Symbol Table with memory management
        
        Args:
            max_memory_size (int): Maximum memory size in bytes for in-memory storage
        """
        # In-memory storage for symbols
        self.symbols = {}
        
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
    
    def clear(self):
        """
        Clear all symbols from memory and secondary storage
        """
        self.symbols.clear()
        
        # Clear secondary storage file
        open(self.secondary_storage_path, 'w').close()

# Modify the existing show_symbol_table function
def show_symbol_table():
    """Creates a pop-up window for the symbol table"""
    global tokens_list, symbol_table_instance
    
    if not tokens_list:
        messagebox.showinfo("Información", "No hay tokens para mostrar.")
        return
    
    pop_up = tk.Toplevel(root)
    pop_up.title("Tabla de Símbolos")
    pop_up.geometry("770x400")
    
    label = tk.Label(pop_up, text="Tabla de Símbolos", font=("Arial", 11))
    label.pack()
    
    symbol_table_popup = tk.Text(pop_up, bg='lightgray', fg='black', font=("Consolas", 10))
    symbol_table_popup.pack(expand=True, fill="both")
    
    # Headers
    headers = ["Identificador", "Categoría", "Tipo", "Ámbito", "Dirección de Memoria" ,"Línea", "Valor","Estado", "Info Estructura", "Cont. Uso"]
    header_format = "{:<20} {:<20} {:<15} {:<15} {:<10} {:<10} {:20} {:10} {:15} {:10}\n".format(*headers)
    symbol_table_popup.insert("end", header_format)
    symbol_table_popup.insert("end", "-" * 95 + "\n")
    
    # Process tokens and populate symbol table
    for token in tokens_list:
        parts = token.split(": ")
        if len(parts) == 3:
            line_number,type, details = parts[0], parts[1], parts[2]
            
            # Basic symbol details (you'll want to enhance this with more comprehensive parsing)
            symbol_details = {
                "Identificador": details,
                "Categoría": "Token",
                "Tipo": type,
                "Ámbito": "Global",
                "Dirección de Memoria": "0x0000",
                "Línea": line_number,
                "Valor": details,
                "Estado": "Declarado",
                "Info Estructura": "N/A",
                "Cont. Uso": "0"
            }
            
            # Add symbol to symbol table instance
            symbol_table_instance.add_symbol(details, symbol_details)
            
            # Format for display
            row_format = "{:<20} {:<20} {:<15} {:<15} {:<10} {:<10}\n".format(
                symbol_details["Identificador"][:20],
                symbol_details["Categoría"][:20],
                symbol_details["Tipo"][:15],
                symbol_details["Ámbito"][:15],
                symbol_details["Dirección de Memoria"][:10],
                symbol_details["Línea"][:10],
                symbol_details["Valor"][:20],
                symbol_details["Estado"][:10],
                symbol_details["Info Estructura"][:15],
                symbol_details["Cont. Uso"][:10]
            )
            symbol_table_popup.insert("end", row_format)
    
    symbol_table_popup.config(state="disabled")

symbol_table_instance = SymbolTable()

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
# valid_token_names = set(TOKENS_GRAMATICA.values())
# escaped_token_names = "|".join(map(re.escape, valid_token_names))
# regEx = re.compile(rf"^(?:{escaped_token_names}|__ANON_\d+): .+$")

# ----- CONFIGURACIÓN DE LA INTERFAZ -----
root = tk.Tk()
root.title("Analizador Léxico")
root.geometry("1000x800")
# Función para actualizar los números de línea
def update_line_numbers(event=None):
    line_numbers.config(state="normal")
    line_numbers.delete(1.0, "end")  # Borrar los números anteriores
    line_count = int(input_code.index('end-1c').split('.')[0])  # Número de líneas del Text
    for i in range(1, line_count + 1):
        line_numbers.insert("end", f"{i}\n")  # Insertar los números de línea
        
    line_numbers.config(state="disabled")

def compile_code():        
    if input_code.get("1.0", "end-1c") == "":
        console_output.delete("1.0", "end")
        console_output.insert("end", "No hay código para compilar.\n")
        # symbol_table.config(state="normal")
        # symbol_table.insert("end", "No hay símbolos.\n")
        # symbol_table.config(state="disabled")
        return
    
    console_output.delete("1.0", "end")
    # symbol_table.config(state="normal")
    # symbol_table.delete("1.0","end")
    # symbol_table.config(state="disabled")
    console_output.insert("end", "Compilando...\n")

    tokens  = obtener_lista_tokens(input_code.get("1.0", "end-1c"))
   
    root.after(2000, show_compiling_complete(tokens))  # Llamar a la función después de 2 segundos

def show_compiling_complete(tokens):
    console_output.delete("1.0", "end")
    # symbol_table.config(state="normal")
    # symbol_table.delete("1.0","end")
    # symbol_table.config(state="disabled")
    global tokens_list
    tokens_list = tokens    
    if not es_error(tokens):
        #print(tokens)
        #insert_tokens_in_symbol_table(tokens)
        console_output.insert("end","Compilacion completada. \n")
    else:
        console_output.insert("end", f"Compilación completada.\n{tokens}")

# ------- FRAMES -------
# FRAMA PARA ICONOS
frame_superior = tk.Frame(root, bg="lightgray", height=50, bd=2, relief="sunken")
frame_superior.pack(fill="x")

frame_principal = tk.Frame(root, bg="lightgray")
frame_principal.pack(fill="both", expand=True)

# FRAME DE CÓDIGO
frame_izq = tk.Frame(frame_principal, bg="lightgray", width=550, bd=2, relief="sunken")
frame_izq.pack(side="left", fill="both", expand=True)
# FRAME DE TABLA DE SÍMBOLOS
frame_der = tk.Frame(frame_principal, bg="lightgray", width=250, bd=2, relief="sunken")
frame_der.pack(side="right", fill="y")
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


# Tabla de Simbolos | frame der

# label = tk.Label(frame_der, text="Tabla de Símbolos", bg="lightgray", fg="black", font=("Arial", 11))
# label.place(x=5, y=5)
# symbol_table = tk.Text(frame_der, bg='lightgray', fg='black', font=("Consolas", 10), state="disabled")
# symbol_table.place(x=1, y=29, width=220, height=564)


# Consola de errores | frame inferior
console_output = tk.Text(frame_inferior, bg='black', fg='white', font=("Consolas", 10), height=10)
console_output.pack(side="left", fill="both", expand=True)

label_error = tk.Label(frame_inferior, text="Consola de Errores", bg="black", fg="white", font=("Arial", 10))
label_error.place(x=850, y=5)

error_scrollbar = tk.Scrollbar(frame_inferior, orient="vertical" ,command=console_output.yview)
error_scrollbar.pack(side="right", fill="y")
console_output.config(yscrollcommand=error_scrollbar.set)

with open("Gramatica.ebnf", "r") as file:
    grammar = file.read()

# Crear el parser con Lark
try:
    parser = Lark(grammar, parser="lalr", start="start")
    print("✅ La gramática es válida y compatible con Lark")
    # console_output.delete("1.0", "end")
    # console_output.insert("end", "✅ La gramática es válida y compatible con Lark")

except Exception as e:
    print("❌ Error en la gramática:")
    print(e)
    # console_output.delete("1.0", "end")
    # console_output.insert("end", f"❌ Error en la gramática: {e}")
    exit()

# def is_tokens_list(res):
#     return isinstance(res, list) and all(regEx.match(token) for token in res)

def es_error(resultado):
    return resultado and isinstance(resultado, list) and resultado[0].startswith("Error ")

# Función para obtener lista de tokens
def obtener_lista_tokens(codigo):
    try:
        tokens = list(parser.lex(codigo))
        resultado = []
        sentencia_id = 1
        for i, token in enumerate(tokens):
            tipo_token = TOKENS_GRAMATICA.get(token.type, token.type)
            resultado.append(f"{sentencia_id}: {tipo_token}: {token.value}")
            if token.type == "SEMICOLON":  # Detectar fin de sentencia
                sentencia_id += 1
        print(resultado)
        return resultado
    except UnexpectedInput as e:
        error_msg = f"Error en la línea {e.line}, columna {e.column}: \n{e.get_context(codigo)}"
        return [error_msg]
    except Exception as e:
        return [f"Error en el análisis léxico: {str(e)}"]
    

update_line_numbers()

root.mainloop()
