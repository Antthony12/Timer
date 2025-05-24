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
brakes = []
rpms = []
gears = []
laps = []  # Lista de vueltas registradas
lap_data = {}  # Diccionario para almacenar datos por vuelta

# Expresiones regulares para extraer datos
timestamp_pattern = re.compile(r"Fecha: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})")
speed_pattern = re.compile(r"Velocidad: ([\d,]+) km/h")
brake_pattern = re.compile(r"Freno: ([\d,]+)%")
rpm_pattern = re.compile(r"RPM: ([\d,]+)")
gear_pattern = re.compile(r"Marcha: (\d+)")
lap_pattern = re.compile(r"Vuelta: (\d+)")

# Variables temporales
current_lap = None

# Leer y procesar el archivo
with open(file_path, "r", encoding="utf-8") as file:
    for line in file:
        timestamp_match = timestamp_pattern.search(line)
        speed_match = speed_pattern.search(line)
        brake_match = brake_pattern.search(line)
        rpm_match = rpm_pattern.search(line)
        gear_match = gear_pattern.search(line)
        lap_match = lap_pattern.search(line)

        if timestamp_match:
            current_timestamp = timestamp_match.group(1)

        if lap_match:
            lap_number = int(lap_match.group(1))
            if lap_number not in lap_data:
                lap_data[lap_number] = {"timestamps": [], "speeds": [], "brakes": [], "rpms": [], "gears": []}
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

# Función para actualizar la gráfica según la vuelta seleccionada
def actualizar_grafica():
    seleccion = combo_vueltas.get()
    axs[0].cla()
    axs[1].cla()
    axs[2].cla()
    axs[3].cla()

    # Color fijo para todas las vueltas
    color_fijo = "b"  # Azul

    if seleccion == "Todas las vueltas":
        for lap_number in lap_data.keys():
            axs[0].plot(lap_data[lap_number]["timestamps"], lap_data[lap_number]["speeds"], color=color_fijo, alpha=0.7)
            axs[1].plot(lap_data[lap_number]["timestamps"], lap_data[lap_number]["brakes"], color=color_fijo, alpha=0.7)
            axs[2].plot(lap_data[lap_number]["timestamps"], lap_data[lap_number]["rpms"], color=color_fijo, alpha=0.7)
            axs[3].plot(lap_data[lap_number]["timestamps"], lap_data[lap_number]["gears"], color=color_fijo, alpha=0.7)

            # Configurar ticks solo si hay datos de marchas
            if lap_data[lap_number]["gears"]:
                axs[3].set_yticks(range(int(min(lap_data[lap_number]["gears"])), int(max(lap_data[lap_number]["gears"])) + 1))

        # Agregar líneas verticales para cada vuelta
        for i in range(len(laps)):  # Incluir también la última vuelta
            lap_time = lap_data[laps[i]]["timestamps"][0]  # Primer timestamp de la vuelta
            for ax in axs:
                ax.axvline(lap_time, color="r", linestyle="--", alpha=0.7)
                ax.text(lap_time, ax.get_ylim()[1] * 0.9, f"Vuelta {laps[i]}", color="red", fontsize=10, rotation=45)

    else:
        try:
            vuelta_seleccionada = int(seleccion.split()[1])  # Extraer número de vuelta
            axs[0].plot(lap_data[vuelta_seleccionada]["timestamps"], lap_data[vuelta_seleccionada]["speeds"], label=f"Vuelta {vuelta_seleccionada}", color=color_fijo)
            axs[1].plot(lap_data[vuelta_seleccionada]["timestamps"], lap_data[vuelta_seleccionada]["brakes"], label=f"Vuelta {vuelta_seleccionada}", color=color_fijo)
            axs[2].plot(lap_data[vuelta_seleccionada]["timestamps"], lap_data[vuelta_seleccionada]["rpms"], label=f"Vuelta {vuelta_seleccionada}", color=color_fijo)
            axs[3].plot(lap_data[vuelta_seleccionada]["timestamps"], lap_data[vuelta_seleccionada]["gears"], label=f"Vuelta {vuelta_seleccionada}", color=color_fijo)

            # Configurar ticks solo si hay datos de marchas
            if lap_data[vuelta_seleccionada]["gears"]:
                axs[3].set_yticks(range(int(min(lap_data[vuelta_seleccionada]["gears"])), int(max(lap_data[vuelta_seleccionada]["gears"])) + 1))

        except (IndexError, ValueError, KeyError):
            print("Error: Vuelta seleccionada no válida.")

    # Añadir marcas de tiempo al inicio y al final
    for ax in axs:
        if seleccion == "Todas las vueltas":
            inicio = lap_data[laps[0]]["timestamps"][0]
            fin = lap_data[laps[-1]]["timestamps"][-1]
        else:
            inicio = lap_data[int(seleccion.split()[1])]["timestamps"][0]
            fin = lap_data[int(seleccion.split()[1])]["timestamps"][-1]

        # Ajustar límites del eje X para que las líneas toquen ambos extremos
        ax.set_xlim(inicio, fin)

    axs[0].set_ylabel("Velocidad (km/h)")
    axs[0].grid()

    axs[1].set_ylabel("Freno (%)")
    axs[1].grid()

    axs[2].set_ylabel("RPM")
    axs[2].grid()

    axs[3].set_xlabel("Tiempo")
    axs[3].set_ylabel("Marcha")
    axs[3].grid()

    canvas_fig.draw()

# Crear interfaz gráfica
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

# Menú desplegable para elegir vuelta
frame_control = tk.Frame(root)
frame_control.pack(side=tk.TOP, fill=tk.X)

tk.Label(frame_control, text="Selecciona vuelta:").pack(side=tk.LEFT, padx=1, pady=1)
vueltas_disponibles = ["Todas las vueltas"] + [f"Vuelta {lap}" for lap in laps]
combo_vueltas = ttk.Combobox(frame_control, values=vueltas_disponibles)
combo_vueltas.current(0)
combo_vueltas.pack(side=tk.LEFT, padx=0, pady=0)
tk.Button(frame_control, text="Actualizar", command=actualizar_grafica).pack(side=tk.LEFT, padx=0, pady=0)

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

# Crear una figura con cuatro subgráficas
fig, axs = plt.subplots(4, 1, figsize=(12, 16))

# Reducir los márgenes y el espacio entre subgráficas
plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, hspace=0.3)

canvas_fig = FigureCanvasTkAgg(fig, master=frame)
canvas_fig.draw()
canvas_fig.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Iniciar la interfaz gráfica
root.mainloop()