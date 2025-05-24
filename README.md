# Timer

Timer es un script para GTA V (utilizando ScriptHookVDotNet) que permite medir tiempos de vuelta y sectores en circuitos personalizados, mostrando telemetría en pantalla y guardando los resultados en archivos de texto.

## Contexto

Este script nació por la falta de mods funcionales para cronometrar vueltas rápidas en GTA V. Inspirado en Race Timer (https://www.gta5-mods.com/scripts/race-timer), pero mejorado y actualizado para funcionar correctamente.

## Características

- Cronómetro de vueltas y sectores con notificaciones en pantalla.
- Soporte para múltiples circuitos definidos en un archivo `timer.ini`.
- Registro de mejores tiempos por vehículo y por sector.
- Telemetría en tiempo real: velocidad, RPM, marcha, freno, combustible, dirección y estado de las ruedas.
- Guardado de resultados y telemetría en archivos configurables.
- Personalización de colores y unidades (km/h o mph) desde el archivo de configuración.
- Cancelación de vuelta con la tecla `N`.

## Scripts adicionales en Python

Además del script principal para GTA V, se incluyen dos scripts en Python para analizar y visualizar los datos de telemetría registrados:

- **grafica.py**: Permite visualizar gráficas de velocidad, frenado, RPM y marchas a lo largo del tiempo, marcando los cambios de vuelta. Utiliza una interfaz gráfica con Tkinter y matplotlib para facilitar la exploración de los datos.
- **mapa3D.py**: Genera una visualización 3D del recorrido del vehículo utilizando las coordenadas registradas en la telemetría. Es útil para ver el trazado del circuito o la ruta recorrida en el juego.

Ambos scripts leen los datos desde el archivo de telemetría generado por el mod (`telemetriagta5.txt`) y requieren tener instaladas las librerías `matplotlib`, `numpy` y `tkinter` (para grafica.py).

## Requisitos

- [Script Hook V](https://dev-c.com/gtav/scripthookv/)
- [ScriptHookVDotNet-Nightly](https://github.com/scripthookvdotnet/scripthookvdotnet-nightly/releases)

## Instalación

1. Copia el archivo `Timer.dll` en la carpeta `scripts` de tu instalación de GTA V.
2. Coloca el archivo `timer.ini` en la misma carpeta que el script y configura tus circuitos y preferencias.
3. Asegúrate de tener instalados los requisitos mencionados arriba.

## Configuración

El archivo `timer.ini` permite definir:
- Rutas de archivos de resultados y telemetría.
- Circuitos y sus puntos de control.
- Preferencias de visualización y colores.
- Unidad de velocidad y tolerancia de detección.

### Opciones principales en `timer.ini`:

- **MostrarTelemetria**: Muestra la telemetría del vehículo al iniciar una vuelta. Si está en `false`, se oculta.
- **MostrarTiempoTranscurrido**: Muestra el tiempo transcurrido en la parte inferior central de la pantalla. Si está en `false`, se oculta.
- **GuardarTelemetria**: Si está en `true`, guarda 4 registros por segundo de telemetría en el archivo correspondiente. Recomendado mantener en `false` para ahorrar espacio.
- **UnidadVelocidad**: Elige la unidad de velocidad (km/h o mph).
- **CircuitoSeleccionado**: Selecciona el circuito en el que vas a dar vueltas.
- **Tolerancia**: Define el tamaño del área de detección de meta y sectores (es un círculo, no una línea).
- **ColoresTelemetria**: Personaliza los colores de los elementos de la telemetría.
- **Circuitos**: Añade o elimina circuitos fácilmente. Ejemplo de sección:

```
[Circuitos]
Nurburgring Nordschleife = x1,y1,z1/x2,y2,z2/x3,y3,z3/...
```

Cada trío de coordenadas es un punto de control. El primero es la salida y el último la meta (deben ser iguales para empezar y terminar en el mismo sitio). Se recomienda mínimo 3 puntos.

> **Nota:** Si modificas el archivo `.ini` mientras el juego está abierto, recarga los scripts para aplicar los cambios. Al recargar, los tiempos y vueltas se reinician.

## Uso

- El cronómetro se inicia automáticamente al pasar por el primer punto de control del circuito seleccionado.
- Los tiempos y la telemetría se muestran en pantalla según la configuración.
- Los resultados se guardan en los archivos especificados en el archivo `.ini`.
- Puedes cancelar la vuelta actual presionando la tecla `N`. El script no se activará de nuevo hasta que cruces la línea de meta.
- Al pasar por los sectores, se muestra el tiempo del sector y el delta respecto a la mejor vuelta con el mismo coche en la misma sesión.
- Al terminar una vuelta, se muestra el tiempo y el delta, y la siguiente vuelta comienza automáticamente.

## Consejos y notas

- Para detener el cronómetro y cancelar la vuelta, presiona la tecla "N".
- Si encuentras un error, tienes una idea o quieres ayudar, deja un comentario en la [página del mod](https://www.gta5-mods.com/scripts/laps-timer).
- Es un script básico y en constante mejora.

## Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE.txt](LICENSE.txt) para más detalles.