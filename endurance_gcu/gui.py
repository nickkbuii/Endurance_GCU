import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import serial
import threading
from collections import deque
import sys

# Configure Serial Communication
arduino = serial.Serial('COM15', 9600, timeout=1)

# Data Storage for Plotting
therm_data = deque([0]*60, maxlen=60)  # Store the last 60 temperature readings
weight_data = deque([0]*60, maxlen=60)  # Store the last 60 weight readings

# Flag to stop the thread
stop_thread = False

# Function to read data from Arduino
def read_from_arduino():
    while not stop_thread:
        if arduino.in_waiting > 0:
            line = arduino.readline().decode('utf-8').strip()
            if line.startswith("TEMP:"):
                temp = float(line.split(':')[1])
                therm_label_var.set(f"Thermocouple: {temp}°C")
                therm_data.append(temp)
            elif line.startswith("PUMP:"):
                pump_label_var.set(f"Pump Speed: {line.split(':')[1]}%")
            elif line.startswith("ENGINE:"):
                engine_label_var.set(f"Engine Speed: {line.split(':')[1]}%")
            elif line.startswith("SHUTOFF:"):
                shutoff_label_var.set(f"Shutoff Angle: {line.split(':')[1]}°")
            elif line.startswith("PROPANE:"):
                propane_label_var.set(f"Propane Angle: {line.split(':')[1]}°")
            elif line.startswith("WEIGHT:"):
                weight = float(line.split(':')[1])
                weight_label_var.set(f"Weight: {weight} g")

# Function to update the thermocouple plot
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
    
    # Adjust layout to prevent labels from being cut off
    fig.tight_layout()
    
    canvas.draw()  # Redraw the plot
    if not stop_thread:
        root.after(100, update_plot)  # Refresh the plot every 100 ms

# Function to send pump speed to Arduino
def set_pump_speed(val):
    speed = int(val)
    arduino.write(f"PUMP:{speed}\n".encode('utf-8'))

# Function to send engine speed to Arduino
def set_engine_speed(val):
    speed = int(val)
    arduino.write(f"ENGINE:{speed}\n".encode('utf-8'))

# Function to set shutoff servo angle
def set_shutoff_angle(val):
    angle = int(float(val))
    arduino.write(f"SHUTOFF:{angle}\n".encode('utf-8'))

# Function to set propane servo angle
def set_propane_angle(val):
    angle = int(float(val))
    arduino.write(f"PROPANE:{angle}\n".encode('utf-8'))

# --- GUI Setup ---
root = tk.Tk()
root.title("Arduino Controller")
root.geometry("800x600")
root.config(bg="#F0F0F0")  # Set background color

# Frame for displaying labels
info_frame = ttk.Frame(root, padding="20")
info_frame.pack(pady=10)

# Labels to display data with better font and color
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

# Add joystick-like control for pump speed
def create_joystick_control(label_text, command, row):
    ttk.Label(controls_frame, text=label_text, font=("Arial", 12)).grid(row=row, column=0, pady=5)
    scale = tk.Scale(controls_frame, from_=0, to=100, orient="horizontal", length=300, tickinterval=20, command=command)
    scale.set(0)  # Default neutral position
    scale.grid(row=row, column=1, padx=10, pady=5)
    return scale

# Create joystick controls for pump and engine
pump_scale = create_joystick_control("Pump Speed", lambda val: set_pump_speed(val), 5)
engine_scale = create_joystick_control("Engine Speed", lambda val: set_engine_speed(val), 6)

# Create sliders for servo control (Shutoff and Propane)
def create_angle_control(label_text, command, row):
    ttk.Label(controls_frame, text=label_text, font=("Arial", 12)).grid(row=row, column=0, pady=5)
    scale = tk.Scale(controls_frame, from_=0, to=180, orient="horizontal", length=300, tickinterval=20, command=command)
    scale.set(90)  # Default position at 90 degrees (neutral position)
    scale.grid(row=row, column=1, padx=10, pady=5)
    return scale

# Create sliders for shutoff and propane servo angles
shutoff_angle_scale = create_angle_control("Shutoff Servo Angle", lambda val: set_shutoff_angle(val), 7)
propane_angle_scale = create_angle_control("Propane Servo Angle", lambda val: set_propane_angle(val), 8)

# Start a thread to continuously read from Arduino
def start_thread():
    global stop_thread
    stop_thread = False
    thread = threading.Thread(target=read_from_arduino, daemon=True)
    thread.start()

# Start updating the plot and the thread
def on_closing():
    global stop_thread
    stop_thread = True  # Set stop flag to True
    arduino.close()  # Close serial connection properly
    root.destroy()  # Close the Tkinter window
    sys.exit()  # Terminate the program

root.protocol("WM_DELETE_WINDOW", on_closing)  # Bind the close button to on_closing

start_thread()  # Start the Arduino reading thread
update_plot()  # Start updating the plot

# Run the GUI
root.mainloop()