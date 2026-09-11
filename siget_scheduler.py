from dataclasses import dataclass, field
from enum import Enum
from copy import deepcopy


# --------------------------------------------------------------------
# 1. ESTADOS DEL PROCESO
# --------------------------------------------------------------------
class Estado(Enum):
    NUEVO = "NUEVO"
    LISTO = "LISTO"
    EN_EJECUCION = "EN_EJECUCION"
    BLOQUEADO = "BLOQUEADO"
    TERMINADO = "TERMINADO"


def _validar_proceso(proceso):
    """Valida que un proceso tenga datos coherentes para la simulacion."""
    if proceso.tiempo_irrupcion < 0:
        raise ValueError(f"El proceso '{proceso.nombre}' tiene una llegada negativa.")
    if proceso.tiempo_ejecucion <= 0:
        raise ValueError(f"El proceso '{proceso.nombre}' debe ejecutar al menos 1 unidad de tiempo.")
    if not 1 <= proceso.prioridad_alerta <= 5:
        raise ValueError(
            f"La prioridad del proceso '{proceso.nombre}' debe estar entre 1 y 5. "
            f"Valor recibido: {proceso.prioridad_alerta}."
        )
    if proceso.tamano_datos < 0:
        raise ValueError(f"El proceso '{proceso.nombre}' tiene un tamaño de datos negativo.")


def _validar_lista_procesos(procesos):
    """Valida la lista de procesos antes de iniciar la simulacion."""
    if procesos is None:
        raise ValueError("La lista de procesos no puede ser None.")
    for proceso in procesos:
        _validar_proceso(proceso)


# --------------------------------------------------------------------
# 2. DEFINICION DE UN PROCESO DEL SIGET
# --------------------------------------------------------------------
@dataclass
class ProcesoSIGET:
    pid: int                     # identificador del proceso
    nombre: str                  # nombre descriptivo de la tarea
    tiempo_irrupcion: int        # instante en que el proceso llega al sistema (arrival time)
    tiempo_ejecucion: int        # tiempo total de CPU que necesita (burst time)
    prioridad_alerta: int        # 1 = maxima prioridad (emergencia), 5 = minima (rutina)
    tamano_datos: int            # tamano de datos a procesar (MB), solo informativo

    # Campos que se actualizan durante la simulacion
    tiempo_restante: int = field(init=False)
    estado: Estado = field(default=Estado.NUEVO, init=False)
    tiempo_inicio: int = field(default=None, init=False)      # primera vez que entra a ejecucion
    tiempo_finalizacion: int = field(default=None, init=False)
    historial: list = field(default_factory=list, init=False) # (tiempo, estado) para graficar

    def __post_init__(self):
        _validar_proceso(self)
        self.tiempo_restante = self.tiempo_ejecucion

    def registrar(self, t):
        """Guarda un cambio de estado con marca de tiempo, evitando duplicados seguidos."""
        if not self.historial or self.historial[-1][1] != self.estado:
            self.historial.append((t, self.estado))

    def cambiar_estado(self, nuevo_estado, t):
        self.estado = nuevo_estado
        self.registrar(t)


# --------------------------------------------------------------------
# 3. CONJUNTO DE TAREAS DE EJEMPLO DEL SIGET
# --------------------------------------------------------------------
def crear_procesos_ejemplo():
    """
    Simula 5 tareas reales del motor de procesamiento de datos de trafico:

    P1: Conteo de vehiculos en una via principal (rutina)
    P2: Alerta de choque reportada por camara (EMERGENCIA)
    P3: Actualizacion de tiempos de semaforos (rutina)
    P4: Falla de un semaforo inteligente (EMERGENCIA)
    P5: Reporte estadistico de flujo vehicular (rutina, tarea pesada)
    """
    return [
        ProcesoSIGET(pid=1, nombre="Conteo_Vehiculos_Via80",     tiempo_irrupcion=0, tiempo_ejecucion=8, prioridad_alerta=4, tamano_datos=50),
        ProcesoSIGET(pid=2, nombre="ALERTA_Choque_Camara12",     tiempo_irrupcion=1, tiempo_ejecucion=3, prioridad_alerta=1, tamano_datos=5),
        ProcesoSIGET(pid=3, nombre="Actualiza_Semaforos_Zona3",  tiempo_irrupcion=2, tiempo_ejecucion=5, prioridad_alerta=3, tamano_datos=15),
        ProcesoSIGET(pid=4, nombre="ALERTA_Semaforo_Danado",     tiempo_irrupcion=4, tiempo_ejecucion=2, prioridad_alerta=1, tamano_datos=2),
        ProcesoSIGET(pid=5, nombre="Reporte_Flujo_Vehicular",    tiempo_irrupcion=0, tiempo_ejecucion=10, prioridad_alerta=5, tamano_datos=200),
    ]


# --------------------------------------------------------------------
# 4. UTILIDADES DE IMPRESION (para ver los estados en consola)
# --------------------------------------------------------------------
def imprimir_encabezado(titulo):
    print("\n" + "=" * 78)
    print(titulo.center(78))
    print("=" * 78)


def imprimir_paso(t, ejecutando, cola_listos, procesos):
    nombre_ejec = ejecutando.nombre if ejecutando else "CPU INACTIVA (idle)"
    listos_str = ", ".join(p.nombre for p in cola_listos) if cola_listos else "-"
    print(f"t={t:>3} | Ejecutando: {nombre_ejec:<28} | Cola LISTOS: {listos_str}")


def imprimir_tabla_resultados(procesos, titulo):
    imprimir_encabezado(titulo)
    print(f"{'PID':<4}{'Proceso':<28}{'Llegada':<9}{'Ejecucion':<11}{'Prioridad':<11}{'Fin':<6}{'Retorno':<9}{'Espera':<8}")
    total_retorno, total_espera = 0, 0
    for p in procesos:
        retorno = p.tiempo_finalizacion - p.tiempo_irrupcion          # tiempo total en el sistema
        espera = retorno - p.tiempo_ejecucion                          # tiempo esperando en cola
        total_retorno += retorno
        total_espera += espera
        print(f"{p.pid:<4}{p.nombre:<28}{p.tiempo_irrupcion:<9}{p.tiempo_ejecucion:<11}"
              f"{p.prioridad_alerta:<11}{p.tiempo_finalizacion:<6}{retorno:<9}{espera:<8}")
    n = len(procesos)
    print("-" * 78)
    if n == 0:
        print("No hay procesos para calcular métricas.")
        return
    print(f"Tiempo promedio de retorno (turnaround): {total_retorno / n:.2f}")
    print(f"Tiempo promedio de espera:                {total_espera / n:.2f}")

    # Latencia de respuesta de las emergencias (prioridad_alerta == 1)
    emergencias = [p for p in procesos if p.prioridad_alerta == 1]
    if emergencias:
        print("\n--- Latencia de respuesta para EMERGENCIAS (prioridad_alerta = 1) ---")
        for p in emergencias:
            latencia = p.tiempo_inicio - p.tiempo_irrupcion
            print(f"  {p.nombre}: comenzo a ejecutarse {latencia} unidades de tiempo despues de llegar")


# --------------------------------------------------------------------
# 5. ALGORITMO 1: ROUND ROBIN (reparto equitativo)
# --------------------------------------------------------------------
def simular_round_robin(procesos_originales, quantum=3, mostrar=True):
    if quantum <= 0:
        raise ValueError("El quantum debe ser un entero positivo.")
    if procesos_originales is None:
        raise ValueError("La lista de procesos no puede ser None.")

    procesos = deepcopy(procesos_originales)
    _validar_lista_procesos(procesos)
    procesos.sort(key=lambda p: p.tiempo_irrupcion)

    t = 0
    cola = []                      # cola de LISTOS
    pendientes = list(procesos)    # aun no han "llegado" (NUEVO)
    terminados = []

    if mostrar:
        imprimir_encabezado("SIMULACION: ROUND ROBIN (quantum = %d)" % quantum)

    def encolar_nuevos_llegados(t):
        for p in list(pendientes):
            if p.tiempo_irrupcion <= t:
                p.cambiar_estado(Estado.LISTO, t)
                cola.append(p)
                pendientes.remove(p)

    encolar_nuevos_llegados(t)

    while cola or pendientes:
        if not cola:
            # CPU inactiva, avanzamos el tiempo hasta el siguiente arribo
            t = min(p.tiempo_irrupcion for p in pendientes)
            encolar_nuevos_llegados(t)
            continue

        proceso = cola.pop(0)
        if proceso.tiempo_inicio is None:
            proceso.tiempo_inicio = t
        proceso.cambiar_estado(Estado.EN_EJECUCION, t)
        if mostrar:
            imprimir_paso(t, proceso, cola + pendientes[:0], procesos)

        ejecutado = min(quantum, proceso.tiempo_restante)
        for _ in range(ejecutado):
            t += 1
            proceso.tiempo_restante -= 1
            encolar_nuevos_llegados(t)   # nuevas llegadas durante la rafaga

        if proceso.tiempo_restante == 0:
            proceso.cambiar_estado(Estado.TERMINADO, t)
            proceso.tiempo_finalizacion = t
            terminados.append(proceso)
        else:
            proceso.cambiar_estado(Estado.LISTO, t)
            cola.append(proceso)

    terminados.sort(key=lambda p: p.pid)
    if mostrar:
        imprimir_tabla_resultados(terminados, "RESULTADOS - ROUND ROBIN")
    return terminados


# --------------------------------------------------------------------
# 6. ALGORITMO 2: PRIORIDAD CON DESALOJO (preemptive priority)
#    1 = mas urgente (emergencia), 5 = menos urgente (rutina)
# --------------------------------------------------------------------
def simular_prioridad(procesos_originales, mostrar=True):
    if procesos_originales is None:
        raise ValueError("La lista de procesos no puede ser None.")

    procesos = deepcopy(procesos_originales)
    _validar_lista_procesos(procesos)
    procesos.sort(key=lambda p: p.tiempo_irrupcion)

    t = 0
    listos = []
    pendientes = list(procesos)
    terminados = []
    actual = None

    if mostrar:
        imprimir_encabezado("SIMULACION: PRIORIDAD CON DESALOJO (preemptive)")

    def encolar_nuevos_llegados(t):
        for p in list(pendientes):
            if p.tiempo_irrupcion <= t:
                p.cambiar_estado(Estado.LISTO, t)
                listos.append(p)
                pendientes.remove(p)

    encolar_nuevos_llegados(t)

    while listos or pendientes or actual:
        if not actual and not listos:
            t = min(p.tiempo_irrupcion for p in pendientes)
            encolar_nuevos_llegados(t)
            continue

        # Elegir el de mayor prioridad disponible (numero mas bajo = mas urgente)
        candidatos = listos + ([actual] if actual else [])
        siguiente = min(candidatos, key=lambda p: (p.prioridad_alerta, p.tiempo_irrupcion))

        if actual and siguiente is not actual:
            # DESALOJO: una emergencia interrumpe al proceso en ejecucion
            actual.cambiar_estado(Estado.LISTO, t)
            listos.append(actual)
            if mostrar:
                print(f"   >> DESALOJO en t={t}: '{siguiente.nombre}' (prioridad {siguiente.prioridad_alerta}) "
                      f"interrumpe a '{actual.nombre}'")
            actual = None

        if siguiente in listos:
            listos.remove(siguiente)
        actual = siguiente

        if actual.tiempo_inicio is None:
            actual.tiempo_inicio = t
        actual.cambiar_estado(Estado.EN_EJECUCION, t)
        if mostrar:
            imprimir_paso(t, actual, listos, procesos)

        # Ejecuta 1 unidad de tiempo y revisa si llego algo de mayor prioridad
        t += 1
        actual.tiempo_restante -= 1
        encolar_nuevos_llegados(t)

        if actual.tiempo_restante == 0:
            actual.cambiar_estado(Estado.TERMINADO, t)
            actual.tiempo_finalizacion = t
            terminados.append(actual)
            actual = None

    terminados.sort(key=lambda p: p.pid)
    if mostrar:
        imprimir_tabla_resultados(terminados, "RESULTADOS - PRIORIDAD CON DESALOJO")
    return terminados


# --------------------------------------------------------------------
# 7. DEMOSTRACION DE LOS 5 ESTADOS PARA UN SOLO PROCESO (didactico)
# --------------------------------------------------------------------
def demo_estados_de_un_proceso():
    imprimir_encabezado("DEMOSTRACION DE LOS ESTADOS DE UN PROCESO (P2 - Alerta de choque)")
    p = ProcesoSIGET(pid=99, nombre="ALERTA_Choque_Demo", tiempo_irrupcion=0,
                      tiempo_ejecucion=4, prioridad_alerta=1, tamano_datos=5)
    t = 0
    print(f"t={t}: el proceso se crea -> estado = {p.estado.value}")

    t = 1
    p.cambiar_estado(Estado.LISTO, t)
    print(f"t={t}: entra a la cola de listos -> estado = {p.estado.value}")

    t = 2
    p.cambiar_estado(Estado.EN_EJECUCION, t)
    print(f"t={t}: el planificador le asigna la CPU -> estado = {p.estado.value}")

    t = 4
    p.cambiar_estado(Estado.BLOQUEADO, t)
    print(f"t={t}: necesita esperar una respuesta de la base de datos de camaras -> estado = {p.estado.value}")

    t = 6
    p.cambiar_estado(Estado.LISTO, t)
    print(f"t={t}: la base de datos respondio, vuelve a la cola -> estado = {p.estado.value}")

    t = 7
    p.cambiar_estado(Estado.EN_EJECUCION, t)
    print(f"t={t}: retoma la CPU -> estado = {p.estado.value}")

    t = 9
    p.cambiar_estado(Estado.TERMINADO, t)
    print(f"t={t}: termina de procesar la alerta -> estado = {p.estado.value}")
    print("\nSecuencia completa de estados:")
    print(" -> ".join(f"[t={ti}] {est.value}" for ti, est in p.historial))


# --------------------------------------------------------------------
# 8. PROGRAMA PRINCIPAL
# --------------------------------------------------------------------
def main():
    print("#" * 78)
    print("  SIMULADOR DEL PLANIFICADOR DE CPU - SIGET".center(78))
    print("  Movilidad urbana: comparacion de algoritmos de planificacion".center(78))
    print("#" * 78)

    # 1) Mostrar los 5 estados de un proceso de forma didactica
    demo_estados_de_un_proceso()

    # 2) Crear el conjunto de tareas (procesos) del SIGET
    procesos = crear_procesos_ejemplo()

    imprimir_encabezado("TAREAS REGISTRADAS EN EL SIGET")
    for p in procesos:
        urgencia = "EMERGENCIA" if p.prioridad_alerta == 1 else "rutina"
        print(f"  PID {p.pid} | {p.nombre:<28} | llega en t={p.tiempo_irrupcion} | "
              f"dura {p.tiempo_ejecucion} | prioridad={p.prioridad_alerta} ({urgencia}) | "
              f"{p.tamano_datos} MB")

    # 3) Ejecutar los dos algoritmos de planificacion
    rr_resultado = simular_round_robin(procesos, quantum=3)
    prio_resultado = simular_prioridad(procesos)

    # 4) Comparacion final
    imprimir_encabezado("COMPARACION FINAL: ROUND ROBIN vs PRIORIDAD")
    emergencias_pids = {p.pid for p in procesos if p.prioridad_alerta == 1}

    for nombre_algo, resultado in [("Round Robin", rr_resultado), ("Prioridad", prio_resultado)]:
        n = len(resultado)
        if n == 0:
            print(f"{nombre_algo:<14} -> sin procesos ejecutados")
            continue
        espera_prom = sum((p.tiempo_finalizacion - p.tiempo_irrupcion - p.tiempo_ejecucion) for p in resultado) / n
        latencias_emergencia = [p.tiempo_inicio - p.tiempo_irrupcion for p in resultado if p.pid in emergencias_pids]
        lat_prom_emergencia = sum(latencias_emergencia) / len(latencias_emergencia) if latencias_emergencia else 0
        print(f"{nombre_algo:<14} -> espera promedio general: {espera_prom:5.2f}   "
              f"| latencia promedio en EMERGENCIAS: {lat_prom_emergencia:5.2f}")

    print("\nConclusion rapida: revisa el informe PDF adjunto para el analisis completo.")


if __name__ == "__main__":
    main()
