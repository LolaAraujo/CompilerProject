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
            print("✅ Programa válido (análisis semántico sin errores).")
        else:
            print("🔍 Errores semánticos detectados:\n")
            for i, error in enumerate(self.errores, start=1):
                print(f"**ERROR {i}:** {error}")


# === Ejemplo de uso manual ===
if __name__ == "__main__":
    sem = AnalizadorSemantico()

    # Simulación de código fuente parseado:
    # Línea 1: int x;
    sem.declarar_variable("x", "int", 1)

    # Línea 2: x = 5;
    sem.asignar_variable("x", "int", 2)

    # Línea 3: imprimir x;
    sem.usar_variable("x", 3)

    # Línea 4: y = 10; (uso sin declarar)
    sem.asignar_variable("y", "int", 4)

    # Línea 5: const float pi = 3.14;
    sem.declarar_variable("pi", "float", 5, constante=True)
    sem.asignar_variable("pi", "float", 6)  # reasignación indebida

    # Línea 7: z; (uso sin inicializar)
    sem.declarar_variable("z", "int", 7)
    sem.usar_variable("z", 8)

    # Línea 9: x = "hola"; (error de tipo)
    sem.asignar_variable("x", "string", 9)

    # Reporte final
    sem.reportar_errores()
