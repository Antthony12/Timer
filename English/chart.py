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

# File path
file_path = r"C:\Users\pato\Desktop\scripts\Logs\telemetrygta5.log"
export_path = r"C:\Users\pato\Desktop\scripts\Logs\Exports"

# Lists to store data
timestamps = []
speeds = []
brakes = []
rpms = []
gears = []
laps = []  # List of recorded laps
lap_data = {}  # Dictionary to store data per lap
track = "Unknown Track"  # Default value

# Dictionary to store sessions
sessions = {}
current_session = None
track_per_session = {}  # Store track per session

# Regular expressions to extract data
time_pattern = re.compile(r"Date: (\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}\.\d{3})")
speed_pattern = re.compile(r"Speed: ([\d,]+) km/h")
brake_pattern = re.compile(r"Brake: ([\d,]+)%")
rpm_pattern = re.compile(r"RPM: ([\d,]+)")
gear_pattern = re.compile(r"Gear: (\d+)")
lap_pattern = re.compile(r"Lap: (\d+)")
track_pattern = re.compile(r"Track: (.+?) \| Lap:")
position_pattern = re.compile(r"Position: \(([\d,-]+), ([\d,-]+), ([\d,-]+)\)")
session_start_pattern = re.compile(r"=== Telemetry started (.+?) (.+?) (.+?) ===")

# Function to clean the last line if it's a start record
def clean_last_line_if_record(file_path, start_record):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if lines and lines[-1].startswith(start_record):
            lines.pop()
            # If the new last line is blank, remove it too
            if lines and lines[-1].strip() == "":
                lines.pop()
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

# Clean files if necessary
clean_last_line_if_record(file_path, "=== Telemetry started")

# Read and process the file
with open(file_path, "r", encoding="utf-8") as file:
    for line in file:
        # Search for session start
        session_match = session_start_pattern.search(line)
        if session_match:
            session_date = session_match.group(1).strip()  # Date
            session_time = session_match.group(2).strip()  # Time
            track = session_match.group(3).strip()      # Track
            current_session = f"{session_date} {session_time}"  # Combine date and time
            if current_session not in sessions:
                sessions[current_session] = {}
                track_per_session[current_session] = track
            continue

        # If we're not in any session, skip
        if current_session is None:
            continue

        # Search for track name
        track_match = track_pattern.search(line)
        if track_match:
            track_per_session[current_session] = track_match.group(1).strip()

        time_match = time_pattern.search(line)
        speed_match = speed_pattern.search(line)
        brake_match = brake_pattern.search(line)
        rpm_match = rpm_pattern.search(line)
        gear_match = gear_pattern.search(line)
        lap_match = lap_pattern.search(line)
        position_match = position_pattern.search(line)

        if time_match:
            current_timestamp = time_match.group(1)

        if lap_match:
            lap_number = int(lap_match.group(1))
            if lap_number not in sessions[current_session]:
                sessions[current_session][lap_number] = {
                    "timestamps": [],
                    "speeds": [],
                    "brakes": [],
                    "rpms": [],
                    "gears": [],
                    "durations": [],
                    "positions": []
                }
            current_lap = lap_number

        if speed_match and current_timestamp:
            speed = float(speed_match.group(1).replace(",", "."))
            time_object = datetime.strptime(current_timestamp, "%d/%m/%Y %H:%M:%S.%f")
            sessions[current_session][current_lap]["timestamps"].append(time_object)
            sessions[current_session][current_lap]["speeds"].append(speed)

        if brake_match:
            brake = float(brake_match.group(1).replace(",", "."))
            sessions[current_session][current_lap]["brakes"].append(brake)

        if rpm_match:
            rpm = float(rpm_match.group(1).replace(",", "."))
            sessions[current_session][current_lap]["rpms"].append(rpm)

        if gear_match:
            gear = int(gear_match.group(1))
            sessions[current_session][current_lap]["gears"].append(gear)
        
        if position_match:
            x = float(position_match.group(1).replace(",", "."))
            y = float(position_match.group(2).replace(",", "."))
            z = float(position_match.group(3).replace(",", "."))
            
            if current_lap in sessions[current_session]:
                if "positions" not in sessions[current_session][current_lap]:
                    sessions[current_session][current_lap]["positions"] = []
                sessions[current_session][current_lap]["positions"].append((x, y, z))

# Function to format seconds to mm:ss
def seconds_to_minutes(seconds, pos):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

# Calculate the duration of each data point relative to the start of the lap
for session, lap_data in sessions.items():
    for lap_number, data in lap_data.items():
        if data["timestamps"]:
            t0 = data["timestamps"][0]
            data["durations"] = [(t - t0).total_seconds() for t in data["timestamps"]]

# Create the figure using GridSpec with 11 rows:
# Row 0: Lap times chart (line)
# Row 1: Blank space for times chart
# Row 2: Delta chart (bars, no title)
# Row 3: Average speed
# Row 4: Speed
# Row 5: Brake
# Row 6: RPM
# Row 7: Gear
# Row 8: G-Force (new)
# Row 9: 2D Map
# Row 10: (Final blank space, optional)
fig = plt.figure(figsize=(12, 32))
gs = gridspec.GridSpec(12, 1, height_ratios=[1, 0.2, 1, 1, 1, 1, 1, 1, 1, 0.4, 4, 1])
plt.subplots_adjust(left=0.07, right=0.98, top=0.97, bottom=0, hspace=0.02)

# Define each axis (we omit blank rows)
ax0 = fig.add_subplot(gs[0])  # Lap times (line)
ax1 = fig.add_subplot(gs[2])  # Delta (bars, no title)
ax8 = fig.add_subplot(gs[3])  # Average speed
ax2 = fig.add_subplot(gs[4])  # Speed
ax3 = fig.add_subplot(gs[5])  # Brake
ax4 = fig.add_subplot(gs[6])  # RPM
ax5 = fig.add_subplot(gs[7])  # Gear
ax7 = fig.add_subplot(gs[8])  # G-Force (new)
ax6 = fig.add_subplot(gs[10])  # 2D Map

def update_chart():
    global selected_session

    print("Updating chart...")
    selected_laps = listbox_laps.curselection()
    
    print(f"Selected session: {selected_session}")
    print(f"Selected laps: {selected_laps}")
    
    if not selected_session or not selected_laps:
        print("No session or laps selected.")
        return
    
    # Get current session and track (use selected_session)
    current_track = track_per_session.get(selected_session, "Unknown Track")
    lap_data_session = sessions[selected_session]

    print(f"Current session: {selected_session}")
    print(f"Current track: {current_track}")
    print(f"Session data: {lap_data_session.keys()}")
    
    # Clear ALL axes
    for ax in [ax0, ax1, ax2, ax3, ax4, ax5, ax7, ax6, ax8]:
        ax.cla()
    
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

    # Calculate common start and end for speed, brake, RPM and gear charts
    selected_laps_list = []
    for idx in selected_laps:
        lap_text = listbox_laps.get(idx)
        lap_number = int(lap_text.split()[1])
        selected_laps_list.append(lap_number)

    start = min([lap_data_session[lap_number]["durations"][0] for lap_number in selected_laps_list if lap_number in lap_data_session and lap_data_session[lap_number]["durations"]], default=0)
    end = max([lap_data_session[lap_number]["durations"][-1] for lap_number in selected_laps_list if lap_number in lap_data_session and lap_data_session[lap_number]["durations"]], default=1)
    
    print(f"Start: {start}, End: {end}")
    
    # Lists for lap times chart and delta chart
    lap_numbers_line = []
    total_times = []
    lap_numbers_delta = []
    lap_times = []
    lap_numbers_speed = []
    average_speeds = []

    for idx, lap_number in enumerate(selected_laps_list):
        if lap_number not in lap_data_session:
            print(f"Lap {lap_number} is not in session data.")
            continue
        color = colors[idx % len(colors)]
        
        # Plot on speed, brake, RPM and gear charts
        try:
            print(f"Duration length for lap {lap_number}: {len(lap_data_session[lap_number]['durations'])}")
            print(f"Speed length for lap {lap_number}: {len(lap_data_session[lap_number]['speeds'])}")
            ax2.plot(lap_data_session[lap_number]["durations"], lap_data_session[lap_number]["speeds"],
                     color=color, alpha=0.7, label=f"Lap {lap_number}")
            ax3.plot(lap_data_session[lap_number]["durations"], lap_data_session[lap_number]["brakes"],
                     color=color, alpha=0.7, label=f"Lap {lap_number}")
            ax4.plot(lap_data_session[lap_number]["durations"], lap_data_session[lap_number]["rpms"],
                     color=color, alpha=0.7, label=f"Lap {lap_number}")
            ax5.plot(lap_data_session[lap_number]["durations"], lap_data_session[lap_number]["gears"],
                     color=color, alpha=0.7, label=f"Lap {lap_number}")
        except Exception as e:
            print(f"Error plotting lap {lap_number}: {e}")
        
        if lap_data_session[lap_number]["gears"]:
            ax5.set_yticks(range(int(min(lap_data_session[lap_number]["gears"])),
                                 int(max(lap_data_session[lap_number]["gears"])) + 1))
        
        # Collect data for lap times chart and delta chart
        if lap_data_session[lap_number]["durations"]:
            total_time = lap_data_session[lap_number]["durations"][-1]
            lap_numbers_line.append(lap_number)
            total_times.append(total_time)
            lap_numbers_delta.append(lap_number)
            lap_times.append(total_time)

        # Calculate average speed for this lap
        if lap_number in lap_data_session and lap_data_session[lap_number]["speeds"]:
            average_speed = np.mean(lap_data_session[lap_number]["speeds"])
            lap_numbers_speed.append(lap_number)
            average_speeds.append(average_speed)

    # Lap times chart (ax0)
    if lap_numbers_line:
        ax0.plot(lap_numbers_line, total_times, marker='o', linestyle='-',
                color='tab:orange', label="Lap time")
        
        ax0.yaxis.set_major_formatter(FuncFormatter(seconds_to_minutes))
        
    ax0.set_xlabel("Lap")
    ax0.set_ylabel("Time (M:SS)")
    ax0.grid()
    ax0.legend()

    # Delta chart (ax1): difference between each lap and the best lap (no title)
    if lap_times:
        best_time = min(lap_times)
        deltas = [t - best_time for t in lap_times]
        ax1.bar(lap_numbers_delta, deltas, color='tab:red')
    ax1.set_ylabel("Delta (s)")
    ax1.grid(axis="y")
    ax1.set_xticks([])

    # Configuration of speed, brake, RPM and gear charts
    for ax in [ax2, ax3, ax4, ax5, ax7]:
        ax.set_xlim(start, end)
        ax.xaxis.set_major_formatter(FuncFormatter(seconds_to_minutes))
    ax2.set_xticks([])
    ax3.set_xticks([])
    ax4.set_xticks([])
    ax5.set_xticks([])

    ax2.set_ylabel("Speed (km/h)")
    ax2.grid()

    ax3.set_ylabel("Brake (%)")
    ax3.grid()

    ax4.set_ylabel("RPM")
    ax4.grid()

    ax5.set_ylabel("Gear")
    ax5.grid()

    # Average speed per lap chart (ax8)
    if lap_numbers_speed:
        bars = ax8.bar(lap_numbers_speed, average_speeds, color=colors[:len(lap_numbers_speed)])
        
        # Add value labels
        for bar in bars:
            bar.get_height()
    
    ax8.set_ylabel("Average Speed (km/h)")
    ax8.grid(axis="y")
    ax8.set_xticks([])

    # New chart: G-Force (ax7)
    # Calculate acceleration (m/s²) from speed (km/h converted to m/s)
    # and divide by 9.81 to get G-Force.
    for idx, lap_number in enumerate(selected_laps_list):
        if lap_number not in lap_data_session:
            continue
        color = colors[idx % len(colors)]
        speed_list = lap_data_session[lap_number]["speeds"]
        duration_list = lap_data_session[lap_number]["durations"]
        if len(speed_list) >= 2 and len(duration_list) >= 2:
            speeds_mps = np.array(speed_list) * 1000/3600  # Convert to m/s
            durations = np.array(duration_list)
            # Calculate acceleration using finite differences
            acceleration = np.diff(speeds_mps) / np.diff(durations)
            # Time at midpoints
            mid_times = (durations[:-1] + durations[1:]) / 2
            g_force = acceleration / 9.81
            ax7.plot(mid_times, g_force, color=color, alpha=0.7, label=f"Lap {lap_number}")
    ax7.set_xlabel("Time (s)")
    ax7.set_ylabel("G-Force")
    ax7.grid()

    # Draw 2D map (ax6)
    ax6.set_aspect('equal')
    ax6.set_facecolor('none')
    ax6.grid(False)
    ax6.set_xticks([])
    ax6.set_yticks([])
    ax6.set_title("Trajectories")
    for spine in ax6.spines.values():
        spine.set_visible(False)
    
    # Draw trajectories on the map
    for idx, lap_number in enumerate(selected_laps_list):
        if lap_number not in lap_data_session:
            continue
        color = colors[idx % len(colors)]
        if "positions" in lap_data_session[lap_number]:
            positions = lap_data_session[lap_number]["positions"]
            x = [p[0] for p in positions]
            y = [p[1] for p in positions]
            ax6.plot(x, y, color=color, alpha=0.7, linewidth=2, label=f"Lap {lap_number}")
            if x and y:
                ax6.scatter(x[0], y[0], color=color, marker='o', s=50,
                           edgecolor='black', zorder=3)
                ax6.scatter(x[-1], y[-1], color=color, marker='s', s=50,
                           edgecolor='black', zorder=3)
    
    # Adjust map limits with 1% margin
    all_x = [p[0] for lap_number in selected_laps_list if lap_number in lap_data_session and "positions" in lap_data_session[lap_number] for p in lap_data_session[lap_number]["positions"]]
    all_y = [p[1] for lap_number in selected_laps_list if lap_number in lap_data_session and "positions" in lap_data_session[lap_number] for p in lap_data_session[lap_number]["positions"]]
    if all_x and all_y:
        margin_x = (max(all_x) - min(all_x)) * 0.01
        margin_y = (max(all_y) - min(all_y)) * 0.01
        ax6.set_xlim(min(all_x) - margin_x, max(all_x) + margin_x)
        ax6.set_ylim(min(all_y) - margin_y, max(all_y) + margin_y)
    
    ax6.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=7, frameon=True, framealpha=0.8)
    
    fig.suptitle(f"Session: {current_session} | Track: {current_track}", 
                 fontsize=14, fontweight="bold")
    
    # Configure tooltips (with mplcursors) for some charts
    cursor0 = mplcursors.cursor(ax0, hover=True)
    cursor0.connect("add", lambda sel: sel.annotation.set_text(
        f"Lap: {sel.target[0]:.0f}\nTime: {sel.target[1]:.2f} s"))
    cursor1 = mplcursors.cursor(ax1, hover=True)
    cursor1.connect("add", lambda sel: sel.annotation.set_text(
        f"Lap: {sel.target[0]:.0f}\nDelta: {sel.target[1]:.2f} s"))
    cursor2 = mplcursors.cursor(ax2, hover=True)
    cursor2.connect("add", lambda sel: sel.annotation.set_text(
        f"{sel.artist.get_label()}\nTime: {sel.target[0]:.2f} s\nSpeed: {sel.target[1]:.2f} km/h"))
    cursor3 = mplcursors.cursor(ax3, hover=True)
    cursor3.connect("add", lambda sel: sel.annotation.set_text(
        f"{sel.artist.get_label()}\nTime: {sel.target[0]:.2f} s\nBrake: {sel.target[1]:.2f} %"))
    cursor4 = mplcursors.cursor(ax4, hover=True)
    cursor4.connect("add", lambda sel: sel.annotation.set_text(
        f"{sel.artist.get_label()}\nTime: {sel.target[0]:.2f} s\nRPM: {sel.target[1]:.0f}"))
    cursor5 = mplcursors.cursor(ax5, hover=True)
    cursor5.connect("add", lambda sel: sel.annotation.set_text(
        f"{sel.artist.get_label()}\nTime: {sel.target[0]:.2f} s\nGear: {sel.target[1]:.0f}"))
    cursor7 = mplcursors.cursor(ax7, hover=True)
    cursor7.connect("add", lambda sel: sel.annotation.set_text(
        f"G-Force: {sel.target[1]:.2f}"))
    cursor8 = mplcursors.cursor(ax8, hover=True)
    cursor8.connect("add", lambda sel: sel.annotation.set_text(
        f"Lap: {sel.target[0]:.0f}\nAverage Speed: {sel.target[1]:.2f} km/h"))
    cursor6 = mplcursors.cursor(ax6, hover=True)
    cursor6.connect("add", lambda sel: sel.annotation.set_text(
        sel.artist.get_label()))
    
    canvas_fig.draw()

# Function to export the chart (add at the beginning of the code, along with other functions)
def export_chart(fig, track_name):

    # Generate filename with date/time
    date_time = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    file_path = f"{export_path}\\{track_name}_{date_time}.png"

    # Save figure with high quality
    fig.savefig(file_path, dpi=300, bbox_inches='tight', transparent=True)
    print(f"Chart exported as '{file_path}'!")

# Function to load laps when selecting session
def load_laps(event=None):
    global selected_session

    selections = listbox_sessions.curselection()
    if not selections:
        return
    
    # Get selected session
    global current_session
    current_session = available_sessions[selections[0]]
    selected_session = current_session
    
    # Update laps listbox
    listbox_laps.delete(0, tk.END)
    laps = sorted(sessions[current_session].keys())
    for lap in laps:
        listbox_laps.insert(tk.END, f"Lap {lap}")

# Create graphical interface
root = tk.Tk()
selected_session = None
root.title("Telemetry Charts")
root.geometry("1200x900")
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width - 1200) // 2
y = (screen_height - 900) // 2
root.geometry(f"+{x}+{y}")

control_frame = tk.Frame(root)
control_frame.pack(side=tk.TOP, fill=tk.X)

# Add ListBox for sessions
tk.Label(control_frame, text="Sessions:").pack(side=tk.LEFT, padx=1, pady=1)
listbox_sessions = tk.Listbox(control_frame, selectmode=tk.SINGLE, width=40)
available_sessions = sorted(sessions.keys(), reverse=True)  # Sort from most recent to oldest
for session in available_sessions:
    track = track_per_session.get(session, "Unknown Track")
    listbox_sessions.insert(tk.END, f"{session} - {track}")
listbox_sessions.pack(side=tk.LEFT, padx=1, pady=1)

listbox_sessions.bind("<<ListboxSelect>>", load_laps)

# ListBox for laps
tk.Label(control_frame, text="Laps:").pack(side=tk.LEFT, padx=1, pady=1)
listbox_laps = tk.Listbox(control_frame, selectmode=tk.MULTIPLE)
listbox_laps.pack(side=tk.LEFT, padx=1, pady=1)
tk.Button(control_frame, text="Update", command=update_chart).pack(side=tk.LEFT, padx=0, pady=0)

export_button = tk.Button(control_frame, text="Export Charts", command=lambda: export_chart(fig, track_per_session.get(selected_session.split(" - ")[0])))
export_button.pack(side=tk.RIGHT, padx=5)

canvas = tk.Canvas(root)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=canvas.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
canvas.configure(yscrollcommand=scrollbar.set)
canvas.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

frame = ttk.Frame(canvas)
canvas.create_window((0, 0), window=frame, anchor="nw")
canvas_fig = FigureCanvasTkAgg(fig, master=frame)
canvas_fig.draw()
canvas_fig.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Select last session by default if exists and select all laps
if available_sessions:
    listbox_sessions.select_set(0)
    load_laps()
    for i in range(listbox_laps.size()):
        listbox_laps.select_set(i)
    update_chart()

# Function to close the console
def close_program():
    print("Closing program...")
    root.destroy()
    # Close Python interpreter
    exit()

# Assign close function to window close event
root.protocol("WM_DELETE_WINDOW", close_program)

root.mainloop()