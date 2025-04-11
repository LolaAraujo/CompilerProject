class TablaSimbolos:
    def __init__(self):
        self.ambitos = [{}]

    def entrar_ambito(self):
        self.ambitos.append({})

    def salir_ambito(self):
        self.ambitos.pop()

    def declarar(self, nombre, tipo, linea, constante=False):
        ambito_actual = self.ambitos[-1]
        if nombre in ambito_actual:
            return error_manager.add_error(
                line=linea,
                subject=nombre,
                error_type="Semántico - Redefinición de variable",
                solution="Renombrar la variable o usar otra variable diferente en este ámbito"
            )
        for ambito in reversed(self.ambitos[:-1]):
            if nombre in ambito:
                return error_manager.add_error(
                    line=linea,
                    subject=nombre,
                    error_type="Semántico - Ocultamiento de variable",
                    solution="Evitar declarar una variable con el mismo nombre de una del ámbito superior"
                )
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
        self.codigo_inalcanzable = False

    def declarar_variable(self, nombre, tipo, linea, constante=False):
        error = self.tabla.declarar(nombre, tipo, linea, constante)
        if error:
            self.errores.append(error)

    def asignar_variable(self, nombre, tipo_valor, linea):
        simbolo = self.tabla.obtener(nombre)
        if not simbolo:
            self.errores.append(error_manager.add_error(
                line=linea,
                subject=nombre,
                error_type="Semántico - Variable no declarada",
                solution="Declarar la variable antes de asignarle un valor"
            ))
        elif not simbolo["modificable"]:
            self.errores.append(error_manager.add_error(
                line=linea,
                subject=nombre,
                error_type="Semántico - Modificación de constante",
                solution="No se puede modificar una constante, usar una variable"
            ))
        elif simbolo["tipo"] != tipo_valor:
            self.errores.append(error_manager.add_error(
                line=linea,
                subject=nombre,
                error_type="Semántico - Asignación de tipo incorrecto",
                solution=f"Se esperaba tipo '{simbolo['tipo']}' pero se intentó asignar '{tipo_valor}'"
            ))
        else:
            simbolo["inicializado"] = True

    def usar_variable(self, nombre, linea):
        simbolo = self.tabla.obtener(nombre)
        if not simbolo:
            self.errores.append(error_manager.add_error(
                line=linea,
                subject=nombre,
                error_type="Semántico - Variable no declarada",
                solution="Declarar la variable antes de usarla"
            ))
        else:
            simbolo["referencias"] += 1
            if not simbolo["inicializado"]:
                self.errores.append(error_manager.add_error(
                    line=linea,
                    subject=nombre,
                    error_type="Semántico - Uso sin inicialización",
                    solution="Inicializar la variable antes de utilizarla"
                ))

    def declarar_funcion(self, nombre, parametros, tipo_retorno, linea):
        if nombre in self.funciones:
            self.errores.append(error_manager.add_error(
                line=linea,
                subject=nombre,
                error_type="Semántico - Función ya definida",
                solution="Renombrar la función o evitar redefinirla"
            ))
        else:
            self.funciones[nombre] = {
                "parametros": parametros,
                "retorno": tipo_retorno,
                "linea": linea,
                "tiene_retorno": False,
                "tiene_caso_base": False
            }

    def entrar_funcion(self, nombre):
        self.funcion_actual = self.funciones[nombre]
        self.tabla.entrar_ambito()
        for tipo, nombre_param in self.funcion_actual["parametros"]:
            self.tabla.declarar(nombre_param, tipo, self.funcion_actual["linea"])

    def salir_funcion(self):
        if self.funcion_actual["retorno"] != "void" and not self.funcion_actual["tiene_retorno"]:
            self.errores.append(error_manager.add_error(
                line=self.funcion_actual["linea"],
                subject=self.funcion_actual,
                error_type="Semántico - Falta de return",
                solution="Agregar una sentencia return para retornar el valor requerido"
            ))
        if self.funcion_actual["retorno"] != "void" and not self.funcion_actual["tiene_caso_base"]:
            self.errores.append(error_manager.add_error(
                line=self.funcion_actual["linea"],
                subject=self.funcion_actual,
                error_type="Advertencia - Recursión sin caso base",
                solution="Agregar un caso base para evitar recursión infinita"
            ))
        self.funcion_actual = None
        self.tabla.salir_ambito()

    def llamada_funcion(self, nombre, argumentos, linea):
        if nombre not in self.funciones:
            self.errores.append(error_manager.add_error(
                line=linea,
                subject=nombre,
                error_type="Semántico - Llamada a función indefinida",
                solution="Definir la función antes de llamarla"
            ))
        else:
            f = self.funciones[nombre]
            if len(argumentos) != len(f["parametros"]):
                self.errores.append(error_manager.add_error(
                    line=linea,
                    subject=nombre,
                    error_type="Semántico - Cantidad incorrecta de argumentos",
                    solution=f"La función espera {len(f['parametros'])} argumentos"
                ))
            else:
                for (arg_tipo, (param_tipo, _)) in zip(argumentos, f["parametros"]):
                    if arg_tipo != param_tipo:
                        self.errores.append(error_manager.add_error(
                            line=linea,
                            subject=nombre,
                            error_type="Semántico - Tipo incorrecto de argumento",
                            solution=f"Se esperaba '{param_tipo}' pero se recibió '{arg_tipo}'"
                        ))

    def retorno_funcion(self, tipo_retorno, linea):
        if not self.funcion_actual:
            self.errores.append(error_manager.add_error(
                line=linea,
                subject="return",
                error_type="Semántico - Return fuera de función",
                solution="Solo se puede usar return dentro de funciones"
            ))
        elif tipo_retorno != self.funcion_actual["retorno"]:
            self.errores.append(error_manager.add_error(
                line=linea,
                subject="return",
                error_type="Semántico - Tipo de retorno incorrecto",
                solution=f"Se esperaba retornar '{self.funcion_actual['retorno']}' pero se retornó '{tipo_retorno}'"
            ))
        else:
            self.funcion_actual["tiene_retorno"] = True

    def registrar_llamada_en_funcion(self, nombre_funcion_llamada, linea):
        if self.funcion_actual and nombre_funcion_llamada == self.funcion_actual:
            if not self.funcion_actual.get("tiene_caso_base", False):
                self.errores.append(error_manager.add_error(
                    line=linea,
                    subject=nombre_funcion_llamada,
                    error_type="Advertencia - Recursión sin caso base",
                    solution="Agregar un caso base para evitar recursión infinita"
                ))

    def registrar_caso_base(self):
        if self.funcion_actual:
            self.funcion_actual["tiene_caso_base"] = True

    def verificar_division(self, operando_derecho, linea):
        if isinstance(operando_derecho, (int, float)) and operando_derecho == 0:
            self.errores.append(error_manager.add_error(
                line=linea,
                subject="/",
                error_type="Semántico - División por cero",
                solution="Evitar dividir entre cero"
            ))

    def acceso_array(self, nombre, indice, longitud, linea):
        if isinstance(indice, int) and (indice < 0 or indice >= longitud):
            self.errores.append(error_manager.add_error(
                line=linea,
                subject=nombre,
                error_type="Semántico - Índice fuera de rango",
                solution=f"Índice debe estar entre 0 y {longitud - 1}"
            ))

    def operacion_binaria(self, tipo1, tipo2, operador, linea):
        compatibles = {
            '+': [('int', 'int'), ('float', 'float'), ('int', 'float'), ('float', 'int'), ('string', 'string')],
            '-': [('int', 'int'), ('float', 'float'), ('int', 'float'), ('float', 'int')],
            '*': [('int', 'int'), ('float', 'float'), ('int', 'float'), ('float', 'int')],
            '/': [('int', 'int'), ('float', 'float'), ('int', 'float'), ('float', 'int')],
            '%': [('int', 'int')],
        }
        if (tipo1, tipo2) not in compatibles.get(operador, []):
            self.errores.append(error_manager.add_error(
                line=linea,
                subject=operador,
                error_type="Semántico - Tipos incompatibles en operación binaria",
                solution=f"No se puede usar '{operador}' entre '{tipo1}' y '{tipo2}'"
            ))

    def analizar_sentencia(self, tipo_sentencia, linea):
        if tipo_sentencia in ["return", "break", "continue"]:
            self.codigo_inalcanzable = True
        elif self.codigo_inalcanzable:
            self.errores.append(error_manager.add_error(
                line=linea,
                subject=tipo_sentencia,
                error_type="Advertencia - Código inalcanzable",
                solution="Mover esta instrucción fuera del bloque inalcanzable"
            ))

    def reiniciar_codigo_inalcanzable(self):
        self.codigo_inalcanzable = False
