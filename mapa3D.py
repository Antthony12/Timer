import matplotlib.pyplot as plt
import numpy as np
import re

# Cargar los datos desde el archivo
ruta_archivo = r"C:\Users\ejemplo\Desktop\scripts\Logs\telemetriagta5.txt"

x_coords = []  # Longitud
y_coords = []  # Latitud
z_coords = []  # Altura

patron = re.compile(r"Posición: \((-?\d+[\.,]?\d*), (-?\d+[\.,]?\d*), (-?\d+[\.,]?\d*)\)")

with open(ruta_archivo, "r", encoding="utf-8") as file:
    for linea in file:
        match = patron.search(linea)
        if match:
            x, y, z = match.groups()
            x, y, z = x.replace(",", "."), y.replace(",", "."), z.replace(",", ".")
            x_coords.append(float(x))
            y_coords.append(float(y))
            z_coords.append(float(z))

if not x_coords:
    print("No se encontraron coordenadas en el archivo.")
    exit()

x_coords = np.array(x_coords)
y_coords = np.array(y_coords)
z_coords = np.array(z_coords)

fig = plt.figure(figsize=(10, 6))
ax = fig.add_subplot(111, projection='3d')

ax.plot(x_coords, y_coords, z_coords, color="blue")

# 🔹 Ocultar grid y etiquetas
ax.set_xticks([])  # Quitar ticks del eje X
ax.set_yticks([])  # Quitar ticks del eje Y
ax.set_zticks([])  # Quitar ticks del eje Z
ax.grid(False)  # Quitar la cuadrícula

# 🔹 Ocultar los paneles de los ejes (fondo)
ax.xaxis.pane.fill = False
ax.yaxis.pane.fill = False
ax.zaxis.pane.fill = False

# 🔹 Ocultar los bordes del marco
ax.xaxis.line.set_color((0.0, 0.0, 0.0, 0.0))  # Hace invisible el eje X
ax.yaxis.line.set_color((0.0, 0.0, 0.0, 0.0))  # Hace invisible el eje Y
ax.zaxis.line.set_color((0.0, 0.0, 0.0, 0.0))  # Hace invisible el eje Z

# Ajustar la proporción de los ejes
ax.set_box_aspect([1, 1, 0.01])  

plt.show()