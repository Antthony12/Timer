import matplotlib.pyplot as plt
import numpy as np
import re
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D
import os

# Initial configuration
file_path = r"C:\Users\example\Desktop\scripts\Logs\telemetriagta5.log"

# Dictionaries to store data
sessions = {}
track_per_session = {}
last_mouse_position = None
rotation_mode = False

# Regular expressions
session_start_pattern = re.compile(r"=== Telemetry started (.+?) (.+?) (.+?) ===")
position_pattern = re.compile(r"Position: \((-?\d+[\.,]?\d*), (-?\d+[\.,]?\d*), (-?\d+[\.,]?\d*)\)")
track_pattern = re.compile(r"Track: (.+?) \| Lap:")
lap_pattern = re.compile(r"Lap: (\d+)")

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

# Process file
current_session = None
current_lap = 0

with open(file_path, "r", encoding="utf-8") as file:
    for line in file:
        session_match = session_start_pattern.search(line)
        if session_match:
            session_date = session_match.group(1).strip()
            session_time = session_match.group(2).strip()
            track = session_match.group(3).strip()
            current_session = f"{session_date} {session_time}"
            if current_session not in sessions:
                sessions[current_session] = {}
                track_per_session[current_session] = track
            continue

        if current_session is None:
            continue

        track_match = track_pattern.search(line)
        if track_match:
            track_per_session[current_session] = track_match.group(1).strip()

        lap_match = lap_pattern.search(line)
        if lap_match:
            current_lap = int(lap_match.group(1))
            if current_lap not in sessions[current_session]:
                sessions[current_session][current_lap] = {'x': [], 'y': [], 'z': []}

        position_match = position_pattern.search(line)
        if position_match and current_lap > 0:
            x, y, z = position_match.groups()
            x, y, z = x.replace(",", "."), y.replace(",", "."), z.replace(",", ".")
            sessions[current_session][current_lap]['x'].append(float(x))
            sessions[current_session][current_lap]['y'].append(float(y))
            sessions[current_session][current_lap]['z'].append(float(z))

# Function to update the chart
def update_chart(event=None):
    ax.cla()
    session_string = combo_sessions.get()
    session = session_string.split(" - ")[0]  # Only date and time
    
    if session in sessions:
        laps = sessions[session]
        colors = plt.cm.viridis(np.linspace(0, 1, len(laps)))
        
        # First collect all points to calculate ranges
        all_x, all_y, all_z = [], [], []
        for lap, coordinates in laps.items():
            if coordinates['x']:
                all_x.extend(coordinates['x'])
                all_y.extend(coordinates['y'])
                all_z.extend(coordinates['z'])
        
        if not all_x:
            return
            
        # Calculate ranges for each axis
        range_x = max(all_x) - min(all_x)
        range_y = max(all_y) - min(all_y)
        range_z = max(all_z) - min(all_z)
        
        # Adjust aspect ratio based on actual ranges
        aspect_ratio = [range_x, range_y, range_z * 0.2]  # Reduce importance of Z axis
        ax.set_box_aspect(aspect_ratio)
        
        # Draw laps
        for index, (lap, coordinates) in enumerate(laps.items()):
            if coordinates['x']:
                x = np.array(coordinates['x'])
                y = np.array(coordinates['y'])
                z = np.array(coordinates['z'])
                ax.plot(x, y, z, color=colors[index], alpha=0.7, linewidth=2,
                      label=f"Lap {lap}")
        
        # Chart configuration
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_zticks([])
        ax.grid(False)
        
        # Adjust view for better perspective
        ax.view_init(elev=30, azim=45)  # Viewing angle
        
        for axis in [ax.xaxis, ax.yaxis, ax.zaxis]:
            axis.pane.fill = False
            axis.line.set_color((0.0, 0.0, 0.0, 0.0))
        
        if session in track_per_session:
            ax.set_title(f"Track: {track_per_session[session]}\nSession: {session}", pad=20)
        
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        canvas.draw()

# Function to handle zoom with mouse wheel
def zoom(event):
    if event.delta > 0 or event.num == 4:
        scale = 0.9  # Zoom in
    else:
        scale = 1.1  # Zoom out

    # Get current limits
    x_limits = ax.get_xlim3d()
    y_limits = ax.get_ylim3d()
    z_limits = ax.get_zlim3d()

    def scale_limits(limits):
        middle = (limits[0] + limits[1]) / 2
        range_val = (limits[1] - limits[0]) * scale / 2
        return (middle - range_val, middle + range_val)

    ax.set_xlim3d(scale_limits(x_limits))
    ax.set_ylim3d(scale_limits(y_limits))
    ax.set_zlim3d(scale_limits(z_limits))

    canvas.draw()

# Create graphical interface
root = tk.Tk()
root.title("3D Telemetry Visualization")
root.geometry("1000x800")

# Control frame
control_frame = tk.Frame(root)
control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

# Session selector
tk.Label(control_frame, text="Session:").pack(side=tk.LEFT)
formatted_sessions = [f"{session} - {track_per_session.get(session, 'Unknown Track')}" for session in sorted(sessions.keys(), reverse=True)]
combo_sessions = ttk.Combobox(control_frame, values=formatted_sessions, width=50)
combo_sessions.pack(side=tk.LEFT, padx=5)
combo_sessions.bind("<<ComboboxSelected>>", update_chart)

# Control buttons
tk.Button(control_frame, text="Reset Zoom", command=update_chart).pack(side=tk.LEFT, padx=5)

# Chart frame
chart_frame = tk.Frame(root)
chart_frame.pack(fill=tk.BOTH, expand=True)

# Create 3D figure
figure = plt.figure(figsize=(8, 10))
ax = figure.add_subplot(111, projection='3d')

# Initial chart configuration
ax.set_xticks([])
ax.set_yticks([])
ax.set_zticks([])
ax.grid(False)
ax.set_title("Select a session", pad=20)

for axis in [ax.xaxis, ax.yaxis, ax.zaxis]:
    axis.pane.fill = False
    axis.line.set_color((0.0, 0.0, 0.0, 0.0))

# Adjust chart aspect ratio
ax.set_box_aspect([1, 1, 0.1])

# Canvas for the chart
canvas = FigureCanvasTkAgg(figure, master=chart_frame)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Associate scroll events
canvas.get_tk_widget().bind("<MouseWheel>", zoom)

# Select last session by default if exists
if formatted_sessions:
    combo_sessions.set(formatted_sessions[0])
    update_chart()

# Function to close the console
def close_program():
    print("Closing program...")
    root.destroy()
    # Close Python interpreter
    exit()

root.protocol("WM_DELETE_WINDOW", close_program)

root.mainloop()