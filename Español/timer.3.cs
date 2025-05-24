using System;
using System.Diagnostics;
using GTA;
using GTA.UI;
using Screen = GTA.UI.Screen;
using GTA.Math;
using System.Windows.Forms;
using System.IO;
using System.Collections.Generic;

public class CronometroConSectores : Script
{
    // Lista de puntos de control que definen la ruta
    private List<Vector3> puntosDeControl = new List<Vector3>();
    private string circuitoSeleccionado; // Circuito seleccionado en el archivo ini

    // Tolerancia para considerar que el jugador ha alcanzado un punto de control
    private float tolerancia; // Tolerancia en unidades de juego

    // Cronómetro para medir el tiempo de la vuelta
    private Stopwatch cronometro;
    private bool cronometroActivo = false;                              // Indica si el cronómetro está activo
    private int indicePuntoActual = 0;                                  // Índice del punto de control actual
    private List<TimeSpan> tiemposDeSectores = new List<TimeSpan>();    // Lista de tiempos por sector

    // Rutas de los archivos (se cargarán desde el archivo .ini)
    private string rutaArchivo;             // Ruta del archivo de vueltas
    private string rutaArchivoTelemetria;   // Ruta del archivo de telemetría

    // Propiedades de la vuelta
    private int numeroVuelta = 0;                       // Número de vuelta actual
    private TimeSpan tiempoUltimoPunto = TimeSpan.Zero; // Tiempo del último punto de control alcanzado
    private string vehiculoUtilizado = "A pie";         // Nombre del vehículo utilizado

    // Telemetría
    private float freno;            // Porcentaje de presión en el freno (0.0 a 1.0)
    private float rpm;              // Revoluciones por minuto del motor
    private int marcha;             // Marcha actual del vehículo
    private float velocidad;        // Velocidad
    private string unidadVelocidad; // Unidad de velocidad
    private Vector3 forwardVector;  // Dirección del vehículo
    private bool isOnAllWheels;     // 4 ruedas en el suelo
    private float fuelLevel;        // Nivel de combustible
    private bool guardarTelemetria; // Guardar telemetría en archivo
    private string colorFreno;      // Color para la barra de freno
    private string colorRPM;        // Color para la barra de RPM
    private string colorMarcha;     // Color para las marchas
    private string colorVelocidad;  // Color para la velocidad
    private string colorTiempoTranscurrido; // Color para el tiempo transcurrido

    // Diccionarios para almacenar las mejores vueltas y mejores tiempos por sector por vehículo
    private Dictionary<string, TimeSpan> mejoresVueltasPorVehiculo = new Dictionary<string, TimeSpan>();
    private Dictionary<string, List<TimeSpan>> mejoresTiemposPorSectorPorVehiculo = new Dictionary<string, List<TimeSpan>>();

    // HUD
    private bool mostrarTelemetria;         // Mostrar telemetría en pantalla
    private bool mostrarTiempoTranscurrido; // Mostrar tiempo transcurrido en pantalla

    // Constructor de la clase
    public CronometroConSectores()
    {
        // Cargar la configuración desde el archivo .ini
        CargarConfiguracion();

        // Suscribir los eventos Tick y KeyDown
        Tick += OnTick;
        KeyDown += OnKeyDown;
    }

    private void CargarConfiguracion()
    {
        // Ruta del archivo .ini
        string configPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "timer.ini");

        // Leer todo el contenido del archivo .ini
        string[] lines = File.ReadAllLines(configPath);

        // Leer las rutas desde el archivo .ini
        rutaArchivo = ObtenerValorIni(lines, "Rutas", "ArchivoVueltas");
        rutaArchivoTelemetria = ObtenerValorIni(lines, "Rutas", "ArchivoTelemetria");

        // Verificar si las rutas son válidas
        if (string.IsNullOrEmpty(rutaArchivo) || string.IsNullOrEmpty(rutaArchivoTelemetria))
        {
            Notification.PostTicker("Error: Las rutas de los archivos no están configuradas correctamente en el archivo .ini.", true, true);
        }

        // Leer configuraciones de visualización
        mostrarTelemetria = ObtenerValorIni(lines, "Ajustes", "MostrarTelemetria", "true").ToLower() == "true";
        mostrarTiempoTranscurrido = ObtenerValorIni(lines, "Ajustes", "MostrarTiempoTranscurrido", "true").ToLower() == "true";

        // Leer unidad de velocidad
        unidadVelocidad = ObtenerValorIni(lines, "Ajustes", "UnidadVelocidad", "kmh").ToLower();

        // Leer colores de telemetría
        colorFreno = ObtenerValorIni(lines, "ColoresTelemetria", "ColorFreno", "~b~");
        colorRPM = ObtenerValorIni(lines, "ColoresTelemetria", "ColorRPM", "~r~");
        colorMarcha = ObtenerValorIni(lines, "ColoresTelemetria", "ColorMarcha", "~s~");
        colorVelocidad = ObtenerValorIni(lines, "ColoresTelemetria", "ColorVelocidad", "~y~");
        colorTiempoTranscurrido = ObtenerValorIni(lines, "ColoresTelemetria", "ColorTiempoTranscurrido", "~s~");

        // Leer guardado de telemetría
        guardarTelemetria = ObtenerValorIni(lines, "Ajustes", "GuardarTelemetria", "true").ToLower() == "true";

        // Leer circuito seleccionado
        circuitoSeleccionado = ObtenerValorIni(lines, "Ajustes", "CircuitoSeleccionado", "Nurburgring Nordschleife");

        // Leer los puntos del circuito seleccionado
        string circuitoData = ObtenerValorIni(lines, "Circuitos", circuitoSeleccionado);

        if (!string.IsNullOrEmpty(circuitoData))
        {
            puntosDeControl.Clear();
            string[] puntos = circuitoData.Split('/');
            foreach (string punto in puntos)
            {
                string[] coords = punto.Split(',');
                if (coords.Length == 3)
                {
                    float x = float.Parse(coords[0].Replace('.', ','));
                    float y = float.Parse(coords[1].Replace('.', ','));
                    float z = float.Parse(coords[2].Replace('.', ','));
                    puntosDeControl.Add(new Vector3(x, y, z));
                }
                else
                {
                    Notification.PostTicker("Coordenadas no validas" + coords, true, true);
                }
            }

            Notification.PostTicker("Circuito seleccionado: " + circuitoSeleccionado, true, true);
        }
        else
        {
            Notification.PostTicker("Circuito " + circuitoSeleccionado + " no encontrado en timer.ini", true, true);
        }

        // Leer la tolerancia desde el archivo .ini
        string toleranciaStr = ObtenerValorIni(lines, "Ajustes", "Tolerancia");
        tolerancia = float.Parse(toleranciaStr.Replace('.', ','));
    }

    // Método auxiliar para obtener valores del archivo .ini
    private string ObtenerValorIni(string[] lines, string section, string key, string valorPorDefecto = "")
    {
        bool dentroSeccion = false;
        foreach (string line in lines)
        {
            // Detectar secciones
            if (line.StartsWith("[" + section + "]"))
            {
                dentroSeccion = true;
            }
            else if (line.StartsWith("[") && dentroSeccion)
            {
                // Salir de la sección al encontrar una nueva sección
                break;
            }
            else if (dentroSeccion && line.Contains("="))
            {
                // Buscar la clave en la sección
                var partes = line.Split('=');
                if (partes[0].Trim() == key)
                {
                    return partes.Length > 1 ? partes[1].Trim() : valorPorDefecto;
                }
            }
        }
        return valorPorDefecto;  // Retornar el valor por defecto si no se encuentra
    }

    // Método que se ejecuta en cada fotograma del juego
    private void OnTick(object sender, EventArgs e)
    {

        // Obtener la posición actual del jugador
        Vector3 posicionJugador = Game.Player.Character.Position;
        // Calcular la distancia al punto de control actual
        float distancia = Vector3.Distance(posicionJugador, puntosDeControl[indicePuntoActual]);

        // Si el jugador está dentro de la tolerancia del punto de control
        if (distancia <= tolerancia)
        {
            if (!cronometroActivo)
            {
                // Obtener el nombre del vehículo si está en uno
                vehiculoUtilizado = ObtenerNombreVehiculo();

                // Incrementar el número de vuelta
                numeroVuelta++;

                // Iniciar cronómetro al pasar por el primer punto de control
                Notification.PostTicker("¡Vuelta " + numeroVuelta + " iniciada!\n" + circuitoSeleccionado, true, true);
                cronometro = Stopwatch.StartNew();
                cronometroActivo = true;
                tiempoUltimoPunto = TimeSpan.Zero;
                indicePuntoActual++;
            }
            else
            {
                // Registrar tiempo del sector al pasar por puntos intermedios o final
                TimeSpan tiempoActual = cronometro.Elapsed;
                TimeSpan tiempoSector = tiempoActual - tiempoUltimoPunto;
                tiemposDeSectores.Add(tiempoSector);
                tiempoUltimoPunto = tiempoActual;

                // Calcular delta para el sector actual
                TimeSpan mejorTiempoSector = ObtenerMejorTiempoSector(vehiculoUtilizado, indicePuntoActual - 1);
                TimeSpan deltaSector = tiempoSector - mejorTiempoSector;

                // Mostrar notificación con el tiempo del sector y el delta
                string mensajeDeltaSector = "";
                if (mejorTiempoSector == TimeSpan.Zero)
                {
                }
                else if (deltaSector < TimeSpan.Zero)
                {
                    mensajeDeltaSector = "~g~¡Mejor tiempo en este sector! Mejoraste: " + FormatearTiempo(-deltaSector) + "~s~";
                }
                else
                {
                    mensajeDeltaSector = "~r~Más lento en este sector por: " + FormatearTiempo(deltaSector) + "~s~";
                }

                Notification.PostTicker("Punto de control " + indicePuntoActual + " alcanzado.\nTiempo del sector: " + FormatearTiempo(tiempoSector) + "\n" + mensajeDeltaSector, true, true);

                // Actualizar el mejor tiempo del sector si es necesario
                if (mejorTiempoSector == TimeSpan.Zero || tiempoSector < mejorTiempoSector)
                {
                    ActualizarMejorTiempoSector(vehiculoUtilizado, indicePuntoActual - 1, tiempoSector);
                }

                if (indicePuntoActual == puntosDeControl.Count - 1)
                {
                    // Si es el último punto de control, finalizar vuelta
                    cronometro.Stop();
                    cronometroActivo = false;
                    TimeSpan tiempoTotalVuelta = cronometro.Elapsed;

                    // Comparar con la mejor vuelta del vehículo actual
                    TimeSpan mejorVuelta = TimeSpan.Zero;
                    if (mejoresVueltasPorVehiculo.ContainsKey(vehiculoUtilizado))
                    {
                        mejorVuelta = mejoresVueltasPorVehiculo[vehiculoUtilizado];
                    }

                    // Calcular el delta (diferencia) con la mejor vuelta
                    TimeSpan deltaVuelta = tiempoTotalVuelta - mejorVuelta;

                    // Mostrar notificación con el tiempo total y el delta
                    string mensajeDeltaVuelta = "";
                    if (mejorVuelta == TimeSpan.Zero)
                    {
                    }
                    else if (deltaVuelta < TimeSpan.Zero)
                    {
                        mensajeDeltaVuelta = "~g~¡Nuevo récord! Mejoraste: " + FormatearTiempo(-deltaVuelta) + "~s~";
                    }
                    else
                    {
                        mensajeDeltaVuelta = "~r~Más lento que el récord por: " + FormatearTiempo(deltaVuelta) + "~s~";
                    }

                    Notification.PostTicker("¡Vuelta " + numeroVuelta + " completada! Tiempo total: " + FormatearTiempo(tiempoTotalVuelta) + "\n" + mensajeDeltaVuelta, true, true);

                    // Actualizar la mejor vuelta si es necesario
                    if (mejorVuelta == TimeSpan.Zero || tiempoTotalVuelta < mejorVuelta)
                    {
                        mejoresVueltasPorVehiculo[vehiculoUtilizado] = tiempoTotalVuelta;
                    }

                    // Guardar tiempos en archivo
                    GuardarTiemposEnArchivo(tiempoTotalVuelta, deltaVuelta);
                    tiemposDeSectores.Clear();
                    indicePuntoActual = 0;
                }
                else
                {
                    // Pasar al siguiente punto de control
                    indicePuntoActual++;
                }
            }
        }

        // Mostrar telemetría y tiempo transcurrido según la configuración
        if (cronometroActivo)
        {
            ActualizarTelemetria();

            // Construir el mensaje a mostrar
            string mensaje = "";

            if (mostrarTelemetria)
            {
                // Crear barras de progreso usando caracteres
                string barraFreno = CrearBarra(freno, 30);
                string barraRPM = CrearBarra(rpm / 10000.0f, 50);

                // Construir el mensaje de telemetría
                mensaje += string.Format(
                    "{4} {5} {6:F0} RPM{7}\n" +
                    "{0}Freno: {1} {2:F0}%{3}\n" +
                    "{12}{9}    {10} {8:F0} {11}",
                    colorFreno, barraFreno, freno * 100, "~s~",
                    colorRPM, barraRPM, rpm, "~s~",
                    velocidad, marcha,
                    colorVelocidad, unidadVelocidad == "mph" ? "mph" : "km/h", colorMarcha
                );
            }

            if (mostrarTiempoTranscurrido)
            {
                TimeSpan tiempoActual = cronometro.Elapsed;
                mensaje += colorTiempoTranscurrido + "\nTiempo transcurrido: " + FormatearTiempo(tiempoActual) + "~s~";
            }

            // Mostrar el mensaje en pantalla si no está vacío
            if (!string.IsNullOrEmpty(mensaje))
            {
                Screen.ShowSubtitle(mensaje);
            }

            // Guardar telemetría en archivo si está habilitado
            if (guardarTelemetria)
            {
                GuardarTelemetriaEnArchivo();
            }
        }
    }

    // Método para obtener el mejor tiempo de un sector para un vehículo
    private TimeSpan ObtenerMejorTiempoSector(string vehiculo, int indiceSector)
    {
        if (mejoresTiemposPorSectorPorVehiculo.ContainsKey(vehiculo) && mejoresTiemposPorSectorPorVehiculo[vehiculo].Count > indiceSector)
        {
            return mejoresTiemposPorSectorPorVehiculo[vehiculo][indiceSector];
        }
        return TimeSpan.Zero;
    }

    // Método para actualizar el mejor tiempo de un sector para un vehículo
    private void ActualizarMejorTiempoSector(string vehiculo, int indiceSector, TimeSpan tiempo)
    {
        if (!mejoresTiemposPorSectorPorVehiculo.ContainsKey(vehiculo))
        {
            mejoresTiemposPorSectorPorVehiculo[vehiculo] = new List<TimeSpan>();
        }

        while (mejoresTiemposPorSectorPorVehiculo[vehiculo].Count <= indiceSector)
        {
            mejoresTiemposPorSectorPorVehiculo[vehiculo].Add(TimeSpan.Zero);
        }

        mejoresTiemposPorSectorPorVehiculo[vehiculo][indiceSector] = tiempo;
    }

    // Método que se ejecuta cuando se presiona una tecla
    private void OnKeyDown(object sender, KeyEventArgs e)
    {
        if (e.KeyCode == Keys.N && cronometroActivo)
        {
            // Cancelar la vuelta si se presiona la tecla N
            cronometro.Stop();
            cronometroActivo = false;
            tiemposDeSectores.Clear();
            indicePuntoActual = 0;
            Notification.PostTicker("¡Vuelta cancelada!", true, true);
        }
    }

    // Método para guardar los tiempos en un archivo de texto
    private void GuardarTiemposEnArchivo(TimeSpan tiempoTotalVuelta, TimeSpan deltaVuelta)
    {
        try
        {
            string directorio = Path.GetDirectoryName(rutaArchivo);
            if (!Directory.Exists(directorio))
            {
                Directory.CreateDirectory(directorio);
            }

            using (StreamWriter sw = new StreamWriter(rutaArchivo, true))
            {
                sw.WriteLine("=======================");
                sw.WriteLine("Vuelta " + numeroVuelta + " - Fecha: " + DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff"));
                sw.WriteLine("=======================");
                sw.WriteLine("  Circuito: " + circuitoSeleccionado);
                sw.WriteLine("  Vehículo: " + vehiculoUtilizado);
                for (int i = 0; i < tiemposDeSectores.Count; i++)
                {
                    TimeSpan mejorTiempoSector = ObtenerMejorTiempoSector(vehiculoUtilizado, i);
                    TimeSpan deltaSector = tiemposDeSectores[i] - mejorTiempoSector;
                    sw.WriteLine("  Sector " + (i + 1) + ": " + FormatearTiempo(tiemposDeSectores[i]) + " (Delta: " + FormatearTiempo(deltaSector) + ")");
                }
                sw.WriteLine("  Tiempo total de la vuelta: " + FormatearTiempo(tiempoTotalVuelta));
                sw.WriteLine("  Delta total: " + FormatearTiempo(deltaVuelta) + "\n");
            }
        }
        catch (Exception e)
        {
            Notification.PostTicker("Error al guardar los tiempos: " + e.Message, true, true);
        }
    }

    private void GuardarTelemetriaEnArchivo()
    {
        try
        {
            using (StreamWriter sw = new StreamWriter(rutaArchivoTelemetria, true))
            {
                sw.WriteLine(string.Format("Telemetría | Fecha: {0} | Circuito: {1} | Vuelta: {2}", DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff"), circuitoSeleccionado, numeroVuelta));
                sw.WriteLine(string.Format("  Velocidad: {0:F1} {1}", velocidad, unidadVelocidad == "mph" ? "mph" : "km/h"));
                sw.WriteLine(string.Format("  RPM: {0:F0}", rpm));
                sw.WriteLine(string.Format("  Marcha: {0}", marcha));
                sw.WriteLine(string.Format("  Freno: {0:F0}%", freno * 100));
                sw.WriteLine(string.Format("  Nivel de combustible: {0:F1}%", fuelLevel));
                sw.WriteLine(string.Format("  Posición: ({0:F2}, {1:F2}, {2:F2})", Game.Player.Character.Position.X, Game.Player.Character.Position.Y, Game.Player.Character.Position.Z));
                sw.WriteLine(string.Format("  Dirección: ({0:F2}, {1:F2}, {2:F2})", forwardVector.X, forwardVector.Y, forwardVector.Z));
                sw.WriteLine(string.Format("  4 ruedas en el suelo: {0}", isOnAllWheels));
            }
        }
        catch (Exception ex)
        {
            Notification.PostTicker("Error al guardar la telemetría: " + ex.Message, true, true);
        }
    }

    // Método para obtener el nombre del vehículo actual
    private string ObtenerNombreVehiculo()
    {
        if (Game.Player.Character.IsInVehicle())
        {
            var vehiculo = Game.Player.Character.CurrentVehicle;
            return vehiculo.DisplayName + " (" + vehiculo.ClassType + ")";
        }
        return "A pie";
    }

    // Método para formatear un TimeSpan en un string legible
    private string FormatearTiempo(TimeSpan tiempo)
    {
        // Verificar si el tiempo es negativo
        bool esNegativo = tiempo < TimeSpan.Zero;
        if (esNegativo)
        {
            tiempo = tiempo.Duration(); // Convertir a valor absoluto
        }

        // Formatear el tiempo
        string tiempoFormateado = string.Format("{0:D2}:{1:D2}:{2:D2}.{3:D3}",
            tiempo.Hours,
            tiempo.Minutes,
            tiempo.Seconds,
            tiempo.Milliseconds);

        // Agregar el signo negativo si es necesario
        if (esNegativo)
        {
            tiempoFormateado = "-" + tiempoFormateado;
        }

        return tiempoFormateado;
    }

    private void ActualizarTelemetria()
    {
        if (Game.Player.Character.IsInVehicle())
        {
            var vehiculo = Game.Player.Character.CurrentVehicle;
            freno = vehiculo.BrakePower;      // Presión en el freno
            rpm = vehiculo.CurrentRPM * 10000; // Convertir a RPM (ajustar según sea necesario)
            marcha = vehiculo.CurrentGear;    // Marcha actual
            velocidad = vehiculo.Speed; // Velocidad en m/s

            // Convertir la velocidad a la unidad seleccionada
            if (unidadVelocidad == "mph")
            {
                velocidad *= 2.23694f; // Convertir de m/s a mph
            }
            else
            {
                velocidad *= 3.6f; // Convertir de m/s a km/h
            }

            forwardVector = vehiculo.ForwardVector; // Dirección del vehículo
            isOnAllWheels = vehiculo.IsOnAllWheels; // Todas las ruedas en el suelo
            fuelLevel = vehiculo.FuelLevel; // Combustible actual
        }
        else
        {
            // Resetear valores si el jugador no está en un vehículo
            freno = 0;
            rpm = 0;
            marcha = 0;
            velocidad = 0;
            forwardVector = Vector3.Zero;
            isOnAllWheels = false;
            fuelLevel = 0;
        }
    }

    // Método para crear una barra de progreso usando caracteres
    private string CrearBarra(float valor, int longitud)
    {
        int cantidad = (int)(valor * longitud);
        return new string('|', cantidad).PadRight(longitud, ' ');
    }
}