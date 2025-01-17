import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import serial
import threading
from collections import deque
import csv
from datetime import datetime
import sys

# Configure Serial Communication
arduino = serial.Serial('COM15', 9600, timeout=1)

# Data Storage for Plotting
therm_data = deque([0]*60, maxlen=60)  # Store the last 60 temperature readings
weight_data = deque([0]*60, maxlen=60)  # Store the last 60 weight readings

# List to store all data for saving
# Format: [time, temperature, weight, pump, engine, shutoff_angle, propane_angle]
data_log = []
time_counter = 0  # Time counter for CSV logging (seconds)

# Flag to stop the thread
stop_thread = False

# Function to read data from Arduino
def read_from_arduino():
    global time_counter
    while not stop_thread:
        if arduino.in_waiting > 0:
            line = arduino.readline().decode('utf-8').strip()
            data_entry = [time_counter, None, None, None, None, None, None]  # Initialize a new entry

            if line.startswith("TEMP:"):
                temp = float(line.split(':')[1])
                therm_label_var.set(f"Thermocouple: {temp}°C")
                therm_data.append(temp)
                data_entry[1] = temp
            elif line.startswith("PUMP:"):
                pump_speed = int(line.split(':')[1])
                pump_label_var.set(f"Pump Speed: {pump_speed}%")
                data_entry[3] = pump_speed
            elif line.startswith("ENGINE:"):
                engine_speed = int(line.split(':')[1])
                engine_label_var.set(f"Engine Speed: {engine_speed}%")
                data_entry[4] = engine_speed
            elif line.startswith("SHUTOFF:"):
                shutoff_angle = int(line.split(':')[1])
                shutoff_label_var.set(f"Shutoff Angle: {shutoff_angle}°")
                data_entry[5] = shutoff_angle
            elif line.startswith("PROPANE:"):
                propane_angle = int(line.split(':')[1])
                propane_label_var.set(f"Propane Angle: {propane_angle}°")
                data_entry[6] = propane_angle
            elif line.startswith("WEIGHT:"):
                weight = float(line.split(':')[1])
                weight_label_var.set(f"Weight: {weight} g")
                weight_data.append(weight)
                data_entry[2] = weight

            # Append to data log if at least one field is filled
            if any(data_entry[1:]):
                data_log.append(data_entry)
                time_counter += 1

# Function to update the plots
def update_plot():
    ax.clear()
    ax.plot(list(therm_data), color='red', label='Temperature (°C)')
    ax.set_title("Real-time Thermocouple Data")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Temperature (°C)")
    ax.legend()
    ax.grid(True)

    ax1.clear()
    ax1.plot(list(weight_data), color='blue', label='Weight (g)')
    ax1.set_title("Real-time Weight Data")
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Weight (g)")
    ax1.legend()
    ax1.grid(True)

    fig.tight_layout()
    canvas.draw()

    if not stop_thread:
        root.after(100, update_plot)

# Function to send pump speed to Arduino
def set_pump_speed(val):
    speed = int(val)
    arduino.write(f"PUMP:{speed}\n".encode('utf-8'))

# Function to send engine speed to Arduino
def set_engine_speed(val):
    speed = int(val)
    arduino.write(f"ENGINE:{speed}\n".encode('utf-8'))

# Function to set shutoff servo angle
current_shutoff_angle = 0  # Default angle for shutoff servo
def update_shutoff_angle(change):
    global current_shutoff_angle
    current_shutoff_angle = max(0, min(180, current_shutoff_angle + change))
    arduino.write(f"SHUTOFF:{current_shutoff_angle}\n".encode('utf-8'))
    shutoff_label_var.set(f"Shutoff Angle: {current_shutoff_angle}°")

# Function to set propane servo angle
current_propane_angle = 0  # Default angle for propane servo
def update_propane_angle(change):
    global current_propane_angle
    current_propane_angle = max(0, min(180, current_propane_angle + change))
    arduino.write(f"PROPANE:{current_propane_angle}\n".encode('utf-8'))
    propane_label_var.set(f"Propane Angle: {current_propane_angle}°")

# Function to save data to CSV
def save_data_to_csv():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data_{timestamp}.csv"
    try:
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                "Time (s)", "Temperature (°C)", "Weight (g)", 
                "Pump Speed (%)", "Engine Speed (%)", 
                "Shutoff Angle (°)", "Propane Angle (°)"
            ])
            writer.writerows(data_log)
        messagebox.showinfo("Success", f"Data saved to {filename}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save data: {str(e)}")

# --- GUI Setup ---
root = tk.Tk()
root.title("Arduino Controller")
root.geometry("800x600")
root.config(bg="#F0F0F0")

# Frame for displaying labels
info_frame = ttk.Frame(root, padding="20")
info_frame.pack(pady=10)

therm_label_var = tk.StringVar(value="Thermocouple: N/A")
therm_label = tk.Label(info_frame, textvariable=therm_label_var, font=("Arial", 14), bg="#F0F0F0", anchor="w")
therm_label.grid(row=0, column=0, sticky="w", pady=5)

weight_label_var = tk.StringVar(value="Weight: N/A")
weight_label = tk.Label(info_frame, textvariable=weight_label_var, font=("Arial", 14), bg="#F0F0F0", anchor="w")
weight_label.grid(row=1, column=0, sticky="w", pady=5)

# Add the plots below the labels
fig, (ax, ax1) = plt.subplots(2, 1, figsize=(5, 6))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(pady=10)

pump_label_var = tk.StringVar(value="Pump Speed: N/A")
pump_label = tk.Label(info_frame, textvariable=pump_label_var, font=("Arial", 14), bg="#F0F0F0", anchor="w")
pump_label.grid(row=2, column=0, sticky="w", pady=5)

engine_label_var = tk.StringVar(value="Engine Speed: N/A")
engine_label = tk.Label(info_frame, textvariable=engine_label_var, font=("Arial", 14), bg="#F0F0F0", anchor="w")
engine_label.grid(row=3, column=0, sticky="w", pady=5)

shutoff_label_var = tk.StringVar(value="Shutoff Angle: N/A")
shutoff_label = tk.Label(info_frame, textvariable=shutoff_label_var, font=("Arial", 14), bg="#F0F0F0", anchor="w")
shutoff_label.grid(row=4, column=0, sticky="w", pady=5)

propane_label_var = tk.StringVar(value="Propane Angle: N/A")
propane_label = tk.Label(info_frame, textvariable=propane_label_var, font=("Arial", 14), bg="#F0F0F0", anchor="w")
propane_label.grid(row=5, column=0, sticky="w", pady=5)

# Frame for controls (joystick-like scales for pump and engine)
controls_frame = ttk.Frame(root, padding="20")
controls_frame.pack(pady=20)

def create_joystick_control(label_text, command, row):
    ttk.Label(controls_frame, text=label_text, font=("Arial", 12)).grid(row=row, column=0, pady=5)
    scale = tk.Scale(controls_frame, from_=0, to=100, orient="horizontal", length=300, tickinterval=20, command=command)
    scale.set(0)
    scale.grid(row=row, column=1, padx=10, pady=5)
    return scale

pump_scale = create_joystick_control("Pump Speed", lambda val: set_pump_speed(val), 5)
engine_scale = create_joystick_control("Engine Speed", lambda val: set_engine_speed(val), 6)

# Function to set shutoff servo angle to a specific value
def set_shutoff_to_angle(angle):
    global current_shutoff_angle
    current_shutoff_angle = max(0, min(180, angle))  # Ensure the angle is within bounds (0-180)
    arduino.write(f"SHUTOFF:{current_shutoff_angle}\n".encode('utf-8'))
    shutoff_label_var.set(f"Shutoff Angle: {current_shutoff_angle}°")

# Function to create increment buttons along with 0 and 90 degree buttons
def create_shutoff_buttons_with_preset(label_text, update_command, row):
    ttk.Label(controls_frame, text=label_text, font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
    button_frame = ttk.Frame(controls_frame)
    button_frame.grid(row=row, column=1, pady=5)

    # Existing buttons for adjusting angle by +/- 10 degrees
    minus_button = ttk.Button(button_frame, text="-", width=4, command=lambda: update_command(-10))
    minus_button.pack(side="left", padx=2)

    plus_button = ttk.Button(button_frame, text="+", width=4, command=lambda: update_command(10))
    plus_button.pack(side="left", padx=2)

    # New buttons for setting the angle to 0 and 90 degrees
    zero_button = ttk.Button(button_frame, text="0°", width=4, command=lambda: set_shutoff_to_angle(0))
    zero_button.pack(side="left", padx=2)

    ninety_button = ttk.Button(button_frame, text="90°", width=4, command=lambda: set_shutoff_to_angle(90))
    ninety_button.pack(side="left", padx=2)

# Add the new buttons for Shutoff Servo Angle with 0° and 90° options
create_shutoff_buttons_with_preset("Shutoff Servo Angle", update_shutoff_angle, 7)

# Function to set propane servo angle to 75 degrees
def set_propane_off():
    global current_propane_angle
    current_propane_angle = 75  # Set the propane angle to 75 degrees
    arduino.write(f"PROPANE:{current_propane_angle}\n".encode('utf-8'))
    propane_label_var.set(f"Propane Angle: {current_propane_angle}°")

# Propane Servo Angle Controls with OFF Button
def create_propane_buttons_with_off(label_text, update_command, off_command, row):
    ttk.Label(controls_frame, text=label_text, font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
    button_frame = ttk.Frame(controls_frame)
    button_frame.grid(row=row, column=1, pady=5)

    minus_button = ttk.Button(button_frame, text="-", width=4, command=lambda: update_command(-10))
    minus_button.pack(side="left", padx=2)

    plus_button = ttk.Button(button_frame, text="+", width=4, command=lambda: update_command(10))
    plus_button.pack(side="left", padx=2)

    off_button = ttk.Button(button_frame, text="OFF", width=4, command=off_command)
    off_button.pack(side="left", padx=2)

# Add buttons for Propane Servo Angle with OFF option
create_propane_buttons_with_off("Propane Servo Angle", update_propane_angle, set_propane_off, 8)

save_button = ttk.Button(controls_frame, text="Save Data", command=save_data_to_csv)
save_button.grid(row=9, column=0, columnspan=2, pady=10)

def start_thread():
    global stop_thread
    stop_thread = False
    thread = threading.Thread(target=read_from_arduino, daemon=True)
    thread.start()

def on_closing():
    global stop_thread
    stop_thread = True
    arduino.close()
    root.destroy()
    sys.exit()

root.protocol("WM_DELETE_WINDOW", on_closing)

start_thread()
update_plot()

root.mainloop()