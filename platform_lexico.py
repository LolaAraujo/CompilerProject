# Fase 1. Analizador Léxico
# 02/24/2025
# Integrantes: Fabian Gutierrez Gachuz y Maria Dolores Cervantes Araujo

import tkinter as tk
from tkinter import Text, PanedWindow, Scrollbar, PhotoImage

# ----- FUNCIONES -----
def update_line_numbers():
    """Actualiza la numeración de líneas en el editor."""
    lines = input_code.get("1.0", "end").split("\n")  
    line_numbers.config(state="normal")
    line_numbers.delete("1.0", "end")
    line_numbers.insert("1.0", "\n".join(str(i) for i in range(1, len(lines))))
    line_numbers.config(state="disabled")

def compile_code():
    """Simulación de compilación."""
    console_output.insert("end", "Compilando...\n")

# ----- CONFIGURACIÓN DE LA INTERFAZ -----
root = tk.Tk()
root.title("Analizador Léxico")
root.geometry("800x600")
root.configure(bg="black")

# Crear el contenedor principal con PanedWindow
main_pane = PanedWindow(root, orient="horizontal")  # Permite redimensionar los paneles laterales
main_pane.pack(fill="both", expand=True)

# Crear el frame izquierdo (editor de código)
frame_izq = tk.Frame(main_pane, bg="lightblue", width=550, height=500)
main_pane.add(frame_izq)  # Añadir al PanedWindow

# Crear el frame derecho (tabla de símbolos)
frame_der = tk.Frame(main_pane, bg="lightgreen", width=250, height=500)
main_pane.add(frame_der)  # Añadir al PanedWindow

# Crear un segundo PanedWindow para la consola de errores
bottom_pane = PanedWindow(root, orient="vertical")  
bottom_pane.pack(fill="both", expand=True)

# Crear el frame inferior (consola de errores)
frame_inf = tk.Frame(bottom_pane, bg="lightgray", height=100)
bottom_pane.add(frame_inf)  # Añadir al PanedWindow

# ----- OBJETOS EN FRAMES -----

# Área para numeración de líneas
line_numbers = Text(frame_izq, width=4, bg="gray", fg="white", font=("Consolas", 12))
line_numbers.pack(side="left", fill="y")
line_numbers.insert("1.0", "1")
line_numbers.config(state="disabled")  # Para evitar edición

# Editor de código en el frame izquierdo
input_code = Text(frame_izq, bg='white', fg='black', font=("Consolas", 12))
input_code.pack(side="left", fill="both", expand=True, padx=5, pady=5)

# Scrollbar para el editor
scrollbar = Scrollbar(frame_izq, command=input_code.yview)
scrollbar.pack(side="right", fill="y")
input_code.config(yscrollcommand=scrollbar.set)

# Consola de errores en el frame inferior
console_output = Text(frame_inf, bg='black', fg='white', font=("Consolas", 10), height=5)
console_output.pack(fill="both", expand=True, padx=5, pady=5)

# ----- BOTÓN DE COMPILAR -----
compile_frame = tk.Frame(frame_der, bg="lightgreen")
compile_frame.pack(pady=20)

# Cargar imagen del botón (cambia "compile.png" por tu imagen)
compile_image = PhotoImage(file="compilar.png")  
compile_button = tk.Button(compile_frame, image=compile_image, command=compile_code)
compile_button.pack()
 
# ----- EVENTOS -----
input_code.bind("<KeyRelease>", lambda event: update_line_numbers())

# Iniciar el bucle de Tkinter
root.mainloop()


