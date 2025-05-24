using System;
using System.Diagnostics;
using GTA;
using GTA.UI;
using Screen = GTA.UI.Screen;
using GTA.Math;
using System.Windows.Forms;
using System.IO;
using System.Collections.Generic;

public class SectorTimer : Script
{
    // List of checkpoints that define the route
    private List<Vector3> checkpoints = new List<Vector3>();
    private string selectedTrack; // Track selected in the ini file

    // Tolerance to consider that the player has reached a checkpoint
    private float tolerance; // Tolerance in game units

    // Stopwatch to measure lap time
    private Stopwatch stopwatch;
    private bool stopwatchActive = false;                              // Indicates if the stopwatch is active
    private int currentCheckpointIndex = 0;                            // Index of the current checkpoint
    private List<TimeSpan> sectorTimes = new List<TimeSpan>();         // List of sector times

    // File paths (loaded from the .ini file)
    private string lapFilePath;             // Path of the lap file
    private string telemetryFilePath;       // Path of the telemetry file

    // Lap properties
    private int lapNumber = 0;                       // Current lap number
    private TimeSpan lastCheckpointTime = TimeSpan.Zero; // Time of the last checkpoint reached
    private string vehicleUsed = "On foot";         // Name of the vehicle used

    // Telemetry
    private float brake;            // Brake pressure percentage (0.0 to 1.0)
    private float rpm;              // Engine revolutions per minute
    private int gear;               // Current gear of the vehicle
    private float speed;            // Speed
    private string speedUnit;       // Speed unit
    private Vector3 forwardVector;  // Vehicle direction
    private bool isOnAllWheels;     // All wheels on the ground
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

    // Class constructor
    public SectorTimer()
    {
        // Load paths from the .ini file
        LoadConfiguration();

        // Subscribe to Tick and KeyDown events
        Tick += OnTick;
        KeyDown += OnKeyDown;
    }

    private void LoadConfiguration()
    {
        // Path of the .ini file
        string configPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "timer.ini");

        // Read all lines from the .ini file
        string[] lines = File.ReadAllLines(configPath);

        // Read paths from the .ini file
        lapFilePath = GetIniValue(lines, "Paths", "LapFile");
        telemetryFilePath = GetIniValue(lines, "Paths", "TelemetryFile");

        // Verify if the paths are valid
        if (string.IsNullOrEmpty(lapFilePath) || string.IsNullOrEmpty(telemetryFilePath))
        {
            Notification.PostTicker("Error: File paths are not configured correctly in the .ini file.", true, true);
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

        // Read the points of the selected track
        string trackData = GetIniValue(lines, "Tracks", selectedTrack);

        if (!string.IsNullOrEmpty(trackData))
        {
            checkpoints.Clear();
            string[] points = trackData.Split('/');
            foreach (string point in points)
            {
                string[] coords = point.Split(',');
                if (coords.Length == 3)
                {
                    float x = float.Parse(coords[0].Replace('.', ','));
                    float y = float.Parse(coords[1].Replace('.', ','));
                    float z = float.Parse(coords[2].Replace('.', ','));
                    checkpoints.Add(new Vector3(x, y, z));
                }
                else
                {
                    Notification.PostTicker("Invalid coordinates: " + coords, true, true);
                }
            }

            Notification.PostTicker("Selected track: " + selectedTrack, true, true);
        }
        else
        {
            Notification.PostTicker("Track " + selectedTrack + " not found in timer.ini", true, true);
        }

        // Read the tolerance from the .ini file
        string toleranceStr = GetIniValue(lines, "Settings", "Tolerance");
        tolerance = float.Parse(toleranceStr.Replace('.', ','));
    }

    // Helper method to get values from the .ini file
    private string GetIniValue(string[] lines, string section, string key, string defaultValue = "")
    {
        bool inSection = false;
        foreach (string line in lines)
        {
            // Detect sections
            if (line.StartsWith("[" + section + "]"))
            {
                inSection = true;
            }
            else if (line.StartsWith("[") && inSection)
            {
                // Exit the section when a new section is found
                break;
            }
            else if (inSection && line.Contains("="))
            {
                // Search for the key in the section
                var parts = line.Split('=');
                if (parts[0].Trim() == key)
                {
                    return parts.Length > 1 ? parts[1].Trim() : defaultValue;
                }
            }
        }
        return defaultValue;  // Return the default value if not found
    }

    // Method executed on each game frame
    private void OnTick(object sender, EventArgs e)
    {
        // Get the player's current position
        Vector3 playerPosition = Game.Player.Character.Position;
        // Calculate the distance to the current checkpoint
        float distance = Vector3.Distance(playerPosition, checkpoints[currentCheckpointIndex]);

        // If the player is within the tolerance of the checkpoint
        if (distance <= tolerance)
        {
            if (!stopwatchActive)
            {
                // Get the name of the vehicle if the player is in one
                vehicleUsed = GetVehicleName();

                // Increment the lap number
                lapNumber++;

                // Start the stopwatch when passing the first checkpoint
                Notification.PostTicker("Lap " + lapNumber + " started!\n" + selectedTrack, true, true);
                stopwatch = Stopwatch.StartNew();
                stopwatchActive = true;
                lastCheckpointTime = TimeSpan.Zero;
                currentCheckpointIndex++;
            }
            else
            {
                // Record sector time when passing intermediate or final checkpoints
                TimeSpan currentTime = stopwatch.Elapsed;
                TimeSpan sectorTime = currentTime - lastCheckpointTime;
                sectorTimes.Add(sectorTime);
                lastCheckpointTime = currentTime;

                // Calculate delta for the current sector
                TimeSpan bestSectorTime = GetBestSectorTime(vehicleUsed, currentCheckpointIndex - 1);
                TimeSpan sectorDelta = sectorTime - bestSectorTime;

                // Show notification with the sector time and delta
                string sectorDeltaMessage = "";
                if (bestSectorTime == TimeSpan.Zero)
                {
                }
                else if (sectorDelta < TimeSpan.Zero)
                {
                    sectorDeltaMessage = "~g~Best time in this sector! You improved by: " + FormatTime(-sectorDelta) + "~s~";
                }
                else
                {
                    sectorDeltaMessage = "~r~Slower in this sector by: " + FormatTime(sectorDelta) + "~s~";
                }

                Notification.PostTicker("Checkpoint " + currentCheckpointIndex + " reached.\nSector time: " + FormatTime(sectorTime) + "\n" + sectorDeltaMessage, true, true);

                // Update the best sector time if necessary
                if (bestSectorTime == TimeSpan.Zero || sectorTime < bestSectorTime)
                {
                    UpdateBestSectorTime(vehicleUsed, currentCheckpointIndex - 1, sectorTime);
                }

                if (currentCheckpointIndex == checkpoints.Count - 1)
                {
                    // If it's the last checkpoint, finish the lap
                    stopwatch.Stop();
                    stopwatchActive = false;
                    TimeSpan totalLapTime = stopwatch.Elapsed;

                    // Compare with the best lap for the current vehicle
                    TimeSpan bestLap = TimeSpan.Zero;
                    if (bestLapsPerVehicle.ContainsKey(vehicleUsed))
                    {
                        bestLap = bestLapsPerVehicle[vehicleUsed];
                    }

                    // Calculate the delta (difference) with the best lap
                    TimeSpan lapDelta = totalLapTime - bestLap;

                    // Show notification with the total lap time and delta
                    string lapDeltaMessage = "";
                    if (bestLap == TimeSpan.Zero)
                    {
                    }
                    else if (lapDelta < TimeSpan.Zero)
                    {
                        lapDeltaMessage = "~g~New record! You improved by: " + FormatTime(-lapDelta) + "~s~";
                    }
                    else
                    {
                        lapDeltaMessage = "~r~Slower than the record by: " + FormatTime(lapDelta) + "~s~";
                    }

                    Notification.PostTicker("Lap " + lapNumber + " completed! Total time: " + FormatTime(totalLapTime) + "\n" + lapDeltaMessage, true, true);

                    // Update the best lap if necessary
                    if (bestLap == TimeSpan.Zero || totalLapTime < bestLap)
                    {
                        bestLapsPerVehicle[vehicleUsed] = totalLapTime;
                    }

                    // Save times to file
                    SaveTimesToFile(totalLapTime, lapDelta);
                    sectorTimes.Clear();
                    currentCheckpointIndex = 0;
                }
                else
                {
                    // Move to the next checkpoint
                    currentCheckpointIndex++;
                }
            }
        }

        // Show telemetry and elapsed time according to the configuration
        if (stopwatchActive)
        {
            UpdateTelemetry();

            // Build the message to display
            string message = "";

            if (showTelemetry)
            {
                // Create progress bars using characters
                string brakeBar = CreateBar(brake, 30);
                string rpmBar = CreateBar(rpm / 10000.0f, 50);

                // Build the telemetry message
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

            if (showElapsedTime)
            {
                TimeSpan currentTime = stopwatch.Elapsed;
                message += elapsedTimeColor + "\nElapsed time: " + FormatTime(currentTime) + "~s~";
            }

            // Show the message on screen if it's not empty
            if (!string.IsNullOrEmpty(message))
            {
                Screen.ShowSubtitle(message);
            }

            // Save telemetry to file if enabled
            if (saveTelemetry)
            {
                SaveTelemetryToFile();
            }
        }
    }

    // Method to get the best sector time for a vehicle
    private TimeSpan GetBestSectorTime(string vehicle, int sectorIndex)
    {
        if (bestSectorTimesPerVehicle.ContainsKey(vehicle) && bestSectorTimesPerVehicle[vehicle].Count > sectorIndex)
        {
            return bestSectorTimesPerVehicle[vehicle][sectorIndex];
        }
        return TimeSpan.Zero;
    }

    // Method to update the best sector time for a vehicle
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

    // Method executed when a key is pressed
    private void OnKeyDown(object sender, KeyEventArgs e)
    {
        if (e.KeyCode == Keys.N && stopwatchActive)
        {
            // Cancel the lap if the N key is pressed
            stopwatch.Stop();
            stopwatchActive = false;
            sectorTimes.Clear();
            currentCheckpointIndex = 0;
            Notification.PostTicker("Lap canceled!", true, true);
        }
    }

    // Method to save times to a text file
    private void SaveTimesToFile(TimeSpan totalLapTime, TimeSpan lapDelta)
    {
        try
        {
            string directory = Path.GetDirectoryName(lapFilePath);
            if (!Directory.Exists(directory))
            {
                Directory.CreateDirectory(directory);
            }

            using (StreamWriter sw = new StreamWriter(lapFilePath, true))
            {
                sw.WriteLine("=======================");
                sw.WriteLine("Lap " + lapNumber + " - Date: " + DateTime.Now);
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

    private void SaveTelemetryToFile()
    {
        try
        {
            using (StreamWriter sw = new StreamWriter(telemetryFilePath, true))
            {
                sw.WriteLine(string.Format("Telemetry | Date: {0} | Track: {1}", DateTime.Now, selectedTrack));
                sw.WriteLine(string.Format("  Speed: {0:F1} {1}", speed, speedUnit == "mph" ? "mph" : "km/h"));
                sw.WriteLine(string.Format("  RPM: {0:F0}", rpm));
                sw.WriteLine(string.Format("  Gear: {0}", gear));
                sw.WriteLine(string.Format("  Brake: {0:F0}%", brake * 100));
                sw.WriteLine(string.Format("  Fuel level: {0:F1}%", fuelLevel));
                sw.WriteLine(string.Format("  Direction: ({0:F2}, {1:F2}, {2:F2})", forwardVector.X, forwardVector.Y, forwardVector.Z));
                sw.WriteLine(string.Format("  All wheels on the ground: {0}", isOnAllWheels));
            }
        }
        catch (Exception ex)
        {
            Notification.PostTicker("Error saving telemetry: " + ex.Message, true, true);
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
        // Check if the time is negative
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

        // Add negative sign if necessary
        if (isNegative)
        {
            formattedTime = "-" + formattedTime;
        }

        return formattedTime;
    }

    private void UpdateTelemetry()
    {
        if (Game.Player.Character.IsInVehicle())
        {
            var vehicle = Game.Player.Character.CurrentVehicle;
            brake = vehicle.BrakePower;      // Brake pressure
            rpm = vehicle.CurrentRPM * 10000; // Convert to RPM (adjust as needed)
            gear = vehicle.CurrentGear;    // Current gear
            speed = vehicle.Speed; // Speed in m/s

            // Convert speed to the selected unit
            if (speedUnit == "mph")
            {
                speed *= 2.23694f; // Convert from m/s to mph
            }
            else
            {
                speed *= 3.6f; // Convert from m/s to km/h
            }

            forwardVector = vehicle.ForwardVector; // Vehicle direction
            isOnAllWheels = vehicle.IsOnAllWheels; // All wheels on the ground
            fuelLevel = vehicle.FuelLevel; // Current fuel level
        }
        else
        {
            // Reset values if the player is not in a vehicle
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