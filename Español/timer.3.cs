using System;
using System.Diagnostics;
using GTA;
using GTA.UI;
using Screen = GTA.UI.Screen;
using GTA.Math;
using System.Windows.Forms;
using System.IO;
using System.Collections.Generic;
using System.Linq;
using GTA.Chrono;

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
    // https://github.com/scripthookvdotnet/scripthookvdotnet/blob/main/source/scripting_v3/GTA/Entities/Vehicles/Vehicle.cs
    private float pedalAcelerador;          // Posición del pedal del acelerador (0.0 a 1.0)
    private float acelerador;               // Porcentaje de presión en el acelerador (0.0 a 1.0)
    private float freno;                    // Porcentaje de presión en el freno (0.0 a 1.0)
    private float rpm;                      // Revoluciones por minuto del motor
    private float embrague;                 // Porcentaje de presión en el embrague (0.0 a 1.0)
    private int marcha;                     // Marcha actual del vehículo
    private bool frenoMano;                 // Freno de mano activado
    private float anguloGiro;               // Ángulo de giro de la dirección
    private float turbo;                    // Nivel de turbo
    private float velocidad;                // Velocidad
    private float velocidadRuedas;          // Velocidad de las ruedas
    private Vector3 velocidad2;             // Velocidad vectorial
    private Vector3 forwardVector;          // Dirección del vehículo
    private bool todasRuedasTocandoSuelo;   // 4 ruedas en el suelo
    private float nivelCombustible;         // Nivel de combustible
    private float nivelAceite;              // Nivel de aceite
    private float temperaturaMotor;         // Temperatura del motor
    private bool cocheDetenido;             // Si el coche está detenido
    private bool coheteActivado;            // Si el cohete está activado
    private bool motorArrancando;           // Si el cohete está activado
    private bool motorEncendido;            // Si el cohete está activado
    private bool lucesEncendidas;           // Si las luces están encendidas
    private bool lucesLargasEncendidas;     // Si las luces largas están encendidas
    private bool intermitenteIzquierdo;     // Si el intermitente izquierdo está activado
    private bool intermitenteDerecho;       // Si el intermitente derecho está activado

    private float nivelSuciedad;            // Nivel de suciedad del vehículo

    private float saludMotor;               // Salud del motor
    private float saludChasis;              // Salud del chasis
    private float saludTanqueCombustible;   // Salud del sistema de combustible

    private int horaJuego;                  // Hora del juego
    private int minutoJuego;                // Minuto del juego
    private int segundoJuego;               // Segundo del juego
    private int milisegundoJuego;           // Milisegundo del juego
    private Weather clima;                  // Clima actual

    // Variables de configuración
    private string unidadVelocidad;         // Unidad de velocidad
    private bool guardarTelemetria;         // Guardar telemetría en archivo

    // Colores de telemetría
    private string colorFreno;              // Color para la barra de freno
    private string colorAcelerador;         // Color para la barra de acelerador
    private string colorRPM;                // Color para la barra de RPM
    private string colorMarcha;             // Color para las marchas
    private string colorVelocidad;          // Color para la velocidad
    private string colorTiempoTranscurrido; // Color para el tiempo transcurrido

    // Diccionarios para almacenar las mejores vueltas y mejores tiempos por sector por vehículo
    private Dictionary<string, TimeSpan> mejoresVueltasPorVehiculo = new Dictionary<string, TimeSpan>();
    private Dictionary<string, List<TimeSpan>> mejoresTiemposPorSectorPorVehiculo = new Dictionary<string, List<TimeSpan>>();

    // HUD
    private bool mostrarTelemetria;         // Mostrar telemetría en pantalla
    private bool mostrarTiempoTranscurrido; // Mostrar tiempo transcurrido en pantalla

    // Diccionario para almacenar todos los circuitos cargados
    private Dictionary<string, List<Vector3>> circuitosCargados = new Dictionary<string, List<Vector3>>();
    private bool cargarTodosCircuitos = true; // Bandera para controlar la carga de circuitos

    // Variables para el modo de búsqueda de circuito
    private bool modoBusquedaCircuito = false;
    private string busquedaActual = "";
    private List<string> circuitosFiltrados = new List<string>();
    private int indiceSeleccion = 0;
    private string ultimoCircuito = "";

    // Inicializar lista para acumular telemetría antes de guardarla
    private List<string> telemetriaAcumulada = new List<string>();

    // Constructor de la clase
    public CronometroConSectores()
    {
        // Cargar todos los circuitos disponibles
        CargarTodosLosCircuitos();

        // Cargar la configuración
        CargarConfiguracion();

        // Suscribir los eventos Tick y KeyDown
        Tick += OnTick;
        KeyDown += OnKeyDown;
    }

    // Función para cargar todos los circuitos desde el archivo timer.ini
    private void CargarTodosLosCircuitos()
    {
        if (!cargarTodosCircuitos) return;

        string configPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "timer.ini");
        if (!File.Exists(configPath))
        {
            Notification.PostTicker("Archivo timer.ini no encontrado.", true, true);
            return;
        }

        string[] lines = File.ReadAllLines(configPath);
        circuitosCargados.Clear();

        bool enSeccionCircuitos = false;
        string nombreCircuitoActual = "";

        foreach (string line in lines)
        {
            string linea = line.Trim();

            // Detectar sección de circuitos
            if (linea.StartsWith("[Circuitos]"))
            {
                enSeccionCircuitos = true;
                continue;
            }
            else if (linea.StartsWith("[") && enSeccionCircuitos)
            {
                // Salir de la sección si encontramos otra sección
                enSeccionCircuitos = false;
            }

            if (enSeccionCircuitos && linea.Contains("="))
            {
                // Procesar línea de circuito
                var partes = linea.Split('=');
                if (partes.Length == 2)
                {
                    nombreCircuitoActual = partes[0].Trim();
                    string circuitoData = partes[1].Trim();

                    if (!string.IsNullOrEmpty(nombreCircuitoActual) && !nombreCircuitoActual.StartsWith(";"))
                    {
                        // Parsear las coordenadas del circuito
                        List<Vector3> puntosCircuito = ParsearCoordenadasCircuito(circuitoData, nombreCircuitoActual);
                        if (puntosCircuito.Count > 0)
                        {
                            circuitosCargados[nombreCircuitoActual] = puntosCircuito;
                        }
                    }
                }
            }
        }

        Notification.PostTicker("Cargados " + circuitosCargados.Count + " circuitos", true, true);
    }

    // Función para parsear las coordenadas de un circuito desde una cadena
    private List<Vector3> ParsearCoordenadasCircuito(string circuitoData, string nombreCircuito)
    {
        List<Vector3> puntos = new List<Vector3>();
        string[] puntosStr = circuitoData.Split('/');

        foreach (string punto in puntosStr)
        {
            string[] coords = punto.Split(',');
            if (coords.Length == 3)
            {
                try
                {
                    float x = float.Parse(coords[0].Replace('.', ','));
                    float y = float.Parse(coords[1].Replace('.', ','));
                    float z = float.Parse(coords[2].Replace('.', ','));
                    puntos.Add(new Vector3(x, y, z));
                }
                catch (Exception ex)
                {
                    Notification.PostTicker("Error parseando coordenadas del circuito " + nombreCircuito + ": " + ex.Message, true, true);
                }
            }
        }

        return puntos;
    }

    // Función para cargar la configuración desde el archivo .ini
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
        colorAcelerador = ObtenerValorIni(lines, "ColoresTelemetria", "ColorAcelerador", "~g~");
        colorFreno = ObtenerValorIni(lines, "ColoresTelemetria", "ColorFreno", "~r~");
        colorRPM = ObtenerValorIni(lines, "ColoresTelemetria", "ColorRPM", "~c~");
        colorMarcha = ObtenerValorIni(lines, "ColoresTelemetria", "ColorMarcha", "~s~");
        colorVelocidad = ObtenerValorIni(lines, "ColoresTelemetria", "ColorVelocidad", "~y~");
        colorTiempoTranscurrido = ObtenerValorIni(lines, "ColoresTelemetria", "ColorTiempoTranscurrido", "~s~");

        // Leer guardado de telemetría
        guardarTelemetria = ObtenerValorIni(lines, "Ajustes", "GuardarTelemetria", "true").ToLower() == "true";

        // Leer circuito seleccionado
        circuitoSeleccionado = ObtenerValorIni(lines, "Ajustes", "CircuitoSeleccionado", "Nurburgring Nordschleife");
        ultimoCircuito = circuitoSeleccionado; // Almacenar el último circuito seleccionado

        // Leer los puntos del circuito seleccionado
        if (circuitosCargados.ContainsKey(circuitoSeleccionado))
        {
            puntosDeControl = new List<Vector3>(circuitosCargados[circuitoSeleccionado]);
            Notification.PostTicker("Circuito seleccionado: " + circuitoSeleccionado, true, true);
        }
        else
        {
            Notification.PostTicker("Circuito " + circuitoSeleccionado + " no encontrado", true, true);
            // Seleccionar el primer circuito disponible si el configurado no existe
            if (circuitosCargados.Count > 0)
            {
                circuitoSeleccionado = circuitosCargados.Keys.First();
                puntosDeControl = new List<Vector3>(circuitosCargados[circuitoSeleccionado]);
                Notification.PostTicker("Usando circuito: " + circuitoSeleccionado, true, true);
            }
        }

        // Leer la tolerancia desde el archivo .ini
        string toleranciaStr = ObtenerValorIni(lines, "Ajustes", "Tolerancia");
        tolerancia = float.Parse(toleranciaStr.Replace('.', ','));

        // Eliminar la última línea de los archivos si es un registro de inicio
        BorrarUltimaLinea();

        // Inicializar la sesión de vueltas
        using (StreamWriter sw = new StreamWriter(rutaArchivo, true))
        {
            sw.WriteLine("\n=== Registro de vueltas iniciado " + DateTime.Now.ToString("dd/MM/yyyy HH:mm:ss.fff") + " " + circuitoSeleccionado + " ===");
        }

        if (guardarTelemetria)
        {
            // Inicializar la sesión de telemetría
            using (StreamWriter sw = new StreamWriter(rutaArchivoTelemetria, true))
            {
                sw.WriteLine("\n=== Telemetría iniciada " + DateTime.Now.ToString("dd/MM/yyyy HH:mm:ss.fff") + " " + circuitoSeleccionado + " ===");
            }
        }
    }

    // Función auxiliar para obtener valores del archivo .ini
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

    // Función que se ejecuta en cada fotograma del juego
    private void OnTick(object sender, EventArgs e)
    {
        // Deshabilitar controles del juego si estamos en modo búsqueda
        if (modoBusquedaCircuito)
        {
            Game.DisableAllControlsThisFrame();
            // Permitir solo controles de cámara si quieres
            Game.EnableControlThisFrame(GTA.Control.LookUpDown);
            Game.EnableControlThisFrame(GTA.Control.LookLeftRight);
        }

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
                    mensajeDeltaSector = "~g~¡Mejor tiempo en este sector! Has mejorado: " + FormatearTiempo(-deltaSector) + "~s~";
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
                        mensajeDeltaVuelta = "~g~¡Nuevo récord! Has mejorado: " + FormatearTiempo(-deltaVuelta) + "~s~";
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

                    // Guardar telemetría en archivo si está habilitado
                    if (guardarTelemetria && telemetriaAcumulada.Count > 0)
                    {
                        try
                        {
                            using (StreamWriter sw = new StreamWriter(rutaArchivoTelemetria, true))
                            {
                                foreach (string linea in telemetriaAcumulada)
                                {
                                    sw.WriteLine(linea);
                                }
                            }
                            telemetriaAcumulada.Clear();
                        }
                        catch (Exception ex)
                        {
                            Notification.PostTicker("Error al guardar la telemetría: " + ex.Message, true, true);
                        }
                    }
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
                string barraAcelerador = CrearBarra(acelerador, 30);
                string barraFreno = CrearBarra(freno, 30);
                string barraRPM = CrearBarra(rpm, 50);

                // Construir el mensaje de telemetría
                mensaje += string.Format(
                    "{8} {9} {10:F0} RPM{11}\n" +
                    "{4}Acel: {5} {6:F0}%{7}\n" +
                    "{0}Freno: {1} {2:F0}%{3}\n" +
                    "{16}{13}    {14} {12:F0} {15}",
                    colorFreno, barraFreno, freno * 100, "~s~",
                    colorAcelerador, barraAcelerador, acelerador * 100, "~s~",
                    colorRPM, barraRPM, rpm * 10000, "~s~",
                    velocidad, marcha,
                    colorVelocidad, unidadVelocidad == "mph" ? "mph" : "km/h", colorMarcha
                );
            }

            // Añadir tiempo transcurrido si está habilitado
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
                AcumularTelemetria();
            }
        }
    }

    // Función para obtener el mejor tiempo de un sector para un vehículo
    private TimeSpan ObtenerMejorTiempoSector(string vehiculo, int indiceSector)
    {
        if (mejoresTiemposPorSectorPorVehiculo.ContainsKey(vehiculo) && mejoresTiemposPorSectorPorVehiculo[vehiculo].Count > indiceSector)
        {
            return mejoresTiemposPorSectorPorVehiculo[vehiculo][indiceSector];
        }
        return TimeSpan.Zero;
    }

    // Función para actualizar el mejor tiempo de un sector para un vehículo
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

    // Función para controlar inputs del teclado
    private void OnKeyDown(object sender, KeyEventArgs e)
    {
        // Cancelar vuelta con la tecla N
        if (e.KeyCode == Keys.N && cronometroActivo)
        {
            cronometro.Stop();
            cronometroActivo = false;
            tiemposDeSectores.Clear();
            tiempoUltimoPunto = TimeSpan.Zero;
            indicePuntoActual = 0;
            telemetriaAcumulada.Clear();
            Notification.PostTicker("¡Vuelta cancelada!", true, true);
        }

        // Iniciar O SALIR de búsqueda de circuito con Ctrl + B
        if (e.KeyCode == Keys.B && e.Control)
        {
            if (modoBusquedaCircuito)
            {
                // Si ya está en modo búsqueda, salir
                modoBusquedaCircuito = false;
                Screen.ShowSubtitle("");
                Notification.PostTicker("Modo búsqueda desactivado", true, true);
            }
            else
            {
                // Si no está en modo búsqueda, entrar
                IniciarBusquedaCircuito();
            }
            e.Handled = true; // Evitar que la 'B' se procese después
            return; // Salir de la función para que no procese la 'B' como entrada
        }

        // Controlar entrada durante la búsqueda
        if (modoBusquedaCircuito)
        {
            ControlarBusquedaCircuito(e);
        }
    }

    // Función para iniciar el modo de búsqueda de circuito
    private void IniciarBusquedaCircuito()
    {
        modoBusquedaCircuito = true;
        busquedaActual = "";
        circuitosFiltrados = new List<string>(circuitosCargados.Keys);
        indiceSeleccion = 0;

        ActualizarDisplayBusqueda();

        Notification.PostTicker("Modo búsqueda activado. Usa Ctrl+B para salir", true, true);
    }

    // Función para controlar  la entrada durante la búsqueda de circuito
    private void ControlarBusquedaCircuito(KeyEventArgs e)
    {
        // IGNORAR teclas de control (Ctrl, Alt, Shift solos)
        if (e.KeyCode == Keys.ControlKey || e.KeyCode == Keys.Menu || e.KeyCode == Keys.ShiftKey ||
            e.KeyCode == Keys.LControlKey || e.KeyCode == Keys.RControlKey ||
            e.KeyCode == Keys.LMenu || e.KeyCode == Keys.RMenu ||
            e.KeyCode == Keys.LShiftKey || e.KeyCode == Keys.RShiftKey)
        {
            return; // No hacer nada con teclas de control solas
        }

        // Marcar la tecla como manejada para evitar que GTA la procese
        e.Handled = true;

        if (e.KeyCode == Keys.Back)
        {
            if (busquedaActual.Length > 0)
            {
                busquedaActual = busquedaActual.Substring(0, busquedaActual.Length - 1);
                ActualizarFiltroBusqueda();
            }
        }
        else if (e.KeyCode == Keys.Enter)
        {
            if (circuitosFiltrados.Count > 0 && indiceSeleccion < circuitosFiltrados.Count)
            {
                CambiarCircuito(circuitosFiltrados[indiceSeleccion]);
            }
            modoBusquedaCircuito = false;
            Screen.ShowSubtitle("");
        }
        else if (e.KeyCode == Keys.NumPad8 || e.KeyCode == Keys.Up)
        {
            indiceSeleccion = Math.Max(0, indiceSeleccion - 1);
            ActualizarDisplayBusqueda();
        }
        else if (e.KeyCode == Keys.NumPad2 || e.KeyCode == Keys.Down)
        {
            indiceSeleccion = Math.Min(circuitosFiltrados.Count - 1, indiceSeleccion + 1);
            ActualizarDisplayBusqueda();
        }
        else if (e.KeyCode >= Keys.A && e.KeyCode <= Keys.Z && !e.Shift)
        {
            // Letras minúsculas
            busquedaActual += (char)('a' + (e.KeyCode - Keys.A));
            ActualizarFiltroBusqueda();
        }
        else if (e.KeyCode >= Keys.A && e.KeyCode <= Keys.Z && e.Shift)
        {
            // Letras mayúsculas
            busquedaActual += (char)('A' + (e.KeyCode - Keys.A));
            ActualizarFiltroBusqueda();
        }
        else if (e.KeyCode == Keys.Space)
        {
            busquedaActual += " ";
            ActualizarFiltroBusqueda();
        }
        else if (e.KeyCode == Keys.OemMinus || e.KeyCode == Keys.Subtract)
        {
            busquedaActual += "-";
            ActualizarFiltroBusqueda();
        }
        else if (e.KeyCode == Keys.OemQuestion && e.Shift)
        {
            busquedaActual += "?";
            ActualizarFiltroBusqueda();
        }
        else if (e.KeyCode == Keys.OemPeriod || e.KeyCode == Keys.Decimal)
        {
            busquedaActual += ".";
            ActualizarFiltroBusqueda();
        }
        else if (e.KeyCode == Keys.Oemcomma)
        {
            busquedaActual += ",";
            ActualizarFiltroBusqueda();
        }
        else if (e.KeyCode == Keys.D0 || e.KeyCode == Keys.NumPad0)
        {
            busquedaActual += "0";
            ActualizarFiltroBusqueda();
        }
        else if (e.KeyCode >= Keys.D1 && e.KeyCode <= Keys.D9)
        {
            busquedaActual += (char)('1' + (e.KeyCode - Keys.D1));
            ActualizarFiltroBusqueda();
        }
        // Añadir soporte para guión bajo (importante para nombres como "Fujimi_Kaido")
        else if (e.KeyCode == Keys.Oemtilde || e.KeyCode == Keys.Oem8)
        {
            busquedaActual += "_";
            ActualizarFiltroBusqueda();
        }
        else
        {
            // Si no es una tecla que manejamos, no la marcamos como manejada
            e.Handled = false;
        }
    }

    // Función para cambiar de circuito
    private void CambiarCircuito(string nombreCircuito)
    {
        if (circuitosCargados.ContainsKey(nombreCircuito))
        {
            // Si el cronómetro está activo, cancelar la vuelta actual
            if (cronometroActivo)
            {
                cronometro.Stop();
                cronometroActivo = false;
                Notification.PostTicker("¡Vuelta cancelada al cambiar de circuito!", true, true);
            }

            // Limpiar datos
            tiemposDeSectores.Clear();
            telemetriaAcumulada.Clear();
            mejoresTiemposPorSectorPorVehiculo.Clear();
            mejoresVueltasPorVehiculo.Clear();
            tiempoUltimoPunto = TimeSpan.Zero;
            indicePuntoActual = 0;

            // Cambiar los puntos de control
            puntosDeControl = new List<Vector3>(circuitosCargados[nombreCircuito]);

            // Solo escribir líneas de inicio si el circuito ha cambiado
            if (circuitoSeleccionado != nombreCircuito)
            {
                // Guardar telemetría pendiente del circuito anterior
                if (guardarTelemetria && telemetriaAcumulada.Count > 0)
                {
                    try
                    {
                        using (StreamWriter sw = new StreamWriter(rutaArchivoTelemetria, true))
                        {
                            foreach (string linea in telemetriaAcumulada)
                            {
                                sw.WriteLine(linea);
                            }
                        }
                        telemetriaAcumulada.Clear();
                    }
                    catch (Exception ex)
                    {
                        Notification.PostTicker("Error al guardar telemetría: " + ex.Message, true, true);
                    }
                }

                // Eliminar la última línea de los archivos si es un registro de inicio
                BorrarUltimaLinea();

                if (guardarTelemetria)
                {
                    // Escribir nueva sesión en archivo de telemetría
                    using (StreamWriter sw = new StreamWriter(rutaArchivoTelemetria, true))
                    {
                        sw.WriteLine("\n=== Telemetría iniciada " + DateTime.Now.ToString("dd/MM/yyyy HH:mm:ss.fff") + " " + nombreCircuito + " ===");
                    }
                }

                // Escribir nueva sesión en archivo de vueltas
                using (StreamWriter sw = new StreamWriter(rutaArchivo, true))
                {
                    sw.WriteLine("\n=== Registro de vueltas iniciado " + DateTime.Now.ToString("dd/MM/yyyy HH:mm:ss.fff") + " " + nombreCircuito + " ===");
                }
            }

            circuitoSeleccionado = nombreCircuito;

            // Reiniciar el contador de vueltas
            numeroVuelta = 0;

            Notification.PostTicker("Circuito cambiado a: " + nombreCircuito, true, true);
            Notification.PostTicker("Puntos de control: " + puntosDeControl.Count, true, true);
        }
        else
        {
            Notification.PostTicker("Circuito '" + nombreCircuito + "' no encontrado", true, true);
            Notification.PostTicker("Circuitos disponibles:", true, true);

            // Mostrar algunos circuitos disponibles
            int count = 0;
            foreach (string circuito in circuitosCargados.Keys)
            {
                if (count < 5) // Mostrar solo los primeros 5 para no saturar
                {
                    Notification.PostTicker("  " + circuito, true, true);
                    count++;
                }
            }
            if (circuitosCargados.Count > 5)
            {
                Notification.PostTicker("  ... y " + (circuitosCargados.Count - 5) + " más", true, true);
            }
        }
    }

    // Función para borrar la última línea de los archivos si es un registro de inicio
    private void BorrarUltimaLinea()
    {
        // Si la última línea del archivo de vueltas es un registro de vuelta, borrarla
        if (File.Exists(rutaArchivo) && new FileInfo(rutaArchivo).Length > 0)
        {
            // Leer las líneas del archivo de vueltas
            var lineas = File.ReadAllLines(rutaArchivo).ToList();
            if (lineas.Count > 0 && lineas[lineas.Count - 1].StartsWith("=== Registro de vueltas iniciado"))
            {
                // Eliminar la última línea
                lineas.RemoveAt(lineas.Count - 1);

                // Si la nueva última línea está en blanco, también eliminarla
                if (lineas.Count > 0 && string.IsNullOrWhiteSpace(lineas[lineas.Count - 1]))
                {
                    lineas.RemoveAt(lineas.Count - 1);
                }

                // Escribir las líneas restantes de nuevo en el archivo
                File.WriteAllLines(rutaArchivo, lineas);
            }
        }

        // Si la última línea del archivo de telemetría es un registro de telemetría, borrarla
        if (File.Exists(rutaArchivoTelemetria) && new FileInfo(rutaArchivoTelemetria).Length > 0)
        {
            // Leer las líneas del archivo de telemetría
            var lineas = File.ReadAllLines(rutaArchivoTelemetria).ToList();
            // Si la última línea es un registro de telemetría, eliminarla
            if (lineas.Count > 0 && lineas[lineas.Count - 1].StartsWith("=== Telemetría iniciada"))
            {
                // Eliminar la última línea
                lineas.RemoveAt(lineas.Count - 1);

                // Si la nueva última línea está en blanco, también eliminarla
                if (lineas.Count > 0 && string.IsNullOrWhiteSpace(lineas[lineas.Count - 1]))
                {
                    lineas.RemoveAt(lineas.Count - 1);
                }

                // Escribir las líneas restantes de nuevo en el archivo
                File.WriteAllLines(rutaArchivoTelemetria, lineas);
            }
        }
    }

    // Función para actualizar el filtro de búsqueda basado en la entrada del usuario
    private void ActualizarFiltroBusqueda()
    {
        if (string.IsNullOrEmpty(busquedaActual))
        {
            circuitosFiltrados = new List<string>(circuitosCargados.Keys);
        }
        else
        {
            circuitosFiltrados = circuitosCargados.Keys
                .Where(c => c.ToLower().Contains(busquedaActual.ToLower()))
                .ToList();
        }
        indiceSeleccion = circuitosFiltrados.Count > 0 ? 0 : -1;
        ActualizarDisplayBusqueda();
    }

    // Función para actualizar el display de búsqueda en pantalla
    private void ActualizarDisplayBusqueda()
    {
        string display = "~b~BUSCAR CIRCUITO:~s~" + busquedaActual + "_\n\n";

        if (circuitosFiltrados.Count == 0)
        {
            display += "~r~No se encontraron circuitos~s~\n";
        }
        else
        {
            int inicio = Math.Max(0, indiceSeleccion - 2);
            int fin = Math.Min(circuitosFiltrados.Count, inicio + 5);

            for (int i = inicio; i < fin; i++)
            {
                string prefijo = (i == indiceSeleccion) ? "» " : "  ";
                string nombre = circuitosFiltrados[i];
                display += prefijo + nombre + "\n";
            }

            if (circuitosFiltrados.Count > 5)
            {
                display += "\n~y~Mostrando " + (inicio + 1) + "-" + fin + " de " + circuitosFiltrados.Count + "~s~";
            }
        }

        display += "\n\n~g~↑↓: Navegar | Enter: Seleccionar | Ctrl+B: Cancelar~s~";

        Screen.ShowSubtitle(display, 100000);
    }

    // Función para guardar los tiempos en un archivo de texto
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
                sw.WriteLine("Vuelta " + numeroVuelta + " - Fecha: " + DateTime.Now.ToString("dd/MM/yyyy HH:mm:ss.fff"));
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

    // Función para acumular la telemetría en una lista
    private void AcumularTelemetria()
    {
        try
        {
            telemetriaAcumulada.Add(string.Format("Telemetría | Fecha: {0} | Circuito: {1} | Vuelta: {2}", DateTime.Now.ToString("dd/MM/yyyy HH:mm:ss.fff"), circuitoSeleccionado, numeroVuelta));
            telemetriaAcumulada.Add(string.Format("  Hora del juego: {0:D2}:{1:D2}:{2:D2}.{3:D3}", horaJuego, minutoJuego, segundoJuego, milisegundoJuego));
            telemetriaAcumulada.Add(string.Format("  Clima: {0}", clima));
            telemetriaAcumulada.Add(string.Format("  Velocidad: {0:F1} {1}", velocidad, unidadVelocidad == "mph" ? "mph" : "km/h"));
            telemetriaAcumulada.Add(string.Format("  Velocidad de las ruedas: {0:F1} {1}", velocidadRuedas, unidadVelocidad == "mph" ? "mph" : "km/h"));
            telemetriaAcumulada.Add(string.Format("  Velocidad vectores: X={0:F1} Y={1:F1} Z={2:F1} m/s", velocidad2.X, velocidad2.Y, velocidad2.Z));
            telemetriaAcumulada.Add(string.Format("  Pedal Acelerador: {0:F0}%", pedalAcelerador * 100));
            telemetriaAcumulada.Add(string.Format("  Acelerador: {0:F0}%", acelerador * 100));
            telemetriaAcumulada.Add(string.Format("  RPM: {0:F0}", rpm * 10000));
            telemetriaAcumulada.Add(string.Format("  Freno: {0:F0}%", freno * 100));
            telemetriaAcumulada.Add(string.Format("  Embrague: {0}", embrague)); // 1 es no pulsado y cuando más cerca del 0 es totalmente pulsado
            telemetriaAcumulada.Add(string.Format("  Marcha: {0}", marcha));
            telemetriaAcumulada.Add(string.Format("  Ángulo de giro: {0:F1}º", anguloGiro));
            telemetriaAcumulada.Add(string.Format("  Turbo: {0:F0}%", turbo * 100));
            telemetriaAcumulada.Add(string.Format("  Nivel de combustible: {0:F1}L", nivelCombustible));
            telemetriaAcumulada.Add(string.Format("  Nivel de aceite: {0:F1}L", nivelAceite));
            telemetriaAcumulada.Add(string.Format("  Temperatura del motor: {0:F1}ºC", temperaturaMotor));
            telemetriaAcumulada.Add(string.Format("  Posición: ({0:F2}, {1:F2}, {2:F2})", Game.Player.Character.Position.X, Game.Player.Character.Position.Y, Game.Player.Character.Position.Z));
            telemetriaAcumulada.Add(string.Format("  Dirección: ({0:F2}, {1:F2}, {2:F2})", forwardVector.X, forwardVector.Y, forwardVector.Z));
            telemetriaAcumulada.Add(string.Format("  4 ruedas en el suelo: {0}", todasRuedasTocandoSuelo));
            telemetriaAcumulada.Add(string.Format("  Nivel de suciedad: {0:F0}%", nivelSuciedad / 15 * 100));
            telemetriaAcumulada.Add(string.Format("  Luces: {0}", lucesEncendidas));
            telemetriaAcumulada.Add(string.Format("  Luces Largas: {0}", lucesLargasEncendidas));
        }
        catch (Exception ex)
        {
            Notification.PostTicker("Error al acumular la telemetría: " + ex.Message, true, true);
        }
    }

    // Función para obtener el nombre del vehículo actual
    private string ObtenerNombreVehiculo()
    {
        if (Game.Player.Character.IsInVehicle())
        {
            var vehiculo = Game.Player.Character.CurrentVehicle;
            return vehiculo.DisplayName + " (" + vehiculo.ClassType + ")";
        }
        return "A pie";
    }

    // Función para formatear un TimeSpan en un string legible
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

        // Añadir el signo negativo si es necesario
        if (esNegativo)
        {
            tiempoFormateado = "-" + tiempoFormateado;
        }

        return tiempoFormateado;
    }

    // Función para actualizar la telemetría del vehículo
    private void ActualizarTelemetria()
    {
        if (Game.Player.Character.IsInVehicle())
        {
            Vehicle vehiculo = Game.Player.Character.CurrentVehicle;

            horaJuego = GameClock.Hour;                                 // Hora del juego
            minutoJuego = GameClock.Minute;                             // Minuto del juego
            segundoJuego = GameClock.Second;                            // Segundo del juego
            milisegundoJuego = GameClock.MillisecondsPerGameMinute;     // Milisegundo del juego
            clima = World.Weather;                                      // Clima

            pedalAcelerador = vehiculo.Throttle;                        // Pedal de acelerador pisado float
            acelerador = vehiculo.ThrottlePower;                        // Porcentage de acelerador float
            freno = vehiculo.BrakePower;                                // Presión en el freno
            rpm = vehiculo.CurrentRPM;                                  // Convertir a RPM (ajustar según sea necesario)
            embrague = vehiculo.Clutch;                                 // Posicion del embrague float
            marcha = vehiculo.CurrentGear;                              // Marcha actual
            turbo = vehiculo.Turbo;                                     // Estado del turbo float
            //frenoMano = vehiculo.IsHandbrakeForcedOn;                 // Freno de mano activado bool  // No en uso
            forwardVector = vehiculo.ForwardVector;                     // Dirección del vehículo

            velocidad = vehiculo.Speed;                                 // Velocidad en m/s
            velocidad2 = vehiculo.Velocity;                             // Un Vector3 que representa la dirección y fuerza del movimiento.

            nivelCombustible = vehiculo.FuelLevel;                      // Combustible actual
            nivelAceite = vehiculo.OilLevel;                            // Nivel de aceite float
            temperaturaMotor = vehiculo.EngineTemperature;              // Temperatura del motor float 

            todasRuedasTocandoSuelo = vehiculo.IsOnAllWheels;           // Todas las ruedas en el suelo
            cocheDetenido = vehiculo.IsStopped;                         // Indica si el coche está completamente parado // No en uso
            nivelSuciedad = vehiculo.DirtLevel;                         // Nivel de suciedad del vehículo float de 0.0f a 15.0f
            coheteActivado = vehiculo.IsRocketBoostActive;              // Si el cohete está encendido bool             // No en uso

            saludMotor = vehiculo.EngineHealth;                         // Salud del motor float                    // No en uso
            saludChasis = vehiculo.BodyHealth;                          // Salud del chasis float                   // No en uso
            saludTanqueCombustible = vehiculo.PetrolTankHealth;         // Salud del tanque de combustible float    // No en uso

            motorArrancando = vehiculo.IsEngineRunning;                 // Si el motor está arrancando bool     // No en uso
            motorEncendido = vehiculo.IsEngineStarting;                 // Si el motor está encendido bool      // No en uso

            velocidadRuedas = vehiculo.WheelSpeed;                      // Velocidad de giro de las ruedas float
            anguloGiro = vehiculo.SteeringAngle;                        // Ángulo de giro de la dirección float

            lucesEncendidas = vehiculo.AreLightsOn;                     // Indica si las luces están encendidas bool
            lucesLargasEncendidas = vehiculo.AreHighBeamsOn;            // Indica si las luces largas están encendidas bool
            intermitenteIzquierdo = vehiculo.IsLeftIndicatorLightOn;    // Indica si el intermitente izquierdo está encendido bool
            intermitenteDerecho = vehiculo.IsRightIndicatorLightOn;     // Indica si el intermitente derecho está encendido bool
            //lucesFrenoEncendidas = vehiculo.AreBrakeLightsOn;         // Indica si las luces de freno están encendidas bool   // No en uso

            // Convertir la velocidad a la unidad seleccionada
            if (unidadVelocidad == "mph")
            {
                velocidad *= 2.23694f;          // Convertir de m/s a mph
                velocidadRuedas *= 2.23694f;    // Convertir de m/s a mph
            }
            else
            {
                velocidad *= 3.6f;          // Convertir de m/s a km/h
                velocidadRuedas *= 3.6f;    // Convertir de m/s a km/h
            }
        }
        else
        {
            // Resetear valores si el jugador no está en un vehículo
            pedalAcelerador = 0;
            acelerador = 0;
            freno = 0;
            rpm = 0;
            embrague = 0;
            marcha = 0;
            frenoMano = false;
            anguloGiro = 0;
            turbo = 0;
            velocidad = 0;
            velocidadRuedas = 0;
            velocidad2 = Vector3.Zero;
            forwardVector = Vector3.Zero;
            todasRuedasTocandoSuelo = false;
            nivelCombustible = 0;
            nivelAceite = 0;
            temperaturaMotor = 0;
            cocheDetenido = false;
            coheteActivado = false;
            motorArrancando = false;
            motorEncendido = false;
            lucesEncendidas = false;
            lucesLargasEncendidas = false;
            intermitenteIzquierdo = false;
            intermitenteDerecho = false;
            nivelSuciedad = 0;
            saludMotor = 0;
            saludChasis = 0;
            saludTanqueCombustible = 0;

            // Mantener hora y clima actuales incluso cuando no se está en vehículo
            horaJuego = GameClock.Hour;                                 // Hora del juego
            minutoJuego = GameClock.Minute;                             // Minuto del juego
            segundoJuego = GameClock.Second;                            // Segundo del juego
            milisegundoJuego = GameClock.MillisecondsPerGameMinute;     // Milisegundo del juego
            clima = World.Weather;
        }
    }

    // Función para crear una barra de progreso usando caracteres
    private string CrearBarra(float valor, int longitud)
    {
        // Asegurar que el valor esté entre 0 y 1
        valor = Math.Max(0, Math.Min(1, valor));

        int cantidad = (int)(valor * longitud);
        return new string('|', cantidad).PadRight(longitud, ' ');
    }
}