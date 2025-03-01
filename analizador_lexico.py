import tkinter as tk
from tkinter import *
from PIL import Image, ImageTk 
from lark import Lark
from lark.exceptions import UnexpectedInput
import re 

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
root.resizable(False, False)

# Función para actualizar los números de línea
def update_line_numbers(event=None):
    line_numbers.config(state="normal")
    line_numbers.delete(1.0, "end")  # Borrar los números anteriores
    line_count = int(input_code.index('end-1c').split('.')[0])  # Número de líneas del Text
    for i in range(1, line_count + 1):
        line_numbers.insert("end", f"{i}\n")  # Insertar los números de línea

def compile_code():        
    if input_code.get("1.0", "end-1c") == "":
        console_output.insert("end", "No hay código para compilar.\n")
        symbol_table.insert("end", "No hay símbolos.\n")
        return
    
    console_output.delete("1.0", "end")
    symbol_table.delete("1.0", "end")
    console_output.insert("end", "Compilando...\n")

    tokens  = obtener_lista_tokens(input_code.get("1.0", "end-1c"))
   
    root.after(2000, show_compiling_complete(tokens))  # Llamar a la función después de 2 segundos

def show_compiling_complete(tokens):
    console_output.delete("1.0", "end")
    symbol_table.delete("1.0","end")
    if not es_error(tokens):
        #print(tokens)
        insert_tokens_in_symbol_table(tokens)
        console_output.insert("end","Compilacion completada. \n")
    else:
        console_output.insert("end", f"Compilación completada.\n{tokens}")

def insert_tokens_in_symbol_table(tokens):
    """Inserta Los tokens en la tabla de manera formateada"""
    symbol_table.config(state="normal") 
    symbol_table.delete("1.0", "end") 

    #definicion de parametros
    column_width = 20  
    formatted_tokens = ""

    for token in tokens:
        token_type, token_value = token.split(": ", 1)  # Dividir los tokens por tipo y valor
        formatted_tokens += f"{token_type.ljust(column_width)}{token_value}\n"

    symbol_table.insert("end", formatted_tokens)
    symbol_table.config(state="disabled")

# ------- FRAMES -------
# FRAMA PARA ICONOS
frame_superior = tk.Frame(root, bg="black", height=50, bd=2, relief="sunken")
frame_superior.pack(fill="x")

frame_principal = tk.Frame(root, bg="black")
frame_principal.pack(fill="both", expand=True)

# FRAME DE CÓDIGO
frame_izq = tk.Frame(frame_principal, bg="black", width=550, bd=2, relief="sunken")
frame_izq.pack(side="left", fill="both", expand=True)
# FRAME DE TABLA DE SÍMBOLOS
frame_der = tk.Frame(frame_principal, bg="black", width=250, bd=2, relief="sunken")
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

# Canvas para los números de línea
line_numbers = tk.Text(frame_izq, width=2, bg="black", fg="white", font=("Consolas", 12), padx=5, state="disabled", wrap="none")
line_numbers.pack(side="left", fill="y")

# Entrada de código | frame izq
input_code = tk.Text(frame_izq, bg='black', fg='white', font=("Consolas", 12))
input_code.pack(side="left", fill="both", expand=True)
input_code.bind("<KeyRelease>", update_line_numbers)

# Scrollbar para los números de línea
line_numbers_scrollbar = tk.Scrollbar(frame_izq, orient="vertical", command=line_numbers.yview)
line_numbers_scrollbar.pack(side="right", fill="y")
# Asociamos el scrollbar al Text widget de números de línea
line_numbers.config(yscrollcommand=line_numbers_scrollbar.set)


# Tabla de Simbolos | frame der
label = tk.Label(frame_der, text="Tabla de Símbolos", bg="black", fg="white", font=("Arial", 11))
label.place(x=5, y=5)
symbol_table = tk.Text(frame_der, bg='black', fg='white', font=("Consolas", 10))
symbol_table.place(x=1, y=29, width=220, height=564)


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
    console_output.delete("1.0", "end")
    console_output.insert("end", "✅ La gramática es válida y compatible con Lark")

except Exception as e:
    print("❌ Error en la gramática:")
    print(e)
    console_output.delete("1.0", "end")
    console_output.insert("end", f"❌ Error en la gramática: {e}")
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
            resultado.append(f"{sentencia_id}.{i+1} {tipo_token}: {token.value}")
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
