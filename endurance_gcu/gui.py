import tkinter as tk
from tkinter import messagebox
import serial
import threading
import time

# Connect to Arduino
try:
    arduino = serial.Serial('COM3', 9600, timeout=1)  # Replace 'COM3' with your Arduino's port
except Exception as e:
    messagebox.showerror("Error", f"Could not connect to Arduino: {e}")
    arduino = None

# GUI Functions
def send_servo_command():
    if arduino:
        try:
            angle = int(servo_angle_entry.get())
            if 0 <= angle <= 180:
                command = f"SERVO:{angle}\n"
                arduino.write(command.encode())
            else:
                messagebox.showerror("Error", "Servo angle must be between 0 and 180")
        except ValueError:
            messagebox.showerror("Error", "Invalid servo angle")

def read_arduino_data():
    if arduino:
        while True:
            try:
                data = arduino.readline().decode().strip()
                if data.startswith("TEMP:"):
                    temperature = data[5:]
                    temperature_label.config(text=f"Temperature: {temperature} °C")
            except Exception as e:
                print(f"Error reading from Arduino: {e}")
                break

# Start data reading in a separate thread
def start_reading():
    read_thread = threading.Thread(target=read_arduino_data)
    read_thread.daemon = True
    read_thread.start()

# Close the application
def on_closing():
    if arduino:
        arduino.close()
    root.destroy()

# GUI Setup
root = tk.Tk()
root.title("Arduino Controller")

# Servo Control
servo_frame = tk.Frame(root)
servo_frame.pack(pady=10)

tk.Label(servo_frame, text="Servo Angle (0-180):").pack(side=tk.LEFT)
servo_angle_entry = tk.Entry(servo_frame)
servo_angle_entry.pack(side=tk.LEFT, padx=5)
tk.Button(servo_frame, text="Set Angle", command=send_servo_command).pack(side=tk.LEFT)

# Temperature Display
temperature_label = tk.Label(root, text="Temperature: N/A", font=("Arial", 14))
temperature_label.pack(pady=20)

# Handle close event
root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the GUI and serial reading
start_reading()
root.mainloop()
