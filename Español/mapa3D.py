import matplotlib.pyplot as plt
import numpy as np
import re
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D
import os

# Configuración inicial
ruta_archivo = r"C:\Users\pato\Desktop\scripts\Logs\telemetriagta5.txt"

# Diccionarios para almacenar datos
sesiones = {}
circuito_por_sesion = {}
ultima_posicion_raton = None
modo_rotacion = False

# Expresiones regulares
patron_inicio_sesion = re.compile(r"=== Telemetría iniciada (.+?) (.+?) (.+?) ===")
patron_posicion = re.compile(r"Posición: \((-?\d+[\.,]?\d*), (-?\d+[\.,]?\d*), (-?\d+[\.,]?\d*)\)")
patron_circuito = re.compile(r"Circuito: (.+?) \| Vuelta:")
patron_vuelta = re.compile(r"Vuelta: (\d+)")

# Función para limpiar la última línea si es un registro de inicio
def limpiar_ultima_linea_si_registro(ruta_archivo, inicio_registro):
    if os.path.exists(ruta_archivo) and os.path.getsize(ruta_archivo) > 0:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            lineas = f.readlines()
        if lineas and lineas[-1].startswith(inicio_registro):
            lineas.pop()
            # Si la nueva última línea está en blanco, eliminarla también
            if lineas and lineas[-1].strip() == "":
                lineas.pop()
            with open(ruta_archivo, "w", encoding="utf-8") as f:
                f.writelines(lineas)

# Limpiar archivos si es necesario
limpiar_ultima_linea_si_registro(ruta_archivo, "=== Telemetría iniciada")

# Procesar archivo
sesion_actual = None
vuelta_actual = 0

with open(ruta_archivo, "r", encoding="utf-8") as archivo:
    for linea in archivo:
        coincidencia_sesion = patron_inicio_sesion.search(linea)
        if coincidencia_sesion:
            fecha_sesion = coincidencia_sesion.group(1).strip()
            hora_sesion = coincidencia_sesion.group(2).strip()
            circuito = coincidencia_sesion.group(3).strip()
            sesion_actual = f"{fecha_sesion} {hora_sesion}"
            if sesion_actual not in sesiones:
                sesiones[sesion_actual] = {}
                circuito_por_sesion[sesion_actual] = circuito
            continue

        if sesion_actual is None:
            continue

        coincidencia_circuito = patron_circuito.search(linea)
        if coincidencia_circuito:
            circuito_por_sesion[sesion_actual] = coincidencia_circuito.group(1).strip()

        coincidencia_vuelta = patron_vuelta.search(linea)
        if coincidencia_vuelta:
            vuelta_actual = int(coincidencia_vuelta.group(1))
            if vuelta_actual not in sesiones[sesion_actual]:
                sesiones[sesion_actual][vuelta_actual] = {'x': [], 'y': [], 'z': []}

        coincidencia_posicion = patron_posicion.search(linea)
        if coincidencia_posicion and vuelta_actual > 0:
            x, y, z = coincidencia_posicion.groups()
            x, y, z = x.replace(",", "."), y.replace(",", "."), z.replace(",", ".")
            sesiones[sesion_actual][vuelta_actual]['x'].append(float(x))
            sesiones[sesion_actual][vuelta_actual]['y'].append(float(y))
            sesiones[sesion_actual][vuelta_actual]['z'].append(float(z))

# Función para actualizar el gráfico
def actualizar_grafica(event=None):
    ax.cla()
    cadena_sesion = combo_sesiones.get()
    sesion = cadena_sesion.split(" - ")[0]  # Solo la fecha y hora
    
    if sesion in sesiones:
        vueltas = sesiones[sesion]
        colores = plt.cm.viridis(np.linspace(0, 1, len(vueltas)))
        
        # Primero recolectamos todos los puntos para calcular los rangos
        todos_x, todos_y, todos_z = [], [], []
        for vuelta, coordenadas in vueltas.items():
            if coordenadas['x']:
                todos_x.extend(coordenadas['x'])
                todos_y.extend(coordenadas['y'])
                todos_z.extend(coordenadas['z'])
        
        if not todos_x:
            return
            
        # Calculamos los rangos de cada eje
        rango_x = max(todos_x) - min(todos_x)
        rango_y = max(todos_y) - min(todos_y)
        rango_z = max(todos_z) - min(todos_z)
        
        # Ajustamos la relación de aspecto basada en los rangos reales
        relacion_aspecto = [rango_x, rango_y, rango_z * 0.2]  # Reducimos la importancia del eje Z
        ax.set_box_aspect(relacion_aspecto)
        
        # Dibujamos las vueltas
        for indice, (vuelta, coordenadas) in enumerate(vueltas.items()):
            if coordenadas['x']:
                x = np.array(coordenadas['x'])
                y = np.array(coordenadas['y'])
                z = np.array(coordenadas['z'])
                ax.plot(x, y, z, color=colores[indice], alpha=0.7, linewidth=2,
                      label=f"Vuelta {vuelta}")
        
        # Configuración del gráfico
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_zticks([])
        ax.grid(False)
        
        # Ajustamos la vista para mejor perspectiva
        ax.view_init(elev=30, azim=45)  # Ángulo de visualización
        
        for eje in [ax.xaxis, ax.yaxis, ax.zaxis]:
            eje.pane.fill = False
            eje.line.set_color((0.0, 0.0, 0.0, 0.0))
        
        if sesion in circuito_por_sesion:
            ax.set_title(f"Circuito: {circuito_por_sesion[sesion]}\nSesión: {sesion}", pad=20)
        
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        lienzo.draw()

# Función para manejar el zoom con la rueda del ratón
def zoom(evento):
    if evento.delta > 0 or evento.num == 4:
        escala = 0.9  # Acercar
    else:
        escala = 1.1  # Alejar

    # Obtener límites actuales
    limites_x = ax.get_xlim3d()
    limites_y = ax.get_ylim3d()
    limites_z = ax.get_zlim3d()

    def escalar(limites):
        medio = (limites[0] + limites[1]) / 2
        rango = (limites[1] - limites[0]) * escala / 2
        return (medio - rango, medio + rango)

    ax.set_xlim3d(escalar(limites_x))
    ax.set_ylim3d(escalar(limites_y))
    ax.set_zlim3d(escalar(limites_z))

    lienzo.draw()

# Crear interfaz gráfica
raiz = tk.Tk()
raiz.title("Visualización 3D de Telemetría")
raiz.geometry("1000x800")

# Marco de controles
marco_controles = tk.Frame(raiz)
marco_controles.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

# Selector de sesión
tk.Label(marco_controles, text="Sesión:").pack(side=tk.LEFT)
sesiones_formateadas = [f"{sesion} - {circuito_por_sesion.get(sesion, 'Circuito Desconocido')}" for sesion in sorted(sesiones.keys(), reverse=True)]
combo_sesiones = ttk.Combobox(marco_controles, values=sesiones_formateadas, width=50)
combo_sesiones.pack(side=tk.LEFT, padx=5)
combo_sesiones.bind("<<ComboboxSelected>>", actualizar_grafica)

# Botones de control
tk.Button(marco_controles, text="Reset Zoom", command=actualizar_grafica).pack(side=tk.LEFT, padx=5)

# Marco del gráfico
marco_grafico = tk.Frame(raiz)
marco_grafico.pack(fill=tk.BOTH, expand=True)

# Crear figura 3D
figura = plt.figure(figsize=(8, 10))
ax = figura.add_subplot(111, projection='3d')

# Configuración inicial del gráfico
ax.set_xticks([])
ax.set_yticks([])
ax.set_zticks([])
ax.grid(False)
ax.set_title("Seleccione una sesión", pad=20)

for eje in [ax.xaxis, ax.yaxis, ax.zaxis]:
    eje.pane.fill = False
    eje.line.set_color((0.0, 0.0, 0.0, 0.0))

# Ajustar la relación de aspecto del gráfico
ax.set_box_aspect([1, 1, 0.1])

# Lienzo para el gráfico
lienzo = FigureCanvasTkAgg(figura, master=marco_grafico)
lienzo.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Asociar eventos de scroll
lienzo.get_tk_widget().bind("<MouseWheel>", zoom)

# Seleccionar última sesión por defecto si existe
if sesiones_formateadas:
    combo_sesiones.set(sesiones_formateadas[0])
    actualizar_grafica()

# Función para cerrar la consola
def cerrar_programa():
    print("Cerrando programa...")
    raiz.destroy()
    # Cerrar el intérprete de Python
    exit()

raiz.protocol("WM_DELETE_WINDOW", cerrar_programa)

raiz.mainloop()