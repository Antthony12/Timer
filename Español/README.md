# Timer

Timer es un script para GTA V que permite medir tiempos de vuelta y sectores en circuitos personalizados, mostrando telemetría en pantalla y guardando los resultados en archivos de texto.

## Contexto

Este script nació por la falta de mods funcionales para cronometrar vueltas rápidas en GTA V. Inspirado en [Race Timer](https://www.gta5-mods.com/scripts/race-timer), pero mejorado y actualizado para funcionar correctamente.

## Características

- Cronómetro de vueltas y sectores con notificaciones en pantalla.
- Soporte para múltiples circuitos definidos en un archivo `timer.ini`.
- Sistema de búsqueda de circuitos, cambia de circuito sin salir del juego.
- Registro de mejores tiempos por vehículo y por sector.
- Telemetría en tiempo real: velocidad, RPM, marcha, freno, combustible, dirección y estado de las ruedas.
- Guardado de resultados y telemetría en archivos configurables.
- Personalización de colores y unidades (km/h o mph) desde el archivo de configuración.
- Cancelación de vuelta con la tecla `N`.

## Scripts adicionales en Python

Además del script principal para GTA V, se incluyen dos scripts en Python para analizar y visualizar los datos de telemetría registrados:

- **grafica.py**: Permite visualizar gráficas de velocidad, frenado, RPM y marchas a lo largo del tiempo, marcando los cambios de vuelta. Utiliza una interfaz gráfica con Tkinter y matplotlib para facilitar la exploración de los datos. Es posible exportar los datos a PNG con el botón `Exportar Gráficas`
- **mapa3D.py**: Genera una visualización 3D del recorrido del vehículo utilizando las coordenadas registradas en la telemetría. Es útil para ver el trazado del circuito o la ruta recorrida en el juego.

Ambos scripts leen los datos desde el archivo de telemetría generado por el mod (`telemetriagta5.log`) y requieren tener instaladas las librerías `matplotlib`, `numpy` y `tkinter`.

## Requisitos

### Enhanced
- [Script Hook V](https://dev-c.com/gtav/scripthookv/)
- [Script Hook V .Net Enhanced](https://www.gta5-mods.com/tools/script-hook-v-net-enhanced)

### Legacy
- [Script Hook V](https://dev-c.com/gtav/scripthookv/)
- [Script Hook V .Net Enhanced](https://www.gta5-mods.com/tools/script-hook-v-net-enhanced) or [ScriptHookVDotNet-Nightly](https://github.com/scripthookvdotnet/scripthookvdotnet-nightly/releases)

## Instalación

1. Copia el archivo `Timer.dll` y `timer.ini` en la carpeta `scripts` de tu instalación de GTA V.
2. Configura tus circuitos y preferencias en el archivo `timer.ini`.
3. Asegúrate de tener instalados los requisitos mencionados arriba.

## Configuración

El archivo `timer.ini` permite definir:
- Rutas de archivos de resultados y telemetría.
- Circuitos y sus puntos de control.
- Preferencias de visualización y colores de la telemetría.
- Unidad de velocidad y tolerancia de detección.

### Opciones principales en `timer.ini`:

- **MostrarTelemetria**: Muestra la telemetría del vehículo al iniciar una vuelta. Si está en `false`, se oculta.
- **MostrarTiempoTranscurrido**: Muestra el tiempo transcurrido en la parte inferior central de la pantalla. Si está en `false`, se oculta.
- **GuardarTelemetria**: Si está en `true`, guarda 4 registros por segundo de telemetría en el archivo correspondiente. Recomendado mantener en `false` para ahorrar espacio.
- **UnidadVelocidad**: Elige la unidad de velocidad (km/h o mph).
- **CircuitoSeleccionado**: Selecciona el circuito en el que vas a dar vueltas.
- **Tolerancia**: Define el tamaño del área de detección de meta y sectores (es un círculo, no una línea).
- **ColoresTelemetria**: Personaliza los colores de los elementos de la telemetría.
- **Circuitos**: Añade o elimina circuitos "fácilmente". Ejemplo de un circuito:

```
[Circuitos]
Nurburgring Nordschleife = x1,y1,z1/x2,y2,z2/x3,y3,z3/...
```

Cada trío de coordenadas es un punto de control. El primero es la salida y el último la meta (deben ser iguales para empezar y terminar en el mismo sitio). Se recomienda establecer un mínimo de 3 puntos.

## Uso

- El cronómetro se inicia automáticamente al pasar por el primer punto de control del circuito seleccionado.
- Los tiempos y la telemetría se muestran en pantalla según la configuración.
- Los resultados se guardan en los archivos especificados en el archivo `.ini`.
- Puedes cancelar la vuelta actual presionando la tecla `N`. El script no se activará de nuevo hasta que cruces la línea de meta.
- Al pasar por los sectores, se muestra el tiempo del sector y el delta respecto a la mejor vuelta con el mismo coche en la misma sesión.
- Al terminar una vuelta, se muestra el tiempo y el delta, y la siguiente vuelta comienza automáticamente.
- El archivo gta5.log contiene la información básica de las sesiones.

### Sistema de búsqueda de circuitos

Sistema de búsqueda que te permite cambiar de circuito dinámicamente en el juego:

#### Controles del Sistema de Búsqueda

- `Ctrl + B`: Activar/desactivar modo búsqueda
- `Flecha arriba / 8 (teclado numérico)`: Navegar hacia arriba en la lista
- `Flecha abajo / 2 (teclado numérico)`: Navegar hacia abajo en la lista
- `Enter`: Seleccionar circuito resaltado
- `Retroceder`: Borrar caracteres en la búsqueda

#### Cómo usar el sistema de búsqueda

1. Durante el juego, presiona `Ctrl + B` para activar el modo búsqueda
2. Escribe el nombre del circuito que buscas (ej: "fuji" para encontrar "Fujimi_Kaido")
3. Usa `flecha arriba` y `flecha abajo` para navegar por los resultados
4. Presiona `Enter` para seleccionar el circuito resaltado
5. Para salir sin seleccionar, presiona `Ctrl + B` nuevamente

## Consejos y notas

- Para detener el cronómetro y/o cancelar la vuelta, presiona la tecla `N`.
- Usa `Ctrl + B` para buscar y cambiar circuitos rápidamente sin salir del juego.
- Si encuentras un error, tienes una idea o quieres ayudar, deja un comentario en la [página del mod](https://www.gta5-mods.com/scripts/laps-timer).
- Es un script básico.
- A mí me gusta usarlo como complemento del mod [Ghost Replay](https://www.gta5-mods.com/scripts/ghost-car) y tener la telemetría de las vueltas

> [!IMPORTANT] 
> Para evitar el crecimiento excesivo del archivo de telemetría, se recomienda mantener desactivado el registro o establecer un proceso de limpieza periódica. El tamaño del archivo puede aumentar rápidamente durante sesiones prolongadas.

## Circuitos incluidos

El archivo timer.ini incluye más de 30 circuitos populares:

- [Nürburgring (varias configuraciones)](https://www.gta5-mods.com/maps/nurburgring-nordschleife-circuit-hq) 
- [Circuito de la Sarthe (Le Mans)](https://www.gta5-mods.com/maps/le-mans-circuit-sp-fivem)
- [Spa-Francorchamps](https://www.gta5-mods.com/maps/spa-francorchamps-2025-singleplayer-addon)
- [Monza 1966](https://www.gta5-mods.com/maps/monza-1966-add-on-sp-fivem)
- [Monza (varias versiones)](https://www.gta5-mods.com/maps/monza-modern-day-add-on-sp-fivem)
- [Barcelona-Catalunya](https://www.gta5-mods.com/maps/circuit-de-barcelona-catalunya-vsr-kevin)
- [Imola](https://www.gta5-mods.com/maps/autodromo-enzo-e-dino-ferrari-imola-circuit)
- [Monaco](https://www.gta5-mods.com/maps/monaco-grand-prix)
- [Laguna Seca](https://www.gta5-mods.com/maps/laguna-seca-add-on-fivem)
- [Mount Panorama](https://www.gta5-mods.com/maps/bathurst-mount-panorama-add-on-fivem)
- [Top Gear Test Track](https://www.gta5-mods.com/maps/top-gear-uk-test-track-add-on-sp-fivem)
- [Fujimi Kaido](https://www.gta5-mods.com/maps/fujimi-kaido-overhaul-add-on-fivem)

###### Creo que están configurados en la posición por defecto del mod, sino es así, hazmelo saber por favor.

## Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE.txt](LICENSE.txt) para más detalles.