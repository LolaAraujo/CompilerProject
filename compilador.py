import tkinter as tk
from tkinter import *
from tkinter import PanedWindow, Scrollbar, PhotoImage

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
    """Simulación de compilación."""
    console_output.insert("end", "Compilando...\n")

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

compile_image = tk.PhotoImage(file="compilar.png")
compile_button = tk.Button(frame_superior, image=compile_image, command=compile_code, width=40, height=40)
compile_button.pack()

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
label = tk.Label(frame_der, text="Tabla de Símbolos", bg="black", fg="white", font=("Arial", 12))
label.place(x=10, y=10)


# Consola de errores | frame inferior
console_output = tk.Text(frame_inferior, bg='black', fg='white', font=("Consolas", 10), height=10)
console_output.pack(side="left", fill="both", expand=True)

label_error = tk.Label(frame_inferior, text="Consola de Errores", bg="black", fg="white", font=("Arial", 10))
label_error.place(x=850, y=5)

error_scrollbar = tk.Scrollbar(frame_inferior, orient="vertical" ,command=console_output.yview)
error_scrollbar.pack(side="right", fill="y")
console_output.config(yscrollcommand=error_scrollbar.set)



update_line_numbers()

root.mainloop()