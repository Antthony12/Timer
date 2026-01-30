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
patron_velocidad_ruedas = re.compile(r"Velocidad de las ruedas: ([\d,]+) km/h")
patron_freno = re.compile(r"Freno: ([\d,]+)%")
patron_rpm = re.compile(r"RPM: ([\d,]+)")
patron_marcha = re.compile(r"Marcha: (\d+)")
patron_vuelta = re.compile(r"Vuelta: (\d+)")
patron_circuito = re.compile(r"Circuito: (.+?) \| Vuelta:")
patron_posicion = re.compile(r"Posición: \(([\d,-]+), ([\d,-]+), ([\d,-]+)\)")
patron_inicio_sesion = re.compile(r"=== Telemetría iniciada (.+?) (.+?) (.+?) ===")
patron_clima = re.compile(r"Clima: (.+)")
patron_hora_juego = re.compile(r"Hora del juego: (\d{2}):(\d{2}):(\d{2})\.(\d{3})")
patron_embrague = re.compile(r"Embrague: (\d+)")
patron_angulo_giro = re.compile(r"Ángulo de giro: ([\d,-]+)º")
patron_turbo = re.compile(r"Turbo: ([\d,-]+)%")
patron_pedal_acelerador = re.compile(r"Pedal Acelerador: ([\d,]+)%")
patron_temperatura_motor = re.compile(r"Temperatura del motor: ([\d,]+)ºC")
patron_acelerador = re.compile(r"Acelerador: ([\d,]+)%")
patron_suciedad = re.compile(r"Nivel de suciedad: ([\d,]+)%")

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
        coincidencia_clima = patron_clima.search(linea)
        coincidencia_hora_juego = patron_hora_juego.search(linea)
        coincidencia_velocidad_ruedas = patron_velocidad_ruedas.search(linea)
        coincidencia_acelerador = patron_acelerador.search(linea)
        coincidencia_embrague = patron_embrague.search(linea)
        coincidencia_angulo_giro = patron_angulo_giro.search(linea)
        coincidencia_turbo = patron_turbo.search(linea)
        coincidencia_pedal_acelerador = patron_pedal_acelerador.search(linea)
        coincidencia_temperatura_motor = patron_temperatura_motor.search(linea)
        coincidencia_suciedad = patron_suciedad.search(linea)

        if coincidencia_tiempo:
            marca_tiempo_actual = coincidencia_tiempo.group(1)

        if coincidencia_vuelta:
            numero_vuelta = int(coincidencia_vuelta.group(1))
            if numero_vuelta not in sesiones[sesion_actual]:
                sesiones[sesion_actual][numero_vuelta] = {
                    "marcas_tiempo": [],
                    "velocidades": [],
                    "velocidades_ruedas": [],
                    "frenos": [],
                    "rpms": [],
                    "marchas": [],
                    "duraciones": [],
                    "posiciones": [],
                    "climas": [],
                    "horas_juego": [],
                    "embragues": [],
                    "angulos_giro": [],
                    "turbos": [],
                    "pedales_acelerador": [],
                    "temperaturas_motor": [],
                    "aceleradores": []
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

        if coincidencia_clima and vuelta_actual in sesiones[sesion_actual]:
            clima = coincidencia_clima.group(1).strip()
            sesiones[sesion_actual][vuelta_actual]["climas"].append(clima)

        if coincidencia_hora_juego and vuelta_actual in sesiones[sesion_actual]:
            hora = int(coincidencia_hora_juego.group(1))
            minuto = int(coincidencia_hora_juego.group(2))
            segundo = int(coincidencia_hora_juego.group(3))
            milisegundo = int(coincidencia_hora_juego.group(4))
            hora_juego_str = f"{hora:02d}:{minuto:02d}:{segundo:02d}.{milisegundo:04d}"
            sesiones[sesion_actual][vuelta_actual]["horas_juego"].append(hora_juego_str)

        if coincidencia_velocidad_ruedas and vuelta_actual in sesiones[sesion_actual]:
            velocidad_ruedas = float(coincidencia_velocidad_ruedas.group(1).replace(",", "."))
            sesiones[sesion_actual][vuelta_actual]["velocidades_ruedas"].append(velocidad_ruedas)

        if coincidencia_acelerador and vuelta_actual in sesiones[sesion_actual]:
            acelerador = float(coincidencia_acelerador.group(1).replace(",", "."))
            sesiones[sesion_actual][vuelta_actual]["aceleradores"].append(acelerador)

        if coincidencia_embrague and vuelta_actual in sesiones[sesion_actual]:
            embrague = int(coincidencia_embrague.group(1))
            sesiones[sesion_actual][vuelta_actual]["embragues"].append(embrague)

        if coincidencia_angulo_giro and vuelta_actual in sesiones[sesion_actual]:
            angulo_giro = float(coincidencia_angulo_giro.group(1).replace(",", "."))
            sesiones[sesion_actual][vuelta_actual]["angulos_giro"].append(angulo_giro)

        if coincidencia_turbo and vuelta_actual in sesiones[sesion_actual]:
            turbo = float(coincidencia_turbo.group(1).replace(",", "."))
            sesiones[sesion_actual][vuelta_actual]["turbos"].append(turbo)

        if coincidencia_pedal_acelerador and vuelta_actual in sesiones[sesion_actual]:
            pedal_acelerador = float(coincidencia_pedal_acelerador.group(1).replace(",", "."))
            sesiones[sesion_actual][vuelta_actual]["pedales_acelerador"].append(pedal_acelerador)

        if coincidencia_temperatura_motor and vuelta_actual in sesiones[sesion_actual]:
            temperatura_motor = float(coincidencia_temperatura_motor.group(1).replace(",", "."))
            sesiones[sesion_actual][vuelta_actual]["temperaturas_motor"].append(temperatura_motor)

        if coincidencia_suciedad and vuelta_actual in sesiones[sesion_actual]:
            suciedad = float(coincidencia_suciedad.group(1).replace(",", "."))
            if "suciedades" not in sesiones[sesion_actual][vuelta_actual]:
                sesiones[sesion_actual][vuelta_actual]["suciedades"] = []
            sesiones[sesion_actual][vuelta_actual]["suciedades"].append(suciedad)

# Función para formatear segundos a mm:ss.ms
def segundos_a_minutos(segundos, pos=None):
    # Formatea segundos a mm:ss.ms
    if pos is not None:
        # Llamado por FuncFormatter
        minutos = int(segundos // 60)
        segundos_restantes = segundos % 60
        segundos_enteros = int(segundos_restantes)
        milisegundos = int((segundos_restantes - segundos_enteros) * 1000)
        return f"{minutos:02d}:{segundos_enteros:02d}.{milisegundos:03d}"
    else:
        # Llamado manualmente
        minutos = int(segundos // 60)
        segundos_restantes = segundos % 60
        segundos_enteros = int(segundos_restantes)
        milisegundos = int((segundos_restantes - segundos_enteros) * 1000)
        return f"{minutos:02d}:{segundos_enteros:02d}.{milisegundos:03d}"

# Calcular la duración de cada punto de datos en relación al inicio de la vuelta
for sesion, datos_vuelta in sesiones.items():
    for numero_vuelta, datos in datos_vuelta.items():
        if datos["marcas_tiempo"]:
            t0 = datos["marcas_tiempo"][0]
            datos["duraciones"] = [(t - t0).total_seconds() for t in datos["marcas_tiempo"]]

# Crear las figuras usando GridSpec con 17 filas:
fig = plt.figure(figsize=(18, 40))

# GridSpec con 17 filas (una para cada gráfica + espacios)
# Orden:
# 0: Tiempos por vuelta
# 1: Espacio
# 2: Delta
# 3: Velocidad media
# 4: Velocidad
# 5: Velocidad de las ruedas
# 6: Acelerador
# 7: Freno
# 8: RPM
# 9: Pedal Acelerador
# 10: Embrague
# 11: Marcha
# 12: Turbo
# 13: Ángulo de giro
# 14: Fuerza G
# 15: Temperatura del motor
# 16: Espacio
# 17: Suciedad
# 18: Espacio
# 19: Mapa 2D
# 20: Espacio final
gs = gridspec.GridSpec(21, 1, height_ratios=[1, 0.2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.3, 1, 0.4, 4, 1])
plt.subplots_adjust(left=0.07, right=0.98, top=0.97, bottom=0, hspace=0.02)

# Definir cada eje (omitimos las filas en blanco)
ax0  = fig.add_subplot(gs[0])   # Tiempos por vuelta
ax1  = fig.add_subplot(gs[2])   # Delta
ax8  = fig.add_subplot(gs[3])   # Velocidad media
ax2  = fig.add_subplot(gs[4])   # Velocidad
ax9  = fig.add_subplot(gs[5])   # Velocidad de las ruedas
ax10 = fig.add_subplot(gs[6])   # Acelerador
ax3  = fig.add_subplot(gs[7])   # Freno
ax4  = fig.add_subplot(gs[8])   # RPM
ax11 = fig.add_subplot(gs[9])   # Pedal Acelerador
ax12 = fig.add_subplot(gs[10])  # Embrague
ax5  = fig.add_subplot(gs[11])  # Marcha
ax13 = fig.add_subplot(gs[12])  # Turbo
ax14 = fig.add_subplot(gs[13])  # Ángulo de giro
ax7  = fig.add_subplot(gs[14])  # Fuerza G
ax15 = fig.add_subplot(gs[15])  # Temperatura del motor
ax16 = fig.add_subplot(gs[17])  # Suciedad
ax6  = fig.add_subplot(gs[19])  # Mapa 2D

def actualizar_grafica():
    global sesion_seleccionada

    print("Actualizando gráfica...")
    selecciones_vueltas = listbox_vueltas.curselection()
    
    print(f"Sesión seleccionada: {sesion_seleccionada}")
    print(f"Vueltas seleccionadas: {selecciones_vueltas}")
    
    if not sesion_seleccionada or not selecciones_vueltas:
        print("No se han seleccionado sesión o vueltas.")
        return
    
    circuito_actual = circuito_por_sesion.get(sesion_seleccionada, "Circuito Desconocido")
    datos_vuelta_sesion = sesiones[sesion_seleccionada]

    print(f"Sesión actual: {sesion_seleccionada}")
    print(f"Circuito actual: {circuito_actual}")
    print(f"Datos de la sesión: {datos_vuelta_sesion.keys()}")
    
    # Limpiar TODOS los ejes
    for ax in [ax0, ax1, ax2, ax3, ax4, ax5, ax6, ax7, ax8, ax9, ax10, ax11, ax12, ax13, ax14, ax15, ax16]:
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
        
        # Obtener las duraciones como referencia para todas las gráficas
        duraciones = datos_vuelta_sesion[numero_vuelta]["duraciones"]
        duracion_len = len(duraciones)
        
        # Graficar en TODAS las gráficas asegurando que los datos tengan la misma longitud
        try:
            print(f"Longitud de duraciones para la vuelta {numero_vuelta}: {duracion_len}")
            
            # Velocidad (ax2) - ya sabemos que existe
            velocidades = datos_vuelta_sesion[numero_vuelta]["velocidades"][:duracion_len]
            ax2.plot(duraciones, velocidades, color=color, alpha=0.7, label=f"Vuelta {numero_vuelta}")
            
            # Freno (ax3)
            frenos = datos_vuelta_sesion[numero_vuelta]["frenos"][:duracion_len] if len(datos_vuelta_sesion[numero_vuelta]["frenos"]) >= duracion_len else [0] * duracion_len
            ax3.plot(duraciones, frenos, color=color, alpha=0.7, label=f"Vuelta {numero_vuelta}")
            
            # RPM (ax4)
            rpms = datos_vuelta_sesion[numero_vuelta]["rpms"][:duracion_len] if len(datos_vuelta_sesion[numero_vuelta]["rpms"]) >= duracion_len else [0] * duracion_len
            ax4.plot(duraciones, rpms, color=color, alpha=0.7, label=f"Vuelta {numero_vuelta}")
            
            # Marcha (ax5)
            marchas = datos_vuelta_sesion[numero_vuelta]["marchas"][:duracion_len] if len(datos_vuelta_sesion[numero_vuelta]["marchas"]) >= duracion_len else [0] * duracion_len
            ax5.plot(duraciones, marchas, color=color, alpha=0.7, label=f"Vuelta {numero_vuelta}")
            
            # Velocidad de las ruedas (ax9)
            velocidades_ruedas = datos_vuelta_sesion[numero_vuelta]["velocidades_ruedas"][:duracion_len] if len(datos_vuelta_sesion[numero_vuelta]["velocidades_ruedas"]) >= duracion_len else [0] * duracion_len
            ax9.plot(duraciones, velocidades_ruedas, color=color, alpha=0.7, label=f"Vuelta {numero_vuelta}")
            
            # Acelerador (ax10)
            aceleradores = datos_vuelta_sesion[numero_vuelta]["aceleradores"][:duracion_len] if len(datos_vuelta_sesion[numero_vuelta]["aceleradores"]) >= duracion_len else [0] * duracion_len
            ax10.plot(duraciones, aceleradores, color=color, alpha=0.7, label=f"Vuelta {numero_vuelta}")
            
            # Pedal Acelerador (ax11)
            pedales_acelerador = datos_vuelta_sesion[numero_vuelta]["pedales_acelerador"][:duracion_len] if len(datos_vuelta_sesion[numero_vuelta]["pedales_acelerador"]) >= duracion_len else [0] * duracion_len
            ax11.plot(duraciones, pedales_acelerador, color=color, alpha=0.7, label=f"Vuelta {numero_vuelta}")
            
            # Embrague (ax12)
            embragues = datos_vuelta_sesion[numero_vuelta]["embragues"][:duracion_len] if len(datos_vuelta_sesion[numero_vuelta]["embragues"]) >= duracion_len else [0] * duracion_len
            ax12.plot(duraciones, embragues, color=color, alpha=0.7, label=f"Vuelta {numero_vuelta}")
            
            # Turbo (ax13)
            turbos = datos_vuelta_sesion[numero_vuelta]["turbos"][:duracion_len] if len(datos_vuelta_sesion[numero_vuelta]["turbos"]) >= duracion_len else [0] * duracion_len
            ax13.plot(duraciones, turbos, color=color, alpha=0.7, label=f"Vuelta {numero_vuelta}")
            
            # Ángulo de giro (ax14)
            angulos_giro = datos_vuelta_sesion[numero_vuelta]["angulos_giro"][:duracion_len] if len(datos_vuelta_sesion[numero_vuelta]["angulos_giro"]) >= duracion_len else [0] * duracion_len
            ax14.plot(duraciones, angulos_giro, color=color, alpha=0.7, label=f"Vuelta {numero_vuelta}")
            
            # Temperatura del motor (ax15)
            temperaturas_motor = datos_vuelta_sesion[numero_vuelta]["temperaturas_motor"][:duracion_len] if len(datos_vuelta_sesion[numero_vuelta]["temperaturas_motor"]) >= duracion_len else [0] * duracion_len
            ax15.plot(duraciones, temperaturas_motor, color=color, alpha=0.7, label=f"Vuelta {numero_vuelta}")
            
        except Exception as e:
            print(f"Error al graficar la vuelta {numero_vuelta}: {e}")
            import traceback
            traceback.print_exc()
        
        # Configurar ticks de marchas
        if marchas and any(m != 0 for m in marchas):
            marchas_filtradas = [m for m in marchas if m != 0]
            if marchas_filtradas:
                ax5.set_yticks(range(int(min(marchas_filtradas)), int(max(marchas_filtradas)) + 1))
        
        # Recoger datos para la gráfica de tiempos por vuelta y de deltas
        if duraciones:
            tiempo_total = duraciones[-1]
            numeros_vuelta_linea.append(numero_vuelta)
            tiempos_totales.append(tiempo_total)
            numeros_vuelta_delta.append(numero_vuelta)
            tiempos_vuelta.append(tiempo_total)

        # Calcular velocidad media para esta vuelta
        if numero_vuelta in datos_vuelta_sesion and velocidades:
            velocidad_media = np.mean(velocidades)
            numeros_vuelta_velocidad.append(numero_vuelta)
            velocidades_medias.append(velocidad_media)

    # Gráfica de tiempos por vuelta (ax0)
    if numeros_vuelta_linea:
        ax0.plot(numeros_vuelta_linea, tiempos_totales, marker='o', linestyle='none',
                color='tab:orange', label="Tiempo por vuelta")
        
        ax0.yaxis.set_major_formatter(FuncFormatter(segundos_a_minutos))
        ax0.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    
    ax0.set_xlabel("Vuelta")
    ax0.set_ylabel("Tiempo (mm:ss.ms)")
    ax0.grid()
    ax0.legend()

    # Gráfica de deltas (ax1)
    if tiempos_vuelta:
        mejor_tiempo = min(tiempos_vuelta)
        deltas = [t - mejor_tiempo for t in tiempos_vuelta]
        ax1.bar(numeros_vuelta_delta, deltas, color='tab:red')
    ax1.set_ylabel("Delta (s)")
    ax1.grid(axis="y")
    ax1.set_xticks([])

    # Configurar límites y formato para todas las gráficas temporales
    for ax in [ax2, ax3, ax4, ax5, ax7, ax9, ax10, ax11, ax12, ax13, ax14, ax15]:
        ax.set_xlim(inicio, fin)
        ax.xaxis.set_major_formatter(FuncFormatter(segundos_a_minutos))
    
    # Ocultar etiquetas X en las gráficas superiores
    for ax in [ax2, ax3, ax4, ax5, ax9, ax10, ax11, ax12, ax13, ax14]:
        ax.set_xticks([])

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

    # Fuerza G (ax7)
    for idx, numero_vuelta in enumerate(vueltas_seleccionadas):
        if numero_vuelta not in datos_vuelta_sesion:
            continue
        color = colores[idx % len(colores)]
        lista_velocidades = datos_vuelta_sesion[numero_vuelta]["velocidades"]
        lista_duraciones = datos_vuelta_sesion[numero_vuelta]["duraciones"]
        
        # Asegurar que tengan la misma longitud
        min_len = min(len(lista_velocidades), len(lista_duraciones))
        lista_velocidades = lista_velocidades[:min_len]
        lista_duraciones = lista_duraciones[:min_len]
        
        if min_len >= 2:
            velocidades_mps = np.array(lista_velocidades) * 1000/3600
            duraciones = np.array(lista_duraciones)
            aceleracion = np.diff(velocidades_mps) / np.diff(duraciones)
            tiempos_medios = (duraciones[:-1] + duraciones[1:]) / 2
            fuerza_g = aceleracion / 9.81
            ax7.plot(tiempos_medios, fuerza_g, color=color, alpha=0.7, label=f"Vuelta {numero_vuelta}")
    
    ax7.set_ylabel("Fuerza G")
    ax7.grid()
    ax7.set_xticks([])

    # Velocidad de las ruedas (ax9)
    ax9.set_ylabel("Vel. Ruedas (km/h)")
    ax9.grid()
    
    # Acelerador (ax10)
    ax10.set_ylabel("Acelerador (%)")
    ax10.grid()
    
    # Pedal Acelerador (ax11)
    ax11.set_ylabel("Pedal Acel. (%)")
    ax11.grid()
    
    # Embrague (ax12)
    ax12.set_ylabel("Embrague")
    ax12.grid()
    
    # Turbo (ax13)
    ax13.set_ylabel("Turbo (%)")
    ax13.grid()
    
    # Ángulo de giro (ax14)
    ax14.set_ylabel("Ángulo (º)")
    ax14.grid()
    
    # Temperatura del motor (ax15)
    ax15.set_xlim(inicio, fin)
    ax15.xaxis.set_major_formatter(FuncFormatter(segundos_a_minutos))
    ax15.set_ylabel("Temp. Motor (ºC)")
    ax15.set_xlabel("Tiempo (mm:ss.ms)")
    ax15.grid()

    # Suciedad (ax16)
    tiempo_acumulado = 0
    todas_x = []
    todas_y = []
    colores_segmentos = []
    limites_vueltas = []  # Para almacenar los límites de cada vuelta
    
    for idx, numero_vuelta in enumerate(vueltas_seleccionadas):
        if numero_vuelta not in datos_vuelta_sesion:
            continue
        
        color = colores[idx % len(colores)]
        
        # Obtener datos de suciedad y duraciones para esta vuelta
        if "suciedades" in datos_vuelta_sesion[numero_vuelta] and datos_vuelta_sesion[numero_vuelta]["suciedades"]:
            suciedades = datos_vuelta_sesion[numero_vuelta]["suciedades"]
            duraciones_vuelta = datos_vuelta_sesion[numero_vuelta]["duraciones"]
            
            # Asegurar que tengan la misma longitud
            min_len = min(len(suciedades), len(duraciones_vuelta))
            if min_len == 0:
                continue
                
            suciedades = suciedades[:min_len]
            duraciones_vuelta = duraciones_vuelta[:min_len]
            
            # Ajustar las duraciones para que sean continuas
            duraciones_ajustadas = [t + tiempo_acumulado for t in duraciones_vuelta]
            
            # Almacenar los datos ajustados
            todas_x.extend(duraciones_ajustadas)
            todas_y.extend(suciedades)
            
            # Almacenar el color para este segmento
            colores_segmentos.extend([color] * min_len)
            
            # Almacenar el límite de esta vuelta
            limites_vueltas.append({
                'numero': numero_vuelta,
                'color': color,
                'inicio': tiempo_acumulado,
                'fin': tiempo_acumulado + duraciones_vuelta[-1] if duraciones_vuelta else tiempo_acumulado,
                'suciedad_inicio': suciedades[0] if suciedades else 0,
                'suciedad_fin': suciedades[-1] if suciedades else 0
            })
            
            # Actualizar tiempo acumulado para la siguiente vuelta
            tiempo_acumulado += duraciones_vuelta[-1] if duraciones_vuelta else 0
    
    # Graficar la línea continua de suciedad
    if todas_x and todas_y:
        # Crear la línea principal
        ax16.plot(todas_x, todas_y, color='gray', linewidth=1, alpha=0.3)
        
        # Superponer segmentos coloreados por vuelta
        # Para esto necesitamos dividir la línea en segmentos por vuelta
        start_idx = 0
        for limite in limites_vueltas:
            # Encontrar los índices de los puntos que pertenecen a esta vuelta
            puntos_vuelta = []
            tiempos_vuelta = []
            
            for i in range(len(todas_x)):
                if limite['inicio'] <= todas_x[i] <= limite['fin']:
                    puntos_vuelta.append(todas_y[i])
                    tiempos_vuelta.append(todas_x[i])
            
            if tiempos_vuelta and puntos_vuelta:
                ax16.plot(tiempos_vuelta, puntos_vuelta, 
                         color=limite['color'], 
                         linewidth=2, 
                         label=f"Vuelta {limite['numero']}")
        
        # Añadir marcadores en los límites entre vueltas
        for i in range(1, len(limites_vueltas)):
            limite_anterior = limites_vueltas[i-1]
            limite_actual = limites_vueltas[i]
            
            # Dibujar una línea vertical punteada en el límite
            ax16.axvline(x=limite_actual['inicio'], 
                        color='black', 
                        linestyle='--', 
                        alpha=0.5, 
                        linewidth=0.5)
            
            # Añadir etiqueta del número de vuelta
            ax16.text(limite_actual['inicio'], 
                     ax16.get_ylim()[1] * 0.95,  # Cerca del borde superior
                     f"V{limite_actual['numero']}", 
                     ha='center', 
                     va='top',
                     fontsize=8,
                     bbox=dict(boxstyle="round,pad=0.3", 
                              facecolor=limite_actual['color'], 
                              alpha=0.7))
    
    # Configurar la gráfica de suciedad
    if todas_x:
        ax16.set_xlim(min(todas_x), max(todas_x))
    else:
        ax16.set_xlim(inicio, fin)
    
    ax16.set_ylabel("Suciedad (%)")
    ax16.set_xlabel("Tiempo acumulado de sesión (s)")
    ax16.grid(True, alpha=0.3)

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
        f"Vuelta: {sel.target[0]:.0f}\nTiempo: {segundos_a_minutos(sel.target[1], None)}"))
    
    cursor1 = mplcursors.cursor(ax1, hover=True)
    cursor1.connect("add", lambda sel: sel.annotation.set_text(
        f"Vuelta: {sel.target[0]:.0f}\nDelta: {sel.target[1]:.2f} s"))
    
    cursor2 = mplcursors.cursor(ax2, hover=True)
    cursor2.connect("add", lambda sel: 
        sel.annotation.set_text(
            obtener_tooltip_completo(
                sesion_seleccionada, 
                int(sel.artist.get_label().split()[-1]),
                sel.target[0],  # Tiempo relativo
                f"{sel.artist.get_label()}\nTiempo: {sel.target[0]:.2f} s\nVelocidad: {sel.target[1]:.2f} km/h"
            )
        ))
    
    cursor3 = mplcursors.cursor(ax3, hover=True)
    cursor3.connect("add", lambda sel: 
        sel.annotation.set_text(
            obtener_tooltip_completo(
                sesion_seleccionada,
                int(sel.artist.get_label().split()[-1]),
                sel.target[0],
                f"{sel.artist.get_label()}\nTiempo: {sel.target[0]:.2f} s\nFreno: {sel.target[1]:.2f} %"
            )
        ))
    
    cursor4 = mplcursors.cursor(ax4, hover=True)
    cursor4.connect("add", lambda sel: 
        sel.annotation.set_text(
            obtener_tooltip_completo(
                sesion_seleccionada,
                int(sel.artist.get_label().split()[-1]),
                sel.target[0],
                f"{sel.artist.get_label()}\nTiempo: {sel.target[0]:.2f} s\nRPM: {sel.target[1]:.0f}"
            )
        ))
    
    cursor5 = mplcursors.cursor(ax5, hover=True)
    cursor5.connect("add", lambda sel: 
        sel.annotation.set_text(
            obtener_tooltip_completo(
                sesion_seleccionada,
                int(sel.artist.get_label().split()[-1]),
                sel.target[0],
                f"{sel.artist.get_label()}\nTiempo: {sel.target[0]:.2f} s\nMarcha: {sel.target[1]:.0f}"
            )
        ))
    
    cursor7 = mplcursors.cursor(ax7, hover=True)
    cursor7.connect("add", lambda sel: 
        sel.annotation.set_text(
            f"Fuerza G: {sel.target[1]:.2f}\n" +
            obtener_info_clima_hora(sesion_seleccionada, vueltas_seleccionadas[0], sel.target[0])
        ))
    
    cursor8 = mplcursors.cursor(ax8, hover=True)
    cursor8.connect("add", lambda sel: sel.annotation.set_text(
        f"Vuelta: {sel.target[0]:.0f}\nVelocidad Media: {sel.target[1]:.2f} km/h"))
    
    cursor6 = mplcursors.cursor(ax6, hover=True)
    cursor6.connect("add", lambda sel: 
        sel.annotation.set_text(
            obtener_tooltip_trazada(
                sesion_seleccionada,
                int(sel.artist.get_label().split()[-1]),
                sel.target[0],  # Coordenada X
                sel.target[1]   # Coordenada Y
            )
        ))
    
    cursor9 = mplcursors.cursor(ax9, hover=True)
    cursor9.connect("add", lambda sel: 
        sel.annotation.set_text(
            obtener_tooltip_completo(
                sesion_seleccionada,
                int(sel.artist.get_label().split()[-1]),
                sel.target[0],
                f"{sel.artist.get_label()}\nTiempo: {sel.target[0]:.2f} s\nVel. Ruedas: {sel.target[1]:.2f} km/h"
            )
        ))

    cursor10 = mplcursors.cursor(ax10, hover=True)
    cursor10.connect("add", lambda sel: 
        sel.annotation.set_text(
            obtener_tooltip_completo(
                sesion_seleccionada,
                int(sel.artist.get_label().split()[-1]),
                sel.target[0],
                f"{sel.artist.get_label()}\nTiempo: {sel.target[0]:.2f} s\nAcelerador: {sel.target[1]:.2f} %"
            )
        ))

    cursor11 = mplcursors.cursor(ax11, hover=True)
    cursor11.connect("add", lambda sel: 
        sel.annotation.set_text(
            obtener_tooltip_completo(
                sesion_seleccionada,
                int(sel.artist.get_label().split()[-1]),
                sel.target[0],
                f"{sel.artist.get_label()}\nTiempo: {sel.target[0]:.2f} s\nPedal Acel.: {sel.target[1]:.2f} %"
            )
        ))

    cursor12 = mplcursors.cursor(ax12, hover=True)
    cursor12.connect("add", lambda sel: 
        sel.annotation.set_text(
            obtener_tooltip_completo(
                sesion_seleccionada,
                int(sel.artist.get_label().split()[-1]),
                sel.target[0],
                f"{sel.artist.get_label()}\nTiempo: {sel.target[0]:.2f} s\nEmbrague: {sel.target[1]:.0f}"
            )
        ))

    cursor13 = mplcursors.cursor(ax13, hover=True)
    cursor13.connect("add", lambda sel: 
        sel.annotation.set_text(
            obtener_tooltip_completo(
                sesion_seleccionada,
                int(sel.artist.get_label().split()[-1]),
                sel.target[0],
                f"{sel.artist.get_label()}\nTiempo: {sel.target[0]:.2f} s\nTurbo: {sel.target[1]:.2f} %"
            )
        ))

    cursor14 = mplcursors.cursor(ax14, hover=True)
    cursor14.connect("add", lambda sel: 
        sel.annotation.set_text(
            obtener_tooltip_completo(
                sesion_seleccionada,
                int(sel.artist.get_label().split()[-1]),
                sel.target[0],
                f"{sel.artist.get_label()}\nTiempo: {sel.target[0]:.2f} s\nÁngulo: {sel.target[1]:.2f}º"
            )
        ))

    cursor15 = mplcursors.cursor(ax15, hover=True)
    cursor15.connect("add", lambda sel: 
        sel.annotation.set_text(
            obtener_tooltip_completo(
                sesion_seleccionada,
                int(sel.artist.get_label().split()[-1]),
                sel.target[0],
                f"{sel.artist.get_label()}\nTiempo: {sel.target[0]:.2f} s\nTemp. Motor: {sel.target[1]:.2f}ºC"
            )
        ))

    cursor16 = mplcursors.cursor(ax16, hover=True)
    cursor16.connect("add", lambda sel: 
        sel.annotation.set_text(
            obtener_tooltip_suciedad_continua(
                limites_vueltas,
                sel.target[0],  # Tiempo
                sel.target[1]   # Suciedad
            )
        ))
    
    canvas_fig.draw()

def obtener_info_clima_hora(sesion, numero_vuelta, tiempo_relativo):
    # Obtiene información de clima y hora del juego formateada
    datos_vuelta = sesiones[sesion][numero_vuelta]
    
    if not datos_vuelta["duraciones"]:
        return ""
    
    # Buscar el índice más cercano
    duraciones = np.array(datos_vuelta["duraciones"])
    idx = (np.abs(duraciones - tiempo_relativo)).argmin()
    
    # Obtener datos
    clima = datos_vuelta["climas"][idx] if idx < len(datos_vuelta["climas"]) else "Desconocido"
    hora_juego = datos_vuelta["horas_juego"][idx] if idx < len(datos_vuelta["horas_juego"]) else "Desconocida"
    
    return f"Clima: {clima}\nHora juego: {hora_juego}"

def obtener_tooltip_completo(sesion, numero_vuelta, tiempo_relativo, texto_base):
    # Combina el texto base con información de clima y hora del juego
    info_adicional = obtener_info_clima_hora(sesion, numero_vuelta, tiempo_relativo)
    return f"{texto_base}\n{info_adicional}"

def obtener_tooltip_trazada(sesion, numero_vuelta, coord_x, coord_y):
    # Obtiene información para mostrar en tooltips de las trazadas
    datos_vuelta = sesiones[sesion][numero_vuelta]
    
    if not datos_vuelta.get("posiciones"):
        return f"Vuelta {numero_vuelta}\nSin datos de posición"
    
    # Buscar el punto más cercano en las posiciones
    posiciones = datos_vuelta["posiciones"]
    distancias = []
    
    for i, (x, y, z) in enumerate(posiciones):
        distancia = np.sqrt((x - coord_x)**2 + (y - coord_y)**2)
        distancias.append((i, distancia))
    
    # Ordenar por distancia y tomar el más cercano
    distancias.sort(key=lambda x: x[1])
    idx_cercano = distancias[0][0] if distancias else 0
    
    # Obtener datos en ese punto
    velocidad = datos_vuelta["velocidades"][idx_cercano] if idx_cercano < len(datos_vuelta["velocidades"]) else 0
    tiempo_transcurrido = datos_vuelta["duraciones"][idx_cercano] if idx_cercano < len(datos_vuelta["duraciones"]) else 0
    clima = datos_vuelta["climas"][idx_cercano] if idx_cercano < len(datos_vuelta["climas"]) else "Desconocido"
    hora_juego = datos_vuelta["horas_juego"][idx_cercano] if idx_cercano < len(datos_vuelta["horas_juego"]) else "Desconocida"
    
    # Formatear el tiempo transcurrido
    tiempo_formateado = segundos_a_minutos(tiempo_transcurrido, None)
    
    return (f"Vuelta {numero_vuelta}\n"
            f"Velocidad: {velocidad:.1f} km/h\n"
            f"Tiempo: {tiempo_formateado}\n"
            f"Clima: {clima}\n"
            f"Hora juego: {hora_juego}")

def obtener_tooltip_suciedad_continua(limites_vueltas, tiempo, suciedad_valor):
    # Encontrar en qué vuelta estamos basado en el tiempo
    for i, limite in enumerate(limites_vueltas):
        if limite['inicio'] <= tiempo <= limite['fin']:
            tiempo_en_vuelta = tiempo - limite['inicio']
            
            # Calcular porcentaje completado de la vuelta
            duracion_vuelta = limite['fin'] - limite['inicio']
            porcentaje_completado = (tiempo_en_vuelta / duracion_vuelta * 100) if duracion_vuelta > 0 else 0
            
            return (f"Vuelta: {limite['numero']}\n"
                    f"Suciedad: {suciedad_valor:.1f}%\n"
                    f"Tiempo en vuelta: {tiempo_en_vuelta:.1f}s\n"
                    f"Completado: {porcentaje_completado:.1f}%")
    
    return "No se encontró información para este tiempo"

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
root.geometry("1800x900")
ancho_pantalla = root.winfo_screenwidth()
alto_pantalla = root.winfo_screenheight()
x = (ancho_pantalla - 1800) // 2
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