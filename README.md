# Simulador del Planificador de CPU - SIGET

Simulador que representa el motor de procesamiento de datos del **SIGET**
(Sistema Integrado de Gestión del Tráfico), implementando y comparando dos
algoritmos de planificación de procesos: **Round Robin** y **Prioridad con
desalojo (preemptive)**.

El objetivo es analizar qué algoritmo ofrece el mejor equilibrio entre la
latencia de respuesta ante eventos críticos de tráfico (choques, fallas de
semáforos) y la eficiencia general en el procesamiento de un alto volumen de
datos de tráfico rutinarios.

## 📂 Material completo (código, informe y video)

Todo el material de esta entrega está disponible en la siguiente carpeta de
Google Drive, incluyendo el **video de evidencia de ejecución**, el
**código fuente (.py)** y el **informe técnico (.pdf)**:

🔗 **[Ver carpeta completa en Google Drive](https://drive.google.com/drive/folders/15cIp3ayIlsGQJRd9wsQMS3DhGoyiXjjz?usp=sharing)**

## 📄 Archivos en este repositorio

- `siget_scheduler.py` — Código fuente del simulador (Python).
- `informe_siget.pdf` — Relatoría técnica (objetivos, algoritmos, resultados y conclusiones).

## ⚙️ Cómo ejecutar el simulador

Se necesita tener Python 3 instalado. Luego, desde la terminal:

```bash
python3 siget_scheduler.py
```

## 🧩 ¿Qué hace el simulador?

- Representa **5 procesos** del SIGET con atributos realistas: tiempo de
  llegada, tiempo de ejecución, prioridad de alerta (1 = emergencia,
  5 = rutina) y tamaño de datos a procesar (MB).
- Muestra los **5 estados clásicos de un proceso**: `NUEVO`, `LISTO`,
  `EN_EJECUCION`, `BLOQUEADO` y `TERMINADO`, con una demostración paso a paso.
- Implementa dos algoritmos de planificación:
  - **Round Robin (quantum = 3):** reparto equitativo del tiempo de CPU,
    ideal para tareas de rutina.
  - **Prioridad con desalojo:** da respuesta inmediata a emergencias,
    interrumpiendo la tarea en curso cuando llega una alerta más urgente.
- Al final, compara ambos algoritmos según: tiempo de espera promedio y
  latencia de respuesta ante emergencias.

## 📊 Resultados obtenidos

| Algoritmo | Espera promedio | Latencia promedio en emergencias |
|---|---|---|
| Round Robin (q=3) | 13.00 | 8.00 |
| Prioridad con desalojo | 6.40 | 0.00 |

## ✅ Conclusión

Prioridad con desalojo es el algoritmo más adecuado para dar respuesta
inmediata a emergencias de tráfico, mientras que Round Robin es más
equitativo para tareas rutinarias. Para el SIGET se recomienda un esquema
híbrido: prioridad para emergencias, combinado con Round Robin para el resto
de las tareas. El detalle completo del análisis está en `informe_siget.pdf`.
