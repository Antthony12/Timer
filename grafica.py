import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.gridspec as gridspec
import tkinter as tk
from tkinter import ttk
import re
from datetime import datetime
import mplcursors
import numpy as np

# Ruta del archivo
file_path = r"C:\Users\ejemplo\Desktop\scripts\Logs\telemetriagta5.txt"

# Listas para almacenar datos
timestamps = []
speeds = []
brakes = []
rpms = []
gears = []
laps = []  # Lista de vueltas registradas
lap_data = {}  # Diccionario para almacenar datos por vuelta
circuito = "Circuito Desconocido"  # Valor por defecto

# Expresiones regulares para extraer datos
timestamp_pattern = re.compile(r"Fecha: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})")
speed_pattern = re.compile(r"Velocidad: ([\d,]+) km/h")
brake_pattern = re.compile(r"Freno: ([\d,]+)%")
rpm_pattern = re.compile(r"RPM: ([\d,]+)")
gear_pattern = re.compile(r"Marcha: (\d+)")
lap_pattern = re.compile(r"Vuelta: (\d+)")
circuito_pattern = re.compile(r"Circuito: (.+?) \| Vuelta:")
position_pattern = re.compile(r"Posición: \(([\d,-]+), ([\d,-]+), ([\d,-]+)\)")

# Leer y procesar el archivo
with open(file_path, "r", encoding="utf-8") as file:
    for line in file:
        # Buscar el nombre del circuito
        circuito_match = circuito_pattern.search(line)
        if circuito_match:
            circuito = circuito_match.group(1).strip()

        timestamp_match = timestamp_pattern.search(line)
        speed_match = speed_pattern.search(line)
        brake_match = brake_pattern.search(line)
        rpm_match = rpm_pattern.search(line)
        gear_match = gear_pattern.search(line)
        lap_match = lap_pattern.search(line)
        position_match = position_pattern.search(line)

        if timestamp_match:
            current_timestamp = timestamp_match.group(1)

        if lap_match:
            lap_number = int(lap_match.group(1))
            if lap_number not in lap_data:
                lap_data[lap_number] = {
                    "timestamps": [],
                    "speeds": [],
                    "brakes": [],
                    "rpms": [],
                    "gears": [],
                    "durations": []
                }
                laps.append(lap_number)
            current_lap = lap_number

        if speed_match and current_timestamp:
            speed = float(speed_match.group(1).replace(",", "."))
            timestamp_obj = datetime.strptime(current_timestamp, "%Y-%m-%d %H:%M:%S.%f")
            lap_data[current_lap]["timestamps"].append(timestamp_obj)
            lap_data[current_lap]["speeds"].append(speed)

        if brake_match:
            brake = float(brake_match.group(1).replace(",", "."))
            lap_data[current_lap]["brakes"].append(brake)

        if rpm_match:
            rpm = float(rpm_match.group(1).replace(",", "."))
            lap_data[current_lap]["rpms"].append(rpm)

        if gear_match:
            gear = int(gear_match.group(1))
            lap_data[current_lap]["gears"].append(gear)
        
        if position_match:
            x = float(position_match.group(1).replace(",", "."))
            y = float(position_match.group(2).replace(",", "."))
            z = float(position_match.group(3).replace(",", "."))
            
            if current_lap in lap_data:
                if "positions" not in lap_data[current_lap]:
                    lap_data[current_lap]["positions"] = []
                lap_data[current_lap]["positions"].append((x, y, z))

# Calcular la duración de cada punto de datos en relación al inicio de la vuelta
for lap_number in lap_data.keys():
    if lap_data[lap_number]["timestamps"]:
        t0 = lap_data[lap_number]["timestamps"][0]
        lap_data[lap_number]["durations"] = [(t - t0).total_seconds() for t in lap_data[lap_number]["timestamps"]]

# Crear la figura usando GridSpec con 11 filas:
# Fila 0: Gráfica de tiempos por vuelta (línea)
# Fila 1: Espacio en blanco para la gráfica de tiempos
# Fila 2: Gráfica de deltas (barras, sin título)
# Fila 3: Espacio en blanco para la gráfica de deltas
# Fila 4: Velocidad
# Fila 5: Freno
# Fila 6: RPM
# Fila 7: Marcha
# Fila 8: Fuerza G (nueva)
# Fila 9: Mapa 2D
# Fila 10: (Espacio en blanco final, opcional)
fig = plt.figure(figsize=(12, 32))
gs = gridspec.GridSpec(11, 1, height_ratios=[1, 0.2, 1, 0.2, 1, 1, 1, 1, 1, 2, 5])
plt.subplots_adjust(left=0.07, right=0.98, top=0.97, bottom=0, hspace=0.02)

# Definir cada eje (omitimos las filas en blanco)
ax0 = fig.add_subplot(gs[0])  # Tiempos por vuelta (línea)
ax1 = fig.add_subplot(gs[2])  # Delta (barras, sin título)
ax2 = fig.add_subplot(gs[4])  # Velocidad
ax3 = fig.add_subplot(gs[5])  # Freno
ax4 = fig.add_subplot(gs[6])  # RPM
ax5 = fig.add_subplot(gs[7])  # Marcha
ax7 = fig.add_subplot(gs[8])  # Fuerza G (nueva)
ax6 = fig.add_subplot(gs[9])  # Mapa 2D

def actualizar_grafica():
    selecciones = listbox_vueltas.curselection()
    if not selecciones:
        selecciones = range(len(vueltas_disponibles))
    
    # Limpiar TODOS los ejes
    for ax in [ax0, ax1, ax2, ax3, ax4, ax5, ax7, ax6]:
        ax.cla()
    
    colores = plt.rcParams['axes.prop_cycle'].by_key()['color']

    # Calcular el inicio y fin común para las gráficas de velocidad, freno, RPM y marcha
    inicio = min([lap_data[vueltas_disponibles[i]]["durations"][0] for i in selecciones if lap_data[vueltas_disponibles[i]]["durations"]])
    fin = max([lap_data[vueltas_disponibles[i]]["durations"][-1] for i in selecciones if lap_data[vueltas_disponibles[i]]["durations"]])
    
    # Listas para la gráfica de tiempos por vuelta y de deltas
    lap_numbers_line = []
    lap_total_times = []
    lap_numbers_delta = []
    lap_times = []

    for idx in selecciones:
        lap_number = vueltas_disponibles[idx]
        color = colores[idx % len(colores)]
        
        # Graficar en las gráficas de velocidad, freno, RPM y marcha
        ax2.plot(lap_data[lap_number]["durations"], lap_data[lap_number]["speeds"],
                 color=color, alpha=0.7, label=f"Vuelta {lap_number}")
        ax3.plot(lap_data[lap_number]["durations"], lap_data[lap_number]["brakes"],
                 color=color, alpha=0.7, label=f"Vuelta {lap_number}")
        ax4.plot(lap_data[lap_number]["durations"], lap_data[lap_number]["rpms"],
                 color=color, alpha=0.7, label=f"Vuelta {lap_number}")
        ax5.plot(lap_data[lap_number]["durations"], lap_data[lap_number]["gears"],
                 color=color, alpha=0.7, label=f"Vuelta {lap_number}")
        if lap_data[lap_number]["gears"]:
            ax5.set_yticks(range(int(min(lap_data[lap_number]["gears"])),
                                 int(max(lap_data[lap_number]["gears"])) + 1))
        
        # Recoger datos para la gráfica de tiempos por vuelta y de deltas
        if lap_data[lap_number]["durations"]:
            total_time = lap_data[lap_number]["durations"][-1]
            lap_numbers_line.append(lap_number)
            lap_total_times.append(total_time)
            lap_numbers_delta.append(lap_number)
            lap_times.append(total_time)

    # Gráfica de tiempos por vuelta (ax0)
    if lap_numbers_line:
        ax0.plot(lap_numbers_line, lap_total_times, marker='o', linestyle='-',
                 color='tab:orange', label="Tiempo por vuelta")
    ax0.set_xlabel("Vuelta")
    ax0.set_ylabel("Tiempo (s)")
    ax0.grid()
    ax0.legend()

    # Gráfica de deltas (ax1): diferencia entre cada vuelta y la mejor vuelta (sin título)
    if lap_times:
        mejor_tiempo = min(lap_times)
        deltas = [t - mejor_tiempo for t in lap_times]
        ax1.bar(lap_numbers_delta, deltas, color='tab:red')
    ax1.set_xlabel("Vuelta")
    ax1.set_ylabel("Delta (s)")
    ax1.grid(axis="y")

    # Configuración de las gráficas de velocidad, freno, RPM y marcha
    for ax in [ax2, ax3, ax4, ax5, ax7]:
        ax.set_xlim(inicio, fin)
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

    # Nueva gráfica: Fuerza G (ax7)
    # Se calcula la aceleración (m/s²) a partir de la velocidad (km/h convertida a m/s)
    # y se divide por 9.81 para obtener la fuerza G.
    for idx in selecciones:
        lap_number = vueltas_disponibles[idx]
        color = colores[idx % len(colores)]
        speeds_list = lap_data[lap_number]["speeds"]
        durations_list = lap_data[lap_number]["durations"]
        if len(speeds_list) >= 2 and len(durations_list) >= 2:
            speeds_mps = np.array(speeds_list) * 1000/3600  # Convertir a m/s
            durations = np.array(durations_list)
            # Calcular aceleración usando diferencias finitas
            acc = np.diff(speeds_mps) / np.diff(durations)
            # Tiempo en los puntos medios
            mid_times = (durations[:-1] + durations[1:]) / 2
            g_force = acc / 9.81
            ax7.plot(mid_times, g_force, color=color, alpha=0.7, label=f"Vuelta {lap_number}")
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
    for idx in selecciones:
        lap_number = vueltas_disponibles[idx]
        color = colores[idx % len(colores)]
        if "positions" in lap_data[lap_number]:
            positions = lap_data[lap_number]["positions"]
            x = [p[0] for p in positions]
            y = [p[1] for p in positions]
            ax6.plot(x, y, color=color, alpha=0.7, linewidth=2, label=f"Vuelta {lap_number}")
            if x and y:
                ax6.scatter(x[0], y[0], color=color, marker='o', s=50,
                           edgecolor='black', zorder=3)
                ax6.scatter(x[-1], y[-1], color=color, marker='s', s=50,
                           edgecolor='black', zorder=3)
    
    # Ajustar límites del mapa con un margen del 1%
    all_x = [p[0] for lap in vueltas_disponibles if "positions" in lap_data[lap] for p in lap_data[lap]["positions"]]
    all_y = [p[1] for lap in vueltas_disponibles if "positions" in lap_data[lap] for p in lap_data[lap]["positions"]]
    if all_x and all_y:
        margin_x = (max(all_x) - min(all_x)) * 0.01
        margin_y = (max(all_y) - min(all_y)) * 0.01
        ax6.set_xlim(min(all_x) - margin_x, max(all_x) + margin_x)
        ax6.set_ylim(min(all_y) - margin_y, max(all_y) + margin_y)
    
    ax6.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=7, frameon=True, framealpha=0.8)
    
    fig.suptitle(f"Circuito: {circuito}", fontsize=14, fontweight="bold")
    
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
    cursor6 = mplcursors.cursor(ax6, hover=True)
    cursor6.connect("add", lambda sel: sel.annotation.set_text(
        sel.artist.get_label()))
    
    canvas_fig.draw()

# Crear la interfaz gráfica
root = tk.Tk()
root.title("Gráficas de Telemetría")
root.geometry("1200x900")
ancho_pantalla = root.winfo_screenwidth()
alto_pantalla = root.winfo_screenheight()
x = (ancho_pantalla - 1200) // 2
y = (alto_pantalla - 900) // 2
root.geometry(f"+{x}+{y}")

frame_control = tk.Frame(root)
frame_control.pack(side=tk.TOP, fill=tk.X)
tk.Label(frame_control, text="Selecciona vueltas:").pack(side=tk.LEFT, padx=1, pady=1)

listbox_vueltas = tk.Listbox(frame_control, selectmode=tk.MULTIPLE)
vueltas_disponibles = sorted(lap_data.keys())
for lap in vueltas_disponibles:
    listbox_vueltas.insert(tk.END, f"Vuelta {lap}")
listbox_vueltas.pack(side=tk.LEFT, padx=0, pady=0)
tk.Button(frame_control, text="Actualizar", command=actualizar_grafica).pack(side=tk.LEFT, padx=0, pady=0)

canvas = tk.Canvas(root)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=canvas.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
canvas.configure(yscrollcommand=scrollbar.set)
canvas.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

frame = ttk.Frame(canvas)
canvas.create_window((0, 0), window=frame, anchor="nw")
canvas_fig = FigureCanvasTkAgg(fig, master=frame)
canvas_fig.draw()
canvas_fig.get_tk_widget().pack(fill=tk.BOTH, expand=True)

actualizar_grafica()
root.mainloop()
