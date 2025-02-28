# Fase 1. Analizador Léxico
# 02/24/2025
# Integrantes: Fabian Gutierrez Gachuz y Maria Dolores Cervantes Araujo

import tkinter as tk
from tkinter import *
from tkinter import messagebox

# ----- CONFIGURACIÓN DE LA INTERFAZ -----
root = tk.Tk()
root.title("Analizador Léxico")
root.geometry("800x600")
root.configure(bg = 'black')

# Configurar la cuadrícula principal
root.columnconfigure(0, weight=2)
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=3)  # Parte superior (Frames izquierdo y derecho)
root.rowconfigure(1, weight=1)  # Parte inferior (Frame que abarca ambos)

# Crear los frames
frame_izq = tk.Frame(root, bg="lightblue")
frame_der = tk.Frame(root, bg="lightgreen")
frame_inf = tk.Frame(root, bg="lightgray")

# Ubicar los frames en la cuadrícula
frame_izq.grid(row=0, column=0, sticky="nsew")
frame_der.grid(row=0, column=1, sticky="nsew")
frame_inf.grid(row=1, column=0, columnspan=2, sticky="nsew")  # Se extiende en ambas columnas


# ----- OBJETOS EN FRAMES -----
input_code = Text(frame_izq, bg='white', fg='black')
input_code.pack()
input_code.place(x=00, y=-50)


# Iniciar el bucle de Tkinter
root.mainloop()



