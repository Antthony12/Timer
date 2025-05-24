import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
import re
from datetime import datetime

# Ruta del archivo
file_path = r"C:\Users\ejemplo\Desktop\scripts\Logs\telemetriagta5.txt"

# Listas para almacenar datos
timestamps = []
speeds = []
brakes = []  # Lista para almacenar el porcentaje de frenado
rpms = []  # Lista para almacenar las revoluciones por minuto
gears = []  # Lista para almacenar las marchas (enteros)
lap_changes = []  # Para almacenar cambios de vuelta
laps = []  # Lista de vueltas registradas

# Expresiones regulares para extraer datos
timestamp_pattern = re.compile(r"Fecha: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})")
speed_pattern = re.compile(r"Velocidad: ([\d,]+) km/h")
brake_pattern = re.compile(r"Freno: ([\d,]+)%")  # Expresión regular para el freno
rpm_pattern = re.compile(r"RPM: ([\d,]+)")  # Expresión regular para las RPM
gear_pattern = re.compile(r"Marcha: (\d+)")  # Expresión regular para las marchas
lap_pattern = re.compile(r"Vuelta: (\d+)")

# Variables temporales
current_lap = None

# Leer y procesar el archivo
with open(file_path, "r", encoding="utf-8") as file:
    for line in file:
        timestamp_match = timestamp_pattern.search(line)
        speed_match = speed_pattern.search(line)
        brake_match = brake_pattern.search(line)  # Buscar datos de freno
        rpm_match = rpm_pattern.search(line)  # Buscar datos de RPM
        gear_match = gear_pattern.search(line)  # Buscar datos de marcha
        lap_match = lap_pattern.search(line)

        if timestamp_match:
            current_timestamp = timestamp_match.group(1)

        if lap_match:
            lap_number = int(lap_match.group(1))
            if current_lap is None or lap_number != current_lap:
                lap_changes.append(datetime.strptime(current_timestamp, "%Y-%m-%d %H:%M:%S.%f"))
                laps.append(lap_number)
                current_lap = lap_number

        if speed_match and current_timestamp:
            speed = float(speed_match.group(1).replace(",", "."))  # Convertir a número
            timestamps.append(datetime.strptime(current_timestamp, "%Y-%m-%d %H:%M:%S.%f"))
            speeds.append(speed)

        if brake_match and current_timestamp:  # Extraer datos de freno
            brake = float(brake_match.group(1).replace(",", "."))  # Convertir a número
            brakes.append(brake)

        if rpm_match and current_timestamp:  # Extraer datos de RPM
            rpm = float(rpm_match.group(1).replace(",", "."))  # Convertir a número
            rpms.append(rpm)

        if gear_match and current_timestamp:  # Extraer datos de marcha
            gear = int(gear_match.group(1))  # Convertir a entero
            gears.append(gear)

# Crear una figura con cuatro subgráficas (una encima de la otra)
fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(12, 16))  # Aumentar el tamaño de la figura

# Gráfica de velocidad (primera subgráfica)
ax1.plot(timestamps, speeds, linestyle="-", color="b", label="Velocidad (km/h)")
for i, lap_time in enumerate(lap_changes):
    ax1.axvline(lap_time, color="r", linestyle="--", alpha=0.7)
    ax1.text(lap_time, max(speeds) * 0.9, f"Vuelta {laps[i]}", color="red", fontsize=10, rotation=45)
ax1.set_xticks([])
ax1.set_ylabel("Velocidad (km/h)")
ax1.legend()
ax1.grid()

# Gráfica de frenado (segunda subgráfica)
ax2.plot(timestamps, brakes, linestyle="-", color="g", label="Freno (%)")
for i, lap_time in enumerate(lap_changes):
    ax2.axvline(lap_time, color="r", linestyle="--", alpha=0.7)
    ax2.text(lap_time, max(brakes) * 0.9, f"Vuelta {laps[i]}", color="red", fontsize=10, rotation=45)
ax2.set_xticks([])
ax2.set_ylabel("Freno (%)")
ax2.legend()
ax2.grid()

# Gráfica de RPM (tercera subgráfica)
ax3.plot(timestamps, rpms, linestyle="-", color="m", label="RPM")
for i, lap_time in enumerate(lap_changes):
    ax3.axvline(lap_time, color="r", linestyle="--", alpha=0.7)
    ax3.text(lap_time, max(rpms) * 0.9, f"Vuelta {laps[i]}", color="red", fontsize=10, rotation=45)
ax3.set_xticks([])
ax3.set_ylabel("RPM")
ax3.legend()
ax3.grid()

# Gráfica de marchas (cuarta subgráfica)
ax4.plot(timestamps, gears, linestyle="-", color="c", label="Marcha")  # Línea continua sin puntos
for i, lap_time in enumerate(lap_changes):
    ax4.axvline(lap_time, color="r", linestyle="--", alpha=0.7)
    ax4.text(lap_time, max(gears) * 0.9, f"Vuelta {laps[i]}", color="red", fontsize=10, rotation=45)
ax4.set_xlabel("Tiempo")
ax4.set_ylabel("Marcha")
ax4.tick_params(axis='x', rotation=45)

# Forzar que el eje Y de la gráfica de marchas muestre solo valores enteros
ax4.set_yticks(range(int(min(gears)), int(max(gears)) + 1))

ax4.legend()
ax4.grid()

# Ajustar el espacio entre las subgráficas
plt.tight_layout()

# Crear una ventana de Tkinter
root = tk.Tk()
root.title("Gráficas de Telemetría")

# Establecer el tamaño de la ventana (1200x800)
ancho_ventana = 1200
alto_ventana = 800
root.geometry(f"{ancho_ventana}x{alto_ventana}")

# Obtener el tamaño de la pantalla
ancho_pantalla = root.winfo_screenwidth()
alto_pantalla = root.winfo_screenheight()

# Calcular la posición para centrar la ventana
x = (ancho_pantalla - ancho_ventana) // 2
y = (alto_pantalla - alto_ventana) // 2

# Establecer la posición de la ventana
root.geometry(f"+{x}+{y}")

# Crear un canvas con barra de desplazamiento vertical
canvas = tk.Canvas(root)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=canvas.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

canvas.configure(yscrollcommand=scrollbar.set)
canvas.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

# Añadir la figura de matplotlib al canvas
frame = ttk.Frame(canvas)
canvas.create_window((0, 0), window=frame, anchor="nw")

canvas_fig = FigureCanvasTkAgg(fig, master=frame)
canvas_fig.draw()
canvas_fig.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Iniciar la interfaz gráfica
root.mainloop()