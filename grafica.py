import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
import re
from datetime import datetime

# Ruta del archivo
file_path = r"C:\Users\anton\Desktop\scripts\Logs\telemetriagta5.txt"

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
circuito_pattern = re.compile(r"Circuito: (.+?) \| Vuelta:")  # Expresión regular para el nombre del circuito

# Leer y procesar el archivo
with open(file_path, "r", encoding="utf-8") as file:
    for line in file:
        # Buscar el nombre del circuito
        circuito_match = circuito_pattern.search(line)
        if circuito_match:
            circuito = circuito_match.group(1).strip()  # Extraer el nombre del circuito

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
                lap_data[lap_number] = {"timestamps": [], "speeds": [], "brakes": [], "rpms": [], "gears": [], "durations": []}
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

# Calcular la duración de cada punto de datos en relación al inicio de la vuelta
for lap_number in lap_data.keys():
    if lap_data[lap_number]["timestamps"]:
        t0 = lap_data[lap_number]["timestamps"][0]  # Primer timestamp de la vuelta
        lap_data[lap_number]["durations"] = [(t - t0).total_seconds() for t in lap_data[lap_number]["timestamps"]]

# Función para actualizar la gráfica según la vuelta seleccionada
def actualizar_grafica():
    seleccion = combo_vueltas.get()
    axs[0].cla()
    axs[1].cla()
    axs[2].cla()
    axs[3].cla()

    # Obtener el ciclo de colores de Matplotlib
    colores = plt.rcParams['axes.prop_cycle'].by_key()['color']

    if seleccion == "Todas las vueltas":
        for i, lap_number in enumerate(lap_data.keys()):
            color = colores[i % len(colores)]  # Asignar un color único a cada vuelta
            axs[0].plot(lap_data[lap_number]["durations"], lap_data[lap_number]["speeds"], color=color, alpha=0.7, label=f"Vuelta {lap_number}")
            axs[1].plot(lap_data[lap_number]["durations"], lap_data[lap_number]["brakes"], color=color, alpha=0.7, label=f"Vuelta {lap_number}")
            axs[2].plot(lap_data[lap_number]["durations"], lap_data[lap_number]["rpms"], color=color, alpha=0.7, label=f"Vuelta {lap_number}")
            axs[3].plot(lap_data[lap_number]["durations"], lap_data[lap_number]["gears"], color=color, alpha=0.7, label=f"Vuelta {lap_number}")

            # Configurar ticks solo si hay datos de marchas
            if lap_data[lap_number]["gears"]:
                axs[3].set_yticks(range(int(min(lap_data[lap_number]["gears"])), int(max(lap_data[lap_number]["gears"])) + 1))

        # Calcular el inicio y fin para todas las vueltas
        inicio = min([lap_data[lap]["durations"][0] for lap in lap_data.keys()])
        fin = max([lap_data[lap]["durations"][-1] for lap in lap_data.keys()])

    else:
        try:
            vuelta_seleccionada = int(seleccion.split()[1])  # Extraer número de vuelta
            color = colores[vuelta_seleccionada % len(colores)]  # Asignar un color único a la vuelta seleccionada
            axs[0].plot(lap_data[vuelta_seleccionada]["durations"], lap_data[vuelta_seleccionada]["speeds"], color=color, label=f"Vuelta {vuelta_seleccionada}")
            axs[1].plot(lap_data[vuelta_seleccionada]["durations"], lap_data[vuelta_seleccionada]["brakes"], color=color, label=f"Vuelta {vuelta_seleccionada}")
            axs[2].plot(lap_data[vuelta_seleccionada]["durations"], lap_data[vuelta_seleccionada]["rpms"], color=color, label=f"Vuelta {vuelta_seleccionada}")
            axs[3].plot(lap_data[vuelta_seleccionada]["durations"], lap_data[vuelta_seleccionada]["gears"], color=color, label=f"Vuelta {vuelta_seleccionada}")

            # Configurar ticks solo si hay datos de marchas
            if lap_data[vuelta_seleccionada]["gears"]:
                axs[3].set_yticks(range(int(min(lap_data[vuelta_seleccionada]["gears"])), int(max(lap_data[vuelta_seleccionada]["gears"])) + 1))

            # Calcular el inicio y fin para la vuelta seleccionada
            inicio = lap_data[vuelta_seleccionada]["durations"][0]
            fin = lap_data[vuelta_seleccionada]["durations"][-1]

        except (IndexError, ValueError, KeyError):
            print("Error: Vuelta seleccionada no válida.")

    # Ajustar los límites del eje X para que las líneas toquen el inicio y el final
    for ax in axs:
        ax.set_xlim(inicio, fin)

    # Deshabilitar las etiquetas del eje X en las gráficas de velocidad, freno y RPM
    axs[0].set_xticks([])
    axs[1].set_xticks([])
    axs[2].set_xticks([])

    axs[0].set_ylabel("Velocidad (km/h)")
    axs[0].grid()
    axs[0].legend()

    axs[1].set_ylabel("Freno (%)")
    axs[1].grid()
    axs[1].legend()

    axs[2].set_ylabel("RPM")
    axs[2].grid()
    axs[2].legend()

    axs[3].set_xlabel("Duración (segundos)")
    axs[3].set_ylabel("Marcha")
    axs[3].grid()
    axs[3].legend()

    # Añadir el título del circuito
    fig.suptitle(f"Circuito: {circuito}", fontsize=14, fontweight="bold")

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
plt.subplots_adjust(left=0.07, right=0.98, top=0.95, bottom=0.05, hspace=0.02)

canvas_fig = FigureCanvasTkAgg(fig, master=frame)
canvas_fig.draw()
canvas_fig.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Iniciar la interfaz gráfica
root.mainloop()