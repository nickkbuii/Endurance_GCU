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
from pytz import timezone

# Configure Serial Communication
arduino = serial.Serial('COM15', 57600, timeout=0.01) ## Nolan's Port: '/dev/cu.usbmodem101'

def read_from_arduino():
    global time_counter
    pst_tz = timezone("US/Pacific")
    while not stop_thread:
        if arduino.in_waiting > 0:
            line = arduino.readline().decode('utf-8').strip()
            current_time = datetime.now(pst_tz).strftime("%Y-%m-%d %H:%M:%S")
            data_entry = [time_counter, None, None, None, None, None, None, None, current_time]
            if line.startswith("TEMP:"):
                temp = float(line.split(':')[1])
                root.after(0, lambda: therm_label_var.set(f"Thermocouple: {temp}°C"))
                therm_data.append(temp)
                data_entry[1] = temp
            elif line.startswith("MASS FLOW"):
                massFlow = float(line.split(':')[1])
                root.after(0, lambda: massFlow_label_var.set(f"Mass Flow Rate: {massFlow} g/s"))
                data_entry[2] = massFlow
            elif line.startswith("PUMP:"):
                pump_speed = int(line.split(':')[1])
                root.after(0, lambda: pump_label_var.set(f"Pump Speed: {pump_speed}%"))
                data_entry[3] = pump_speed
            elif line.startswith("ENGINE:"):
                engine_speed = int(line.split(':')[1])
                root.after(0, lambda: engine_label_var.set(f"Engine Speed: {engine_speed}%"))
                data_entry[4] = engine_speed
            elif line.startswith("SHUTOFF:"):
                shutoff_angle = int(line.split(':')[1])
                root.after(0, lambda: shutoff_label_var.set(f"Shutoff Angle: {shutoff_angle}°"))
                data_entry[5] = shutoff_angle
            elif line.startswith("PROPANE:"):
                propane_angle = int(line.split(':')[1])
                root.after(0, lambda: propane_label_var.set(f"Propane Angle: {propane_angle}°"))
                data_entry[6] = propane_angle
            elif line.startswith("STATUS:"):
                status = line.split(':')[1]
                root.after(0, lambda: status_label_var.set(f"Status: {status}"))
                data_entry[7] = status

            if any(data_entry[1:]):
                data_log.append(data_entry)
                time_counter += 1

def update_plot():
    ax.clear()
    ax.plot(list(therm_data), color='red', label='Temperature (°C)')
    ax.set_title("Real-time Temperature Data")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Temperature (°C)")
    ax.set_ylim(0,850)
    ax.legend()
    ax.grid(True)

    fig.tight_layout()
    canvas.draw()

    if not stop_thread:
        root.after(500, update_plot)

def set_pump_speed(val):
    speed = int(val)
    arduino.write(f"PUMP:{speed}\n".encode('utf-8'))

def set_engine_speed(val):
    speed = int(val)
    arduino.write(f"ENGINE:{speed}\n".encode('utf-8'))

def save_data_to_csv():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data_{timestamp}.csv"
    try:
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                "Time (s)", "Temperature (°C)", "Mass Flow Rate (g/s)",
                "Pump Speed (%)", "Engine Speed (%)",
                "Shutoff Angle (°)", "Propane Angle (°)", "Status", "Timestamp (PST)"
            ])
            writer.writerows(data_log)
        messagebox.showinfo("Success", f"Data saved to {filename}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save data: {str(e)}")

def create_control(label, command, row):
    ttk.Label(controls_frame, text=label, font=("Arial", 20)).grid(row=row, column=0, sticky="w", padx=10)
    slider = tk.Scale(controls_frame, from_=0, to=100, orient="horizontal", length=300, command=command, font=("Arial", 20))
    slider.grid(row=row, column=1, padx=10)
    return slider

def update_shutoff_angle(change):
    global current_shutoff_angle
    current_shutoff_angle = max(0, min(180, current_shutoff_angle + change))
    arduino.write(f"SHUTOFF:{current_shutoff_angle}\n".encode('utf-8'))

def create_shutoff_buttons(label_text, row):
    ttk.Label(controls_frame, text=label_text, font=("Arial", 20)).grid(row=row, column=0, sticky="w", padx=10)
    button_frame = ttk.Frame(controls_frame)
    button_frame.grid(row=row, column=1, pady=10)

    ttk.Button(button_frame, text="-10°", width=6, command=lambda: update_shutoff_angle(-10), style="Large.TButton").pack(side="left", padx=5)
    ttk.Button(button_frame, text="+10°", width=6, command=lambda: update_shutoff_angle(10), style="Large.TButton").pack(side="left", padx=5)
    ttk.Button(button_frame, text="0°", width=6, command=lambda: update_shutoff_angle(-current_shutoff_angle), style="Large.TButton").pack(side="left", padx=5)
    ttk.Button(button_frame, text="90°", width=6, command=lambda: update_shutoff_angle(90 - current_shutoff_angle), style="Large.TButton").pack(side="left", padx=5)

def update_propane_angle(change):
    global current_propane_angle
    current_propane_angle = max(0, min(180, current_propane_angle + change))
    arduino.write(f"PROPANE:{current_propane_angle}\n".encode('utf-8'))

def create_propane_buttons(row):
    ttk.Label(controls_frame, text="Propane Servo Angle:", font=("Arial", 20)).grid(row=row, column=0, sticky="w", padx=10)
    button_frame = ttk.Frame(controls_frame)
    button_frame.grid(row=row, column=1, pady=10)

    ttk.Button(button_frame, text="-10°", width=6, command=lambda: update_propane_angle(-10), style="Large.TButton").pack(side="left", padx=5)
    ttk.Button(button_frame, text="+10°", width=6, command=lambda: update_propane_angle(10), style="Large.TButton").pack(side="left", padx=5)
    ttk.Button(button_frame, text="OFF", width=6, command=lambda: update_propane_angle(-current_propane_angle + 75), style="Large.TButton").pack(side="left", padx=5)

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

# States
therm_data = deque([0] * 60, maxlen=60)  # Last 60 temperature readings
current_shutoff_angle = 0
current_propane_angle = 0

# List to store all data for saving
data_log = []
time_counter = 0
stop_thread = False

# GUI Setup
root = tk.Tk()
root.title("ENDURANCE GCU")
root.geometry("2000x1000")
root.resizable(True, True)
root.config(bg="#F0F0F0")
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)
root.grid_rowconfigure(0, weight=1)

style = ttk.Style()
style.configure("Large.TButton", font=("Arial", 17))

# Main layout frames
data_frame = ttk.Frame(root, padding="5")
data_frame.grid(row=0, column=0, sticky="nsew")
controls_frame = ttk.Frame(root, padding="5")
controls_frame.grid(row=0, column=2, sticky="nsew")

# Frame for displaying labels
info_frame = ttk.Frame(root, padding="5")
info_frame.grid(row=0, column=1, sticky="nsew")

# Frame for plotting
plot_frame = ttk.Frame(data_frame)
plot_frame.pack(side="top", fill="both", expand=True, padx=10, pady=10)

# Creating data logs
therm_label_var = tk.StringVar(value="Temperature: N/A")
ttk.Label(info_frame, textvariable=therm_label_var, font=("Arial", 20)).grid(row=0, column=0, sticky="w", padx=10)

massFlow_label_var = tk.StringVar(value="Mass Flow Rate: N/A")
ttk.Label(info_frame, textvariable=massFlow_label_var, font=("Arial", 20)).grid(row=1, column=0, sticky="w", padx=10)

pump_label_var = tk.StringVar(value="Pump Speed: N/A")
ttk.Label(info_frame, textvariable=pump_label_var, font=("Arial", 20)).grid(row=2, column=0, sticky="w", padx=10)

engine_label_var = tk.StringVar(value="Engine Speed: N/A")
ttk.Label(info_frame, textvariable=engine_label_var, font=("Arial", 20)).grid(row=3, column=0, sticky="w", padx=10)

shutoff_label_var = tk.StringVar(value="Shutoff Angle: N/A")
ttk.Label(info_frame, textvariable=shutoff_label_var, font=("Arial", 20)).grid(row=4, column=0, sticky="w", padx=10)

propane_label_var = tk.StringVar(value="Propane Angle: N/A")
ttk.Label(info_frame, textvariable=propane_label_var, font=("Arial", 20)).grid(row=5, column=0, sticky="w", padx=10)

status_label_var = tk.StringVar(value="Status: N/A")
ttk.Label(info_frame, textvariable=status_label_var, font=("Arial", 20)).grid(row=6, column=0, sticky="w", padx=10)

# Creating plots
fig, (ax) = plt.subplots(1, 1, figsize=(6, 4))
canvas = FigureCanvasTkAgg(fig, master=plot_frame)
canvas.get_tk_widget().pack(side="top", fill="both")

# Creating controls
create_control("Pump Speed:", lambda val: set_pump_speed(val), 0)
create_control("Engine Speed:", lambda val: set_engine_speed(val), 1)
create_shutoff_buttons("Shutoff Servo Angle:", 2)
create_propane_buttons(6)
ttk.Button(controls_frame, text="Save Data", command=save_data_to_csv, style="Large.TButton").grid(row=8, column=0, columnspan=2, pady=20)

root.protocol("WM_DELETE_WINDOW", on_closing)
start_thread()
update_plot()
root.mainloop()