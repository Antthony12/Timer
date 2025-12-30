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

public class SectorTimer : Script
{
    // List of checkpoints that define the route
    private List<Vector3> checkpoints = new List<Vector3>();
    private string selectedTrack; // Track selected in the ini file

    // Tolerance to consider that the player has reached a checkpoint
    private float tolerance; // Tolerance in game units

    // Stopwatch to measure lap time
    private Stopwatch stopwatch;
    private bool stopwatchActive = false;                       // Indicates if the stopwatch is active
    private int currentCheckpointIndex = 0;                     // Index of the current checkpoint
    private List<TimeSpan> sectorTimes = new List<TimeSpan>(); // List of times per sector

    // File paths (will be loaded from the .ini file)
    private string lapsFilePath;          // Path of the laps file
    private string telemetryFilePath;     // Path of the telemetry file

    // Lap properties
    private int lapNumber = 0;                        // Current lap number
    private TimeSpan lastCheckpointTime = TimeSpan.Zero; // Time of the last reached checkpoint
    private string vehicleUsed = "On foot";           // Name of the vehicle used

    // Telemetry
    private float brake;            // Brake pressure percentage (0.0 to 1.0)
    private float rpm;              // Engine revolutions per minute
    private int gear;               // Current vehicle gear
    private float speed;            // Speed
    private string speedUnit;       // Speed unit
    private Vector3 forwardVector;  // Vehicle direction
    private bool isOnAllWheels;     // 4 wheels on the ground
    private float fuelLevel;        // Fuel level
    private bool saveTelemetry;     // Save telemetry to file
    private string brakeColor;      // Color for the brake bar
    private string rpmColor;        // Color for the RPM bar
    private string gearColor;       // Color for the gears
    private string speedColor;      // Color for the speed
    private string elapsedTimeColor; // Color for the elapsed time

    // Dictionaries to store best laps and best sector times per vehicle
    private Dictionary<string, TimeSpan> bestLapsPerVehicle = new Dictionary<string, TimeSpan>();
    private Dictionary<string, List<TimeSpan>> bestSectorTimesPerVehicle = new Dictionary<string, List<TimeSpan>>();

    // HUD
    private bool showTelemetry;         // Show telemetry on screen
    private bool showElapsedTime;       // Show elapsed time on screen

    // Dictionary to store all loaded tracks
    private Dictionary<string, List<Vector3>> loadedTracks = new Dictionary<string, List<Vector3>>();
    private bool loadAllTracks = true; // Flag to control track loading

    // Variables for track search mode
    private bool trackSearchMode = false;
    private string currentSearch = "";
    private List<string> filteredTracks = new List<string>();
    private int selectionIndex = 0;
    private string lastTrack = "";

    // Starting accumulated telemetry list
    private List<string> accumulatedTelemetry = new List<string>();

    // Class constructor
    public SectorTimer()
    {
        // Load all available tracks
        LoadAllTracks();
        
        // Load configuration
        LoadConfiguration();
        
        // Subscribe to Tick and KeyDown events
        Tick += OnTick;
        KeyDown += OnKeyDown;
    }

    // Method to load all tracks from the timer.ini file
    private void LoadAllTracks()
    {
        if (!loadAllTracks) return;
        
        string configPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "timer.ini");
        if (!File.Exists(configPath))
        {
            Notification.PostTicker("timer.ini file not found.", true, true);
            return;
        }
        
        string[] lines = File.ReadAllLines(configPath);
        loadedTracks.Clear();
        
        bool inTracksSection = false;
        string currentTrackName = "";
        
        foreach (string line in lines)
        {
            string trimmedLine = line.Trim();
            
            // Detect tracks section
            if (trimmedLine.StartsWith("[Tracks]"))
            {
                inTracksSection = true;
                continue;
            }
            else if (trimmedLine.StartsWith("[") && inTracksSection)
            {
                // Exit the section if we find another section
                inTracksSection = false;
            }
            
            if (inTracksSection && trimmedLine.Contains("="))
            {
                // Process track line
                var parts = trimmedLine.Split('=');
                if (parts.Length == 2)
                {
                    currentTrackName = parts[0].Trim();
                    string trackData = parts[1].Trim();
                    
                    if (!string.IsNullOrEmpty(currentTrackName) && !currentTrackName.StartsWith(";"))
                    {
                        // Parse track coordinates
                        List<Vector3> trackPoints = ParseTrackCoordinates(trackData, currentTrackName);
                        if (trackPoints.Count > 0)
                        {
                            loadedTracks[currentTrackName] = trackPoints;
                        }
                    }
                }
            }
        }

        Notification.PostTicker("Loaded " + loadedTracks.Count + " tracks", true, true);
    }

    // Method to parse track coordinates from a string
    private List<Vector3> ParseTrackCoordinates(string trackData, string trackName)
    {
        List<Vector3> points = new List<Vector3>();
        string[] pointsStr = trackData.Split('/');
        
        foreach (string point in pointsStr)
        {
            string[] coords = point.Split(',');
            if (coords.Length == 3)
            {
                try
                {
                    float x = float.Parse(coords[0].Replace('.', ','));
                    float y = float.Parse(coords[1].Replace('.', ','));
                    float z = float.Parse(coords[2].Replace('.', ','));
                    points.Add(new Vector3(x, y, z));
                }
                catch (Exception ex)
                {
                    Notification.PostTicker("Error parsing coordinates for track " + trackName + ": " + ex.Message, true, true);
                }
            }
        }
        
        return points;
    }

    // Method to load configuration from the .ini file
    private void LoadConfiguration()
    {
        // Path of the .ini file
        string configPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "timer.ini");

        // Read all content of the .ini file
        string[] lines = File.ReadAllLines(configPath);

        // Read paths from the .ini file
        lapsFilePath = GetIniValue(lines, "Paths", "LogFile");
        telemetryFilePath = GetIniValue(lines, "Paths", "TelemetryFile");

        // Verify if paths are valid
        if (string.IsNullOrEmpty(lapsFilePath) || string.IsNullOrEmpty(telemetryFilePath))
        {
            Notification.PostTicker("Error: File paths are not correctly configured in the .ini file.", true, true);
        }

        // Read display settings
        showTelemetry = GetIniValue(lines, "Settings", "ShowTelemetry", "true").ToLower() == "true";
        showElapsedTime = GetIniValue(lines, "Settings", "ShowElapsedTime", "true").ToLower() == "true";

        // Read speed unit
        speedUnit = GetIniValue(lines, "Settings", "SpeedUnit", "kmh").ToLower();

        // Read telemetry colors
        brakeColor = GetIniValue(lines, "TelemetryColors", "BrakeColor", "~b~");
        rpmColor = GetIniValue(lines, "TelemetryColors", "RPMColor", "~r~");
        gearColor = GetIniValue(lines, "TelemetryColors", "GearColor", "~s~");
        speedColor = GetIniValue(lines, "TelemetryColors", "SpeedColor", "~y~");
        elapsedTimeColor = GetIniValue(lines, "TelemetryColors", "ElapsedTimeColor", "~s~");

        // Read telemetry saving
        saveTelemetry = GetIniValue(lines, "Settings", "SaveTelemetry", "true").ToLower() == "true";

        // Read selected track
        selectedTrack = GetIniValue(lines, "Settings", "SelectedTrack", "Nurburgring Nordschleife");
        lastTrack = selectedTrack; // Store last track for search mode

        // Read points of the selected track
        if (loadedTracks.ContainsKey(selectedTrack))
        {
            checkpoints = new List<Vector3>(loadedTracks[selectedTrack]);
            Notification.PostTicker("Selected track: " + selectedTrack, true, true);
        }
        else
        {
            Notification.PostTicker("Track " + selectedTrack + " not found", true, true);
            // Select the first available track if the configured one doesn't exist
            if (loadedTracks.Count > 0)
            {
                selectedTrack = loadedTracks.Keys.First();
                checkpoints = new List<Vector3>(loadedTracks[selectedTrack]);
                Notification.PostTicker("Using track: " + selectedTrack, true, true);
            }
        }

        // Read tolerance from the .ini file
        string toleranceStr = GetIniValue(lines, "Settings", "Tolerance");
        tolerance = float.Parse(toleranceStr.Replace('.', ','));

        // Remove last session lines from files
        DeleteLastLine();

        // Initialize lap recording session
        using (StreamWriter sw = new StreamWriter(lapsFilePath, true))
        {
            sw.WriteLine("\n=== Lap recording started " + DateTime.Now.ToString("dd/MM/yyyy HH:mm:ss.fff") + " " + selectedTrack + " ===");
        }

        if (saveTelemetry)
        {
            // Initialize telemetry recording session
            using (StreamWriter sw = new StreamWriter(telemetryFilePath, true))
            {
                sw.WriteLine("\n=== Telemetry started " + DateTime.Now.ToString("dd/MM/yyyy HH:mm:ss.fff") + " " + selectedTrack + " ===");
            }
        }
    }

    // Helper method to get values from the .ini file
    private string GetIniValue(string[] lines, string section, string key, string defaultValue = "")
    {
        bool insideSection = false;
        foreach (string line in lines)
        {
            // Detect sections
            if (line.StartsWith("[" + section + "]"))
            {
                insideSection = true;
            }
            else if (line.StartsWith("[") && insideSection)
            {
                // Exit the section when finding a new section
                break;
            }
            else if (insideSection && line.Contains("="))
            {
                // Look for the key in the section
                var parts = line.Split('=');
                if (parts[0].Trim() == key)
                {
                    return parts.Length > 1 ? parts[1].Trim() : defaultValue;
                }
            }
        }
        return defaultValue;  // Return default value if not found
    }

    // Method that executes on each game frame
    private void OnTick(object sender, EventArgs e)
    {
        // Disable game controls if we are in search mode
        if (trackSearchMode)
        {
            Game.DisableAllControlsThisFrame();
            // Allow only camera controls if desired
            Game.EnableControlThisFrame(GTA.Control.LookUpDown);
            Game.EnableControlThisFrame(GTA.Control.LookLeftRight);
        }

        // Get the current player position
        Vector3 playerPosition = Game.Player.Character.Position;
        // Calculate distance to the current checkpoint
        float distance = Vector3.Distance(playerPosition, checkpoints[currentCheckpointIndex]);

        // If the player is within tolerance of the checkpoint
        if (distance <= tolerance)
        {
            if (!stopwatchActive)
            {
                // Get vehicle name if in one
                vehicleUsed = GetVehicleName();

                // Increment lap number
                lapNumber++;

                // Start stopwatch when passing the first checkpoint
                Notification.PostTicker("Lap " + lapNumber + " started!\n" + selectedTrack, true, true);
                stopwatch = Stopwatch.StartNew();
                stopwatchActive = true;
                lastCheckpointTime = TimeSpan.Zero;
                currentCheckpointIndex++;
            }
            else
            {
                // Record sector time when passing intermediate or final points
                TimeSpan currentTime = stopwatch.Elapsed;
                TimeSpan sectorTime = currentTime - lastCheckpointTime;
                sectorTimes.Add(sectorTime);
                lastCheckpointTime = currentTime;

                // Calculate delta for the current sector
                TimeSpan bestSectorTime = GetBestSectorTime(vehicleUsed, currentCheckpointIndex - 1);
                TimeSpan sectorDelta = sectorTime - bestSectorTime;

                // Show notification with sector time and delta
                string sectorDeltaMessage = "";
                if (bestSectorTime == TimeSpan.Zero)
                {
                }
                else if (sectorDelta < TimeSpan.Zero)
                {
                    sectorDeltaMessage = "~g~Best time in this sector! You improved: " + FormatTime(-sectorDelta) + "~s~";
                }
                else
                {
                    sectorDeltaMessage = "~r~Slower in this sector by: " + FormatTime(sectorDelta) + "~s~";
                }

                Notification.PostTicker("Checkpoint " + currentCheckpointIndex + " reached.\nSector time: " + FormatTime(sectorTime) + "\n" + sectorDeltaMessage, true, true);

                // Update best sector time if needed
                if (bestSectorTime == TimeSpan.Zero || sectorTime < bestSectorTime)
                {
                    UpdateBestSectorTime(vehicleUsed, currentCheckpointIndex - 1, sectorTime);
                }

                if (currentCheckpointIndex == checkpoints.Count - 1)
                {
                    // If it's the last checkpoint, finish lap
                    stopwatch.Stop();
                    stopwatchActive = false;
                    TimeSpan totalLapTime = stopwatch.Elapsed;

                    // Compare with best lap of the current vehicle
                    TimeSpan bestLap = TimeSpan.Zero;
                    if (bestLapsPerVehicle.ContainsKey(vehicleUsed))
                    {
                        bestLap = bestLapsPerVehicle[vehicleUsed];
                    }

                    // Calculate delta (difference) with the best lap
                    TimeSpan lapDelta = totalLapTime - bestLap;

                    // Show notification with total time and delta
                    string lapDeltaMessage = "";
                    if (bestLap == TimeSpan.Zero)
                    {
                    }
                    else if (lapDelta < TimeSpan.Zero)
                    {
                        lapDeltaMessage = "~g~New record! You improved: " + FormatTime(-lapDelta) + "~s~";
                    }
                    else
                    {
                        lapDeltaMessage = "~r~Slower than record by: " + FormatTime(lapDelta) + "~s~";
                    }

                    Notification.PostTicker("Lap " + lapNumber + " completed! Total time: " + FormatTime(totalLapTime) + "\n" + lapDeltaMessage, true, true);

                    // Update best lap if needed
                    if (bestLap == TimeSpan.Zero || totalLapTime < bestLap)
                    {
                        bestLapsPerVehicle[vehicleUsed] = totalLapTime;
                    }

                    // Save times to file
                    SaveTimesToFile(totalLapTime, lapDelta);

                    // Save telemetry to file if enabled
                    if (saveTelemetry && accumulatedTelemetry.Count > 0)
                    {
                        try
                        {
                            using (StreamWriter sw = new StreamWriter(telemetryFilePath, true))
                            {
                                foreach (string line in accumulatedTelemetry)
                                {
                                    sw.WriteLine(line);
                                }
                            }
                            accumulatedTelemetry.Clear();
                        }
                        catch (Exception ex)
                        {
                            Notification.PostTicker("Error saving telemetry: " + ex.Message, true, true);
                        }
                    }
                    sectorTimes.Clear();
                    currentCheckpointIndex = 0;
                }
                else
                {
                    // Move to next checkpoint
                    currentCheckpointIndex++;
                }
            }
        }

        // Show telemetry and elapsed time according to configuration
        if (stopwatchActive)
        {
            UpdateTelemetry();

            // Build message to show
            string message = "";

            if (showTelemetry)
            {
                // Create progress bars using characters
                string brakeBar = CreateBar(brake, 30);
                string rpmBar = CreateBar(rpm / 10000.0f, 50);

                // Build telemetry message
                message += string.Format(
                    "{4} {5} {6:F0} RPM{7}\n" +
                    "{0}Brake: {1} {2:F0}%{3}\n" +
                    "{12}{9}    {10} {8:F0} {11}",
                    brakeColor, brakeBar, brake * 100, "~s~",
                    rpmColor, rpmBar, rpm, "~s~",
                    speed, gear,
                    speedColor, speedUnit == "mph" ? "mph" : "km/h", gearColor
                );
            }

            // Add elapsed time if enabled
            if (showElapsedTime)
            {
                TimeSpan currentTime = stopwatch.Elapsed;
                message += elapsedTimeColor + "\nElapsed time: " + FormatTime(currentTime) + "~s~";
            }

            // Show message on screen if not empty
            if (!string.IsNullOrEmpty(message))
            {
                Screen.ShowSubtitle(message);
            }

            // Save telemetry to file if enabled
            if (saveTelemetry)
            {
                AccumulateTelemetry();
            }
        }
    }

    // Method to get best sector time for a vehicle
    private TimeSpan GetBestSectorTime(string vehicle, int sectorIndex)
    {
        if (bestSectorTimesPerVehicle.ContainsKey(vehicle) && bestSectorTimesPerVehicle[vehicle].Count > sectorIndex)
        {
            return bestSectorTimesPerVehicle[vehicle][sectorIndex];
        }
        return TimeSpan.Zero;
    }

    // Method to update best sector time for a vehicle
    private void UpdateBestSectorTime(string vehicle, int sectorIndex, TimeSpan time)
    {
        if (!bestSectorTimesPerVehicle.ContainsKey(vehicle))
        {
            bestSectorTimesPerVehicle[vehicle] = new List<TimeSpan>();
        }

        while (bestSectorTimesPerVehicle[vehicle].Count <= sectorIndex)
        {
            bestSectorTimesPerVehicle[vehicle].Add(TimeSpan.Zero);
        }

        bestSectorTimesPerVehicle[vehicle][sectorIndex] = time;
    }

    // Modify the OnKeyDown method to cancel lap
    private void OnKeyDown(object sender, KeyEventArgs e)
    {
        // Cancel lap with N key
        if (e.KeyCode == Keys.N && stopwatchActive)
        {
            stopwatch.Stop();
            stopwatchActive = false;
            sectorTimes.Clear();
            lastCheckpointTime = TimeSpan.Zero;
            currentCheckpointIndex = 0;
            accumulatedTelemetry.Clear();
            Notification.PostTicker("Lap cancelled!", true, true);
        }
        
        // Start or EXIT track search with Ctrl + B
        if (e.KeyCode == Keys.B && e.Control)
        {
            if (trackSearchMode)
            {
                // If already in search mode, exit
                trackSearchMode = false;
                Screen.ShowSubtitle("");
                Notification.PostTicker("Search mode deactivated", true, true);
            }
            else
            {
                // If not in search mode, enter
                StartTrackSearch();
            }
            e.Handled = true; // Prevent 'B' from being processed afterwards
            return; // Exit method so 'B' is not processed as input
        }
        
        // Handle input during search
        if (trackSearchMode)
        {
            HandleTrackSearch(e);
        }
    }

    // Method to start track search mode
    private void StartTrackSearch()
    {
        trackSearchMode = true;
        currentSearch = "";
        filteredTracks = new List<string>(loadedTracks.Keys);
        selectionIndex = 0;
        
        UpdateSearchDisplay();
        
        Notification.PostTicker("Search mode activated. Use Ctrl+B to exit", true, true);
    }
    
    // Method to handle key input during track search
    private void HandleTrackSearch(KeyEventArgs e)
    {
        // IGNORE control keys (Ctrl, Alt, Shift alone)
        if (e.KeyCode == Keys.ControlKey || e.KeyCode == Keys.Menu || e.KeyCode == Keys.ShiftKey || 
            e.KeyCode == Keys.LControlKey || e.KeyCode == Keys.RControlKey ||
            e.KeyCode == Keys.LMenu || e.KeyCode == Keys.RMenu ||
            e.KeyCode == Keys.LShiftKey || e.KeyCode == Keys.RShiftKey)
        {
            return; // Do nothing with control keys alone
        }
        
        // Mark the key as handled to prevent GTA from processing it
        e.Handled = true;

        if (e.KeyCode == Keys.Back)
        {
            if (currentSearch.Length > 0)
            {
                currentSearch = currentSearch.Substring(0, currentSearch.Length - 1);
                UpdateSearchFilter();
            }
        }
        else if (e.KeyCode == Keys.Enter)
        {
            if (filteredTracks.Count > 0 && selectionIndex < filteredTracks.Count)
            {
                ChangeTrack(filteredTracks[selectionIndex]);
            }
            trackSearchMode = false;
            Screen.ShowSubtitle("");
        }
        else if (e.KeyCode == Keys.NumPad8 || e.KeyCode == Keys.Up)
        {
            selectionIndex = Math.Max(0, selectionIndex - 1);
            UpdateSearchDisplay();
        }
        else if (e.KeyCode == Keys.NumPad2 || e.KeyCode == Keys.Down)
        {
            selectionIndex = Math.Min(filteredTracks.Count - 1, selectionIndex + 1);
            UpdateSearchDisplay();
        }
        else if (e.KeyCode >= Keys.A && e.KeyCode <= Keys.Z && !e.Shift)
        {
            // Lowercase letters
            currentSearch += (char)('a' + (e.KeyCode - Keys.A));
            UpdateSearchFilter();
        }
        else if (e.KeyCode >= Keys.A && e.KeyCode <= Keys.Z && e.Shift)
        {
            // Uppercase letters
            currentSearch += (char)('A' + (e.KeyCode - Keys.A));
            UpdateSearchFilter();
        }
        else if (e.KeyCode == Keys.Space)
        {
            currentSearch += " ";
            UpdateSearchFilter();
        }
        else if (e.KeyCode == Keys.OemMinus || e.KeyCode == Keys.Subtract)
        {
            currentSearch += "-";
            UpdateSearchFilter();
        }
        else if (e.KeyCode == Keys.OemQuestion && e.Shift)
        {
            currentSearch += "?";
            UpdateSearchFilter();
        }
        else if (e.KeyCode == Keys.OemPeriod || e.KeyCode == Keys.Decimal)
        {
            currentSearch += ".";
            UpdateSearchFilter();
        }
        else if (e.KeyCode == Keys.Oemcomma)
        {
            currentSearch += ",";
            UpdateSearchFilter();
        }
        else if (e.KeyCode == Keys.D0 || e.KeyCode == Keys.NumPad0)
        {
            currentSearch += "0";
            UpdateSearchFilter();
        }
        else if (e.KeyCode >= Keys.D1 && e.KeyCode <= Keys.D9)
        {
            currentSearch += (char)('1' + (e.KeyCode - Keys.D1));
            UpdateSearchFilter();
        }
        // Add support for underscore (important for names like "Fujimi_Kaido")
        else if (e.KeyCode == Keys.Oemtilde || e.KeyCode == Keys.Oem8)
        {
            currentSearch += "_";
            UpdateSearchFilter();
        }
        else
        {
            // If it's not a key we handle, don't mark it as handled
            e.Handled = false;
        }
    }

    // Method to change track
    private void ChangeTrack(string trackName)
    {
        if (loadedTracks.ContainsKey(trackName))
        {
            // If the stopwatch is active, cancel the current lap
            if (stopwatchActive)
            {
                stopwatch.Stop();
                stopwatchActive = false;
                Notification.PostTicker("Lap cancelled when changing track!", true, true);
            }

            // Clear data
            sectorTimes.Clear();
            accumulatedTelemetry.Clear();
            bestSectorTimesPerVehicle.Clear();
            bestLapsPerVehicle.Clear();
            lastCheckpointTime = TimeSpan.Zero;
            currentCheckpointIndex = 0;
            
            // Change checkpoints
            checkpoints = new List<Vector3>(loadedTracks[trackName]);
            
            // Only write start lines if the track changed
            if (selectedTrack != trackName)
            {
                // Save pending telemetry from the previous track
                if (saveTelemetry && accumulatedTelemetry.Count > 0)
                {
                    try
                    {
                        using (StreamWriter sw = new StreamWriter(telemetryFilePath, true))
                        {
                            foreach (string line in accumulatedTelemetry)
                            {
                                sw.WriteLine(line);
                            }
                        }
                        accumulatedTelemetry.Clear();
                    }
                    catch (Exception ex)
                    {
                        Notification.PostTicker("Error saving telemetry: " + ex.Message, true, true);
                    }
                }

                // Remove last session lines from files
                DeleteLastLine();
                
                if (saveTelemetry)
                {
                    // Write new session to telemetry file
                    using (StreamWriter sw = new StreamWriter(telemetryFilePath, true))
                    {
                        sw.WriteLine("\n=== Telemetry started " + DateTime.Now.ToString("dd/MM/yyyy HH:mm:ss.fff") + " " + trackName + " ===");
                    }
                }
                
                // Write new session to laps file
                using (StreamWriter sw = new StreamWriter(lapsFilePath, true))
                {
                    sw.WriteLine("\n=== Lap recording started " + DateTime.Now.ToString("dd/MM/yyyy HH:mm:ss.fff") + " " + trackName + " ===");
                }
            }
            
            selectedTrack = trackName;
            
            // Reset lap counter
            lapNumber = 0;
            
            Notification.PostTicker("Track changed to: " + trackName, true, true);
            Notification.PostTicker("Checkpoints: " + checkpoints.Count, true, true);
        }
        else
        {
            Notification.PostTicker("Track '" + trackName + "' not found", true, true);
            Notification.PostTicker("Available tracks:", true, true);
            
            // Show some available tracks
            int count = 0;
            foreach (string track in loadedTracks.Keys)
            {
                if (count < 5) // Show only the first 5 to avoid saturation
                {
                    Notification.PostTicker("  " + track, true, true);
                    count++;
                }
            }
            if (loadedTracks.Count > 5)
            {
                Notification.PostTicker("  ... and " + (loadedTracks.Count - 5) + " more", true, true);
            }
        }
    }

    // Method to delete last line if it isn't a lap or telemetry record
    private void DeleteLastLine()
    {
        // If the last line of the laps file is a lap record, delete it
        if (File.Exists(lapsFilePath) && new FileInfo(lapsFilePath).Length > 0)
        {
            // Read lines from the laps file
            var fileLines = File.ReadAllLines(lapsFilePath).ToList();
            if (fileLines.Count > 0 && fileLines[fileLines.Count - 1].StartsWith("=== Lap recording started"))
            {
                // Remove the last line
                fileLines.RemoveAt(fileLines.Count - 1);

                // If the new last line is blank, also remove it
                if (fileLines.Count > 0 && string.IsNullOrWhiteSpace(fileLines[fileLines.Count - 1]))
                {
                    fileLines.RemoveAt(fileLines.Count - 1);
                }

                // Write the remaining lines back to the file
                File.WriteAllLines(lapsFilePath, fileLines);
            }
        }

        // If the last line of the telemetry file is a telemetry record, delete it
        if (File.Exists(telemetryFilePath) && new FileInfo(telemetryFilePath).Length > 0)
        {
            // Read lines from the telemetry file
            var fileLines = File.ReadAllLines(telemetryFilePath).ToList();
            // If the last line is a telemetry record, remove it
            if (fileLines.Count > 0 && fileLines[fileLines.Count - 1].StartsWith("=== Telemetry started"))
            {
                // Remove the last line
                fileLines.RemoveAt(fileLines.Count - 1);

                // If the new last line is blank, also remove it
                if (fileLines.Count > 0 && string.IsNullOrWhiteSpace(fileLines[fileLines.Count - 1]))
                {
                    fileLines.RemoveAt(fileLines.Count - 1);
                }

                // Write the remaining lines back to the file
                File.WriteAllLines(telemetryFilePath, fileLines);
            }
        }
    }

    // Method to update the filtered track list based on the current search
    private void UpdateSearchFilter()
    {
        if (string.IsNullOrEmpty(currentSearch))
        {
            filteredTracks = new List<string>(loadedTracks.Keys);
        }
        else
        {
            filteredTracks = loadedTracks.Keys
                .Where(c => c.ToLower().Contains(currentSearch.ToLower()))
                .ToList();
        }
        selectionIndex = filteredTracks.Count > 0 ? 0 : -1;
        UpdateSearchDisplay();
    }

    // Method to update the search display on screen
    private void UpdateSearchDisplay()
    {
        string display = "~b~SEARCH TRACK:~s~" + currentSearch + "_\n\n";
        
        if (filteredTracks.Count == 0)
        {
            display += "~r~No tracks found~s~\n";
        }
        else
        {
            int start = Math.Max(0, selectionIndex - 2);
            int end = Math.Min(filteredTracks.Count, start + 5);
            
            for (int i = start; i < end; i++)
            {
                string prefix = (i == selectionIndex) ? "» " : "  ";
                string name = filteredTracks[i];
                display += prefix + name + "\n";
            }
            
            if (filteredTracks.Count > 5)
            {
                display += "\n~y~Showing " + (start + 1) + "-" + end + " of " + filteredTracks.Count + "~s~";
            }
        }
        
        display += "\n\n~g~↑↓: Navigate | Enter: Select | Ctrl+B: Cancel~s~";
        
        Screen.ShowSubtitle(display, 100000);
    }

    // Method to save times to a text file
    private void SaveTimesToFile(TimeSpan totalLapTime, TimeSpan lapDelta)
    {
        try
        {
            string directory = Path.GetDirectoryName(lapsFilePath);
            if (!Directory.Exists(directory))
            {
                Directory.CreateDirectory(directory);
            }

            using (StreamWriter sw = new StreamWriter(lapsFilePath, true))
            {
                sw.WriteLine("=======================");
                sw.WriteLine("Lap " + lapNumber + " - Date: " + DateTime.Now.ToString("dd/MM/yyyy HH:mm:ss.fff"));
                sw.WriteLine("=======================");
                sw.WriteLine("  Track: " + selectedTrack);
                sw.WriteLine("  Vehicle: " + vehicleUsed);
                for (int i = 0; i < sectorTimes.Count; i++)
                {
                    TimeSpan bestSectorTime = GetBestSectorTime(vehicleUsed, i);
                    TimeSpan sectorDelta = sectorTimes[i] - bestSectorTime;
                    sw.WriteLine("  Sector " + (i + 1) + ": " + FormatTime(sectorTimes[i]) + " (Delta: " + FormatTime(sectorDelta) + ")");
                }
                sw.WriteLine("  Total lap time: " + FormatTime(totalLapTime));
                sw.WriteLine("  Total delta: " + FormatTime(lapDelta) + "\n");
            }
        }
        catch (Exception e)
        {
            Notification.PostTicker("Error saving times: " + e.Message, true, true);
        }
    }

    // Method to accumulate telemetry in a list
    private void AccumulateTelemetry()
    {
        try
        {
            accumulatedTelemetry.Add(string.Format("Telemetry | Date: {0} | Track: {1} | Lap: {2}", DateTime.Now.ToString("dd/MM/yyyy HH:mm:ss.fff"), selectedTrack, lapNumber));
            accumulatedTelemetry.Add(string.Format("  Speed: {0:F1} {1}", speed, speedUnit == "mph" ? "mph" : "km/h"));
            accumulatedTelemetry.Add(string.Format("  RPM: {0:F0}", rpm));
            accumulatedTelemetry.Add(string.Format("  Gear: {0}", gear));
            accumulatedTelemetry.Add(string.Format("  Brake: {0:F0}%", brake * 100));
            accumulatedTelemetry.Add(string.Format("  Fuel level: {0:F1}%", fuelLevel));
            accumulatedTelemetry.Add(string.Format("  Position: ({0:F2}, {1:F2}, {2:F2})", Game.Player.Character.Position.X, Game.Player.Character.Position.Y, Game.Player.Character.Position.Z));
            accumulatedTelemetry.Add(string.Format("  Direction: ({0:F2}, {1:F2}, {2:F2})", forwardVector.X, forwardVector.Y, forwardVector.Z));
            accumulatedTelemetry.Add(string.Format("  4 wheels on ground: {0}", isOnAllWheels));
        }
        catch (Exception ex)
        {
            Notification.PostTicker("Error accumulating telemetry: " + ex.Message, true, true);
        }
    }

    // Method to get the name of the current vehicle
    private string GetVehicleName()
    {
        if (Game.Player.Character.IsInVehicle())
        {
            var vehicle = Game.Player.Character.CurrentVehicle;
            return vehicle.DisplayName + " (" + vehicle.ClassType + ")";
        }
        return "On foot";
    }

    // Method to format a TimeSpan into a readable string
    private string FormatTime(TimeSpan time)
    {
        // Check if time is negative
        bool isNegative = time < TimeSpan.Zero;
        if (isNegative)
        {
            time = time.Duration(); // Convert to absolute value
        }

        // Format the time
        string formattedTime = string.Format("{0:D2}:{1:D2}:{2:D2}.{3:D3}",
            time.Hours,
            time.Minutes,
            time.Seconds,
            time.Milliseconds);

        // Add negative sign if needed
        if (isNegative)
        {
            formattedTime = "-" + formattedTime;
        }

        return formattedTime;
    }

    // Method to update telemetry data
    private void UpdateTelemetry()
    {
        if (Game.Player.Character.IsInVehicle())
        {
            var vehicle = Game.Player.Character.CurrentVehicle;
            brake = vehicle.BrakePower;      // Brake pressure
            rpm = vehicle.CurrentRPM * 10000; // Convert to RPM (adjust as needed)
            gear = vehicle.CurrentGear;      // Current gear
            speed = vehicle.Speed;           // Speed in m/s

            // Convert speed to selected unit
            if (speedUnit == "mph")
            {
                speed *= 2.23694f; // Convert from m/s to mph
            }
            else
            {
                speed *= 3.6f; // Convert from m/s to km/h
            }

            forwardVector = vehicle.ForwardVector; // Vehicle direction
            isOnAllWheels = vehicle.IsOnAllWheels; // All wheels on ground
            fuelLevel = vehicle.FuelLevel;         // Current fuel
        }
        else
        {
            // Reset values if player is not in a vehicle
            brake = 0;
            rpm = 0;
            gear = 0;
            speed = 0;
            forwardVector = Vector3.Zero;
            isOnAllWheels = false;
            fuelLevel = 0;
        }
    }

    // Method to create a progress bar using characters
    private string CreateBar(float value, int length)
    {
        int amount = (int)(value * length);
        return new string('|', amount).PadRight(length, ' ');
    }
}