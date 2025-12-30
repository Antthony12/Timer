import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter
import tkinter as tk
from tkinter import ttk
import re
from datetime import datetime
import mplcursors
import numpy as np
import os

# Ruta del archivo
ruta_archivo = r"C:\Users\pato\Desktop\scripts\Logs\telemetriagta5.log"
ruta_exportaciones = r"C:\Users\pato\Desktop\scripts\Logs\Exportaciones"

# Listas para almacenar datos
marcas_tiempo = []
velocidades = []
frenos = []
rpms = []
marchas = []
vueltas = []  # Lista de vueltas registradas
datos_vuelta = {}  # Diccionario para almacenar datos por vuelta
circuito = "Circuito Desconocido"  # Valor por defecto

# Diccionario para almacenar sesiones
sesiones = {}
sesion_actual = None
circuito_por_sesion = {}  # Almacenar circuito por sesión

# Expresiones regulares para extraer datos
patron_tiempo = re.compile(r"Fecha: (\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}\.\d{3})")
patron_velocidad = re.compile(r"Velocidad: ([\d,]+) km/h")
patron_freno = re.compile(r"Freno: ([\d,]+)%")
patron_rpm = re.compile(r"RPM: ([\d,]+)")
patron_marcha = re.compile(r"Marcha: (\d+)")
patron_vuelta = re.compile(r"Vuelta: (\d+)")
patron_circuito = re.compile(r"Circuito: (.+?) \| Vuelta:")
patron_posicion = re.compile(r"Posición: \(([\d,-]+), ([\d,-]+), ([\d,-]+)\)")
patron_inicio_sesion = re.compile(r"=== Telemetría iniciada (.+?) (.+?) (.+?) ===")

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

# Leer y procesar el archivo
with open(ruta_archivo, "r", encoding="utf-8") as archivo:
    for linea in archivo:
        # Buscar inicio de sesión
        coincidencia_sesion = patron_inicio_sesion.search(linea)
        if coincidencia_sesion:
            fecha_sesion = coincidencia_sesion.group(1).strip()  # Fecha
            hora_sesion = coincidencia_sesion.group(2).strip()  # Hora
            circuito = coincidencia_sesion.group(3).strip()      # Circuito
            sesion_actual = f"{fecha_sesion} {hora_sesion}"  # Combina fecha y hora
            if sesion_actual not in sesiones:
                sesiones[sesion_actual] = {}
                circuito_por_sesion[sesion_actual] = circuito
            continue

        # Si no estamos en ninguna sesión, saltar
        if sesion_actual is None:
            continue

        # Buscar el nombre del circuito
        coincidencia_circuito = patron_circuito.search(linea)
        if coincidencia_circuito:
            circuito_por_sesion[sesion_actual] = coincidencia_circuito.group(1).strip()

        coincidencia_tiempo = patron_tiempo.search(linea)
        coincidencia_velocidad = patron_velocidad.search(linea)
        coincidencia_freno = patron_freno.search(linea)
        coincidencia_rpm = patron_rpm.search(linea)
        coincidencia_marcha = patron_marcha.search(linea)
        coincidencia_vuelta = patron_vuelta.search(linea)
        coincidencia_posicion = patron_posicion.search(linea)

        if coincidencia_tiempo:
            marca_tiempo_actual = coincidencia_tiempo.group(1)

        if coincidencia_vuelta:
            numero_vuelta = int(coincidencia_vuelta.group(1))
            if numero_vuelta not in sesiones[sesion_actual]:
                sesiones[sesion_actual][numero_vuelta] = {
                    "marcas_tiempo": [],
                    "velocidades": [],
                    "frenos": [],
                    "rpms": [],
                    "marchas": [],
                    "duraciones": [],
                    "posiciones": []
                }
            vuelta_actual = numero_vuelta

        if coincidencia_velocidad and marca_tiempo_actual:
            velocidad = float(coincidencia_velocidad.group(1).replace(",", "."))
            objeto_tiempo = datetime.strptime(marca_tiempo_actual, "%d/%m/%Y %H:%M:%S.%f")
            sesiones[sesion_actual][vuelta_actual]["marcas_tiempo"].append(objeto_tiempo)
            sesiones[sesion_actual][vuelta_actual]["velocidades"].append(velocidad)

        if coincidencia_freno:
            freno = float(coincidencia_freno.group(1).replace(",", "."))
            sesiones[sesion_actual][vuelta_actual]["frenos"].append(freno)

        if coincidencia_rpm:
            rpm = float(coincidencia_rpm.group(1).replace(",", "."))
            sesiones[sesion_actual][vuelta_actual]["rpms"].append(rpm)

        if coincidencia_marcha:
            marcha = int(coincidencia_marcha.group(1))
            sesiones[sesion_actual][vuelta_actual]["marchas"].append(marcha)
        
        if coincidencia_posicion:
            x = float(coincidencia_posicion.group(1).replace(",", "."))
            y = float(coincidencia_posicion.group(2).replace(",", "."))
            z = float(coincidencia_posicion.group(3).replace(",", "."))
            
            if vuelta_actual in sesiones[sesion_actual]:
                if "posiciones" not in sesiones[sesion_actual][vuelta_actual]:
                    sesiones[sesion_actual][vuelta_actual]["posiciones"] = []
                sesiones[sesion_actual][vuelta_actual]["posiciones"].append((x, y, z))

# Función para formatear segundos a mm:ss
def segundos_a_minutos(segundos, pos):
    minutos = int(segundos // 60)
    segundos = int(segundos % 60)
    return f"{minutos:02d}:{segundos:02d}"

# Calcular la duración de cada punto de datos en relación al inicio de la vuelta
for sesion, datos_vuelta in sesiones.items():
    for numero_vuelta, datos in datos_vuelta.items():
        if datos["marcas_tiempo"]:
            t0 = datos["marcas_tiempo"][0]
            datos["duraciones"] = [(t - t0).total_seconds() for t in datos["marcas_tiempo"]]

# Crear la figura usando GridSpec con 11 filas:
# Fila 0: Gráfica de tiempos por vuelta (línea)
# Fila 1: Espacio en blanco para la gráfica de tiempos
# Fila 2: Gráfica de deltas (barras, sin título)
# Fila 3: Velocidad media
# Fila 4: Velocidad
# Fila 5: Freno
# Fila 6: RPM
# Fila 7: Marcha
# Fila 8: Fuerza G (nueva)
# Fila 9: Mapa 2D
# Fila 10: (Espacio en blanco final, opcional)
fig = plt.figure(figsize=(12, 32))
gs = gridspec.GridSpec(12, 1, height_ratios=[1, 0.2, 1, 1, 1, 1, 1, 1, 1, 0.4, 4, 1])
plt.subplots_adjust(left=0.07, right=0.98, top=0.97, bottom=0, hspace=0.02)

# Definir cada eje (omitimos las filas en blanco)
ax0 = fig.add_subplot(gs[0])  # Tiempos por vuelta (línea)
ax1 = fig.add_subplot(gs[2])  # Delta (barras, sin título)
ax8 = fig.add_subplot(gs[3])  # Velocidad media
ax2 = fig.add_subplot(gs[4])  # Velocidad
ax3 = fig.add_subplot(gs[5])  # Freno
ax4 = fig.add_subplot(gs[6])  # RPM
ax5 = fig.add_subplot(gs[7])  # Marcha
ax7 = fig.add_subplot(gs[8])  # Fuerza G (nueva)
ax6 = fig.add_subplot(gs[10])  # Mapa 2D

def actualizar_grafica():
    global sesion_seleccionada

    print("Actualizando gráfica...")
    selecciones_vueltas = listbox_vueltas.curselection()
    
    print(f"Sesión seleccionada: {sesion_seleccionada}")
    print(f"Vueltas seleccionadas: {selecciones_vueltas}")
    
    if not sesion_seleccionada or not selecciones_vueltas:
        print("No se han seleccionado sesión o vueltas.")
        return
    
    # Obtener sesión y circuito actual (usar sesion_seleccionada)
    circuito_actual = circuito_por_sesion.get(sesion_seleccionada, "Circuito Desconocido")
    datos_vuelta_sesion = sesiones[sesion_seleccionada]

    print(f"Sesión actual: {sesion_seleccionada}")
    print(f"Circuito actual: {circuito_actual}")
    print(f"Datos de la sesión: {datos_vuelta_sesion.keys()}")
    
    # Limpiar TODOS los ejes
    for ax in [ax0, ax1, ax2, ax3, ax4, ax5, ax7, ax6, ax8]:
        ax.cla()
    
    colores = plt.rcParams['axes.prop_cycle'].by_key()['color']

    # Calcular el inicio y fin común para las gráficas de velocidad, freno, RPM y marcha
    vueltas_seleccionadas = []
    for idx in selecciones_vueltas:
        texto_vuelta = listbox_vueltas.get(idx)
        numero_vuelta = int(texto_vuelta.split()[1])
        vueltas_seleccionadas.append(numero_vuelta)

    inicio = min([datos_vuelta_sesion[numero_vuelta]["duraciones"][0] for numero_vuelta in vueltas_seleccionadas if numero_vuelta in datos_vuelta_sesion and datos_vuelta_sesion[numero_vuelta]["duraciones"]], default=0)
    fin = max([datos_vuelta_sesion[numero_vuelta]["duraciones"][-1] for numero_vuelta in vueltas_seleccionadas if numero_vuelta in datos_vuelta_sesion and datos_vuelta_sesion[numero_vuelta]["duraciones"]], default=1)
    
    print(f"Inicio: {inicio}, Fin: {fin}")
    
    # Listas para la gráfica de tiempos por vuelta y de deltas
    numeros_vuelta_linea = []
    tiempos_totales = []
    numeros_vuelta_delta = []
    tiempos_vuelta = []
    numeros_vuelta_velocidad = []
    velocidades_medias = []

    for idx, numero_vuelta in enumerate(vueltas_seleccionadas):
        if numero_vuelta not in datos_vuelta_sesion:
            print(f"La vuelta {numero_vuelta} no está en los datos de la sesión.")
            continue
        color = colores[idx % len(colores)]
        
        # Graficar en las gráficas de velocidad, freno, RPM y marcha
        try:
            print(f"Longitud de duraciones para la vuelta {numero_vuelta}: {len(datos_vuelta_sesion[numero_vuelta]['duraciones'])}")
            print(f"Longitud de velocidades para la vuelta {numero_vuelta}: {len(datos_vuelta_sesion[numero_vuelta]['velocidades'])}")
            ax2.plot(datos_vuelta_sesion[numero_vuelta]["duraciones"], datos_vuelta_sesion[numero_vuelta]["velocidades"],
                     color=color, alpha=0.7, label=f"Vuelta {numero_vuelta}")
            ax3.plot(datos_vuelta_sesion[numero_vuelta]["duraciones"], datos_vuelta_sesion[numero_vuelta]["frenos"],
                     color=color, alpha=0.7, label=f"Vuelta {numero_vuelta}")
            ax4.plot(datos_vuelta_sesion[numero_vuelta]["duraciones"], datos_vuelta_sesion[numero_vuelta]["rpms"],
                     color=color, alpha=0.7, label=f"Vuelta {numero_vuelta}")
            ax5.plot(datos_vuelta_sesion[numero_vuelta]["duraciones"], datos_vuelta_sesion[numero_vuelta]["marchas"],
                     color=color, alpha=0.7, label=f"Vuelta {numero_vuelta}")
        except Exception as e:
            print(f"Error al graficar la vuelta {numero_vuelta}: {e}")
        
        if datos_vuelta_sesion[numero_vuelta]["marchas"]:
            ax5.set_yticks(range(int(min(datos_vuelta_sesion[numero_vuelta]["marchas"])),
                                 int(max(datos_vuelta_sesion[numero_vuelta]["marchas"])) + 1))
        
        # Recoger datos para la gráfica de tiempos por vuelta y de deltas
        if datos_vuelta_sesion[numero_vuelta]["duraciones"]:
            tiempo_total = datos_vuelta_sesion[numero_vuelta]["duraciones"][-1]
            numeros_vuelta_linea.append(numero_vuelta)
            tiempos_totales.append(tiempo_total)
            numeros_vuelta_delta.append(numero_vuelta)
            tiempos_vuelta.append(tiempo_total)

        # Calcular velocidad media para esta vuelta
        if numero_vuelta in datos_vuelta_sesion and datos_vuelta_sesion[numero_vuelta]["velocidades"]:
            velocidad_media = np.mean(datos_vuelta_sesion[numero_vuelta]["velocidades"])
            numeros_vuelta_velocidad.append(numero_vuelta)
            velocidades_medias.append(velocidad_media)

    # Gráfica de tiempos por vuelta (ax0)
    if numeros_vuelta_linea:
        ax0.plot(numeros_vuelta_linea, tiempos_totales, marker='o', linestyle='-',
                color='tab:orange', label="Tiempo por vuelta")
        
        ax0.yaxis.set_major_formatter(FuncFormatter(segundos_a_minutos))
        
    ax0.set_xlabel("Vuelta")
    ax0.set_ylabel("Tiempo (M:SS)")
    ax0.grid()
    ax0.legend()

    # Gráfica de deltas (ax1): diferencia entre cada vuelta y la mejor vuelta (sin título)
    if tiempos_vuelta:
        mejor_tiempo = min(tiempos_vuelta)
        deltas = [t - mejor_tiempo for t in tiempos_vuelta]
        ax1.bar(numeros_vuelta_delta, deltas, color='tab:red')
    ax1.set_ylabel("Delta (s)")
    ax1.grid(axis="y")
    ax1.set_xticks([])

    # Configuración de las gráficas de velocidad, freno, RPM y marcha
    for ax in [ax2, ax3, ax4, ax5, ax7]:
        ax.set_xlim(inicio, fin)
        ax.xaxis.set_major_formatter(FuncFormatter(segundos_a_minutos))
    ax2.set_xticks([])
    ax3.set_xticks([])
    ax4.set_xticks([])
    ax5.set_xticks([])

    ax2.set_ylabel("Velocidad (km/h)")
    ax2.grid()

    ax3.set_ylabel("Freno (%)")
    ax3.grid()

    ax4.set_ylabel("RPM")
    ax4.grid()

    ax5.set_ylabel("Marcha")
    ax5.grid()

    # Gráfica de velocidad media por vuelta (ax8)
    if numeros_vuelta_velocidad:
        bars = ax8.bar(numeros_vuelta_velocidad, velocidades_medias, color=colores[:len(numeros_vuelta_velocidad)])
        
        # Añadir etiquetas con los valores
        for bar in bars:
            bar.get_height()
    
    ax8.set_ylabel("Velocidad Media (km/h)")
    ax8.grid(axis="y")
    ax8.set_xticks([])

    # Nueva gráfica: Fuerza G (ax7)
    # Se calcula la aceleración (m/s²) a partir de la velocidad (km/h convertida a m/s)
    # y se divide por 9.81 para obtener la fuerza G.
    for idx, numero_vuelta in enumerate(vueltas_seleccionadas):
        if numero_vuelta not in datos_vuelta_sesion:
            continue
        color = colores[idx % len(colores)]
        lista_velocidades = datos_vuelta_sesion[numero_vuelta]["velocidades"]
        lista_duraciones = datos_vuelta_sesion[numero_vuelta]["duraciones"]
        if len(lista_velocidades) >= 2 and len(lista_duraciones) >= 2:
            velocidades_mps = np.array(lista_velocidades) * 1000/3600  # Convertir a m/s
            duraciones = np.array(lista_duraciones)
            # Calcular aceleración usando diferencias finitas
            aceleracion = np.diff(velocidades_mps) / np.diff(duraciones)
            # Tiempo en los puntos medios
            tiempos_medios = (duraciones[:-1] + duraciones[1:]) / 2
            fuerza_g = aceleracion / 9.81
            ax7.plot(tiempos_medios, fuerza_g, color=color, alpha=0.7, label=f"Vuelta {numero_vuelta}")
    ax7.set_xlabel("Tiempo (s)")
    ax7.set_ylabel("Fuerza G")
    ax7.grid()

    # Dibujar el mapa 2D (ax6)
    ax6.set_aspect('equal')
    ax6.set_facecolor('none')
    ax6.grid(False)
    ax6.set_xticks([])
    ax6.set_yticks([])
    ax6.set_title("Trazadas")
    for spine in ax6.spines.values():
        spine.set_visible(False)
    
    # Dibujar trayectorias en el mapa
    for idx, numero_vuelta in enumerate(vueltas_seleccionadas):
        if numero_vuelta not in datos_vuelta_sesion:
            continue
        color = colores[idx % len(colores)]
        if "posiciones" in datos_vuelta_sesion[numero_vuelta]:
            posiciones = datos_vuelta_sesion[numero_vuelta]["posiciones"]
            x = [p[0] for p in posiciones]
            y = [p[1] for p in posiciones]
            ax6.plot(x, y, color=color, alpha=0.7, linewidth=2, label=f"Vuelta {numero_vuelta}")
            if x and y:
                ax6.scatter(x[0], y[0], color=color, marker='o', s=50,
                           edgecolor='black', zorder=3)
                ax6.scatter(x[-1], y[-1], color=color, marker='s', s=50,
                           edgecolor='black', zorder=3)
    
    # Ajustar límites del mapa con un margen del 1%
    todas_x = [p[0] for numero_vuelta in vueltas_seleccionadas if numero_vuelta in datos_vuelta_sesion and "posiciones" in datos_vuelta_sesion[numero_vuelta] for p in datos_vuelta_sesion[numero_vuelta]["posiciones"]]
    todas_y = [p[1] for numero_vuelta in vueltas_seleccionadas if numero_vuelta in datos_vuelta_sesion and "posiciones" in datos_vuelta_sesion[numero_vuelta] for p in datos_vuelta_sesion[numero_vuelta]["posiciones"]]
    if todas_x and todas_y:
        margen_x = (max(todas_x) - min(todas_x)) * 0.01
        margen_y = (max(todas_y) - min(todas_y)) * 0.01
        ax6.set_xlim(min(todas_x) - margen_x, max(todas_x) + margen_x)
        ax6.set_ylim(min(todas_y) - margen_y, max(todas_y) + margen_y)
    
    ax6.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=7, frameon=True, framealpha=0.8)
    
    fig.suptitle(f"Sesión: {sesion_actual} | Circuito: {circuito_actual}", 
                 fontsize=14, fontweight="bold")
    
    # Configurar tooltips (con mplcursors) para algunas gráficas
    cursor0 = mplcursors.cursor(ax0, hover=True)
    cursor0.connect("add", lambda sel: sel.annotation.set_text(
        f"Vuelta: {sel.target[0]:.0f}\nTiempo: {sel.target[1]:.2f} s"))
    cursor1 = mplcursors.cursor(ax1, hover=True)
    cursor1.connect("add", lambda sel: sel.annotation.set_text(
        f"Vuelta: {sel.target[0]:.0f}\nDelta: {sel.target[1]:.2f} s"))
    cursor2 = mplcursors.cursor(ax2, hover=True)
    cursor2.connect("add", lambda sel: sel.annotation.set_text(
        f"{sel.artist.get_label()}\nTiempo: {sel.target[0]:.2f} s\nVelocidad: {sel.target[1]:.2f} km/h"))
    cursor3 = mplcursors.cursor(ax3, hover=True)
    cursor3.connect("add", lambda sel: sel.annotation.set_text(
        f"{sel.artist.get_label()}\nTiempo: {sel.target[0]:.2f} s\nFreno: {sel.target[1]:.2f} %"))
    cursor4 = mplcursors.cursor(ax4, hover=True)
    cursor4.connect("add", lambda sel: sel.annotation.set_text(
        f"{sel.artist.get_label()}\nTiempo: {sel.target[0]:.2f} s\nRPM: {sel.target[1]:.0f}"))
    cursor5 = mplcursors.cursor(ax5, hover=True)
    cursor5.connect("add", lambda sel: sel.annotation.set_text(
        f"{sel.artist.get_label()}\nTiempo: {sel.target[0]:.2f} s\nMarcha: {sel.target[1]:.0f}"))
    cursor7 = mplcursors.cursor(ax7, hover=True)
    cursor7.connect("add", lambda sel: sel.annotation.set_text(
        f"Fuerza G: {sel.target[1]:.2f}"))
    cursor8 = mplcursors.cursor(ax8, hover=True)
    cursor8.connect("add", lambda sel: sel.annotation.set_text(
        f"Vuelta: {sel.target[0]:.0f}\nVelocidad Media: {sel.target[1]:.2f} km/h"))
    cursor6 = mplcursors.cursor(ax6, hover=True)
    cursor6.connect("add", lambda sel: sel.annotation.set_text(
        sel.artist.get_label()))
    
    canvas_fig.draw()

# Función para exportar el gráfico (añadir al inicio del código, junto a las otras funciones)
def exportar_grafico(fig, nombre_circuito):

    # Generar nombre de archivo con fecha/hora
    fecha_hora = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    ruta_archivo = f"{ruta_exportaciones}\\{nombre_circuito}_{fecha_hora}.png"

    # Guardar la figura con alta calidad
    fig.savefig(ruta_archivo, dpi=300, bbox_inches='tight', transparent=True)
    print(f"¡Gráfico exportado como '{ruta_archivo}'!")

# Función para cargar vueltas al seleccionar sesión
def cargar_vueltas(event=None):
    global sesion_seleccionada

    selecciones = listbox_sesiones.curselection()
    if not selecciones:
        return
    
    # Obtener sesión seleccionada
    global sesion_actual
    sesion_actual = sesiones_disponibles[selecciones[0]]
    sesion_seleccionada = sesion_actual
    
    # Actualizar listbox de vueltas
    listbox_vueltas.delete(0, tk.END)
    vueltas = sorted(sesiones[sesion_actual].keys())
    for vuelta in vueltas:
        listbox_vueltas.insert(tk.END, f"Vuelta {vuelta}")

# Crear la interfaz gráfica
root = tk.Tk()
sesion_seleccionada = None
root.title("Gráficas de Telemetría")
root.geometry("1200x900")
ancho_pantalla = root.winfo_screenwidth()
alto_pantalla = root.winfo_screenheight()
x = (ancho_pantalla - 1200) // 2
y = (alto_pantalla - 900) // 2
root.geometry(f"+{x}+{y}")

marco_control = tk.Frame(root)
marco_control.pack(side=tk.TOP, fill=tk.X)

# Añadir ListBox para sesiones
tk.Label(marco_control, text="Sesiones:").pack(side=tk.LEFT, padx=1, pady=1)
listbox_sesiones = tk.Listbox(marco_control, selectmode=tk.SINGLE, width=40)
sesiones_disponibles = sorted(sesiones.keys(), reverse=True)  # Ordenar de más reciente a más antigua
for sesion in sesiones_disponibles:
    circuito = circuito_por_sesion.get(sesion, "Circuito Desconocido")
    listbox_sesiones.insert(tk.END, f"{sesion} - {circuito}")
listbox_sesiones.pack(side=tk.LEFT, padx=1, pady=1)

listbox_sesiones.bind("<<ListboxSelect>>", cargar_vueltas)

# ListBox para vueltas
tk.Label(marco_control, text="Vueltas:").pack(side=tk.LEFT, padx=1, pady=1)
listbox_vueltas = tk.Listbox(marco_control, selectmode=tk.MULTIPLE)
listbox_vueltas.pack(side=tk.LEFT, padx=1, pady=1)
tk.Button(marco_control, text="Actualizar", command=actualizar_grafica).pack(side=tk.LEFT, padx=0, pady=0)

boton_exportar = tk.Button(marco_control, text="Exportar Gráficas", command=lambda: exportar_grafico(fig, circuito_por_sesion.get(sesion_seleccionada.split(" - ")[0])))
boton_exportar.pack(side=tk.RIGHT, padx=5)

canvas = tk.Canvas(root)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=canvas.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
canvas.configure(yscrollcommand=scrollbar.set)
canvas.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

marco = ttk.Frame(canvas)
canvas.create_window((0, 0), window=marco, anchor="nw")
canvas_fig = FigureCanvasTkAgg(fig, master=marco)
canvas_fig.draw()
canvas_fig.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Seleccionar última sesión por defecto si existe y seleccionar todas las vueltas
if sesiones_disponibles:
    listbox_sesiones.select_set(0)
    cargar_vueltas()
    for i in range(listbox_vueltas.size()):
        listbox_vueltas.select_set(i)
    actualizar_grafica()

# Función para cerrar la consola
def cerrar_programa():
    print("Cerrando programa...")
    root.destroy()
    # Cerrar el intérprete de Python
    exit()

# Asignar la función de cierre al evento de cierre de ventana
root.protocol("WM_DELETE_WINDOW", cerrar_programa)

root.mainloop()