import tkinter as tk
from tkinter import Text, PanedWindow, Scrollbar, PhotoImage

# ----- CONFIGURACIÓN DE LA INTERFAZ -----
root = tk.Tk()
root.title("Analizador Léxico")
root.geometry("800x600")
root.configure(bg="black")

def compile_code():
    """Simulación de compilación."""
    console_output.insert("end", "Compilando...\n")

frame_superior = tk.Frame(root, bg="lightgray", width=800, height=50)
frame_superior.pack(fill="x")

frame_inferior = tk.Frame(root, bg="lightgray", width=800, height=50)
frame_inferior.pack(fill="x")


compile_image = PhotoImage(file="compilar.png")
compile_button = tk.Button(frame_superior, image=compile_image, command=compile_code, width=40, height=40)
compile_button.pack()

# Consola de errores en el frame inferior
console_output = Text(frame_inferior, bg='black', fg='white', font=("Consolas", 10), height=5)
console_output.pack(fill="both", expand=True, padx=5, pady=5)

root.mainloop()