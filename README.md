# ENDURANCE – Ground Control Unit (GCU)
**Stanford University Turbojet Engine Research Project**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Arduino](https://img.shields.io/badge/Arduino-Giga%20R1%20WiFi-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)]()
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter%20%2B%20Matplotlib-blueviolet.svg)]()
[![Status](https://img.shields.io/badge/Status-Active-blue.svg)]()

---

## 🧭 Overview

**ENDURANCE** is a **micro turbojet engine research platform** developed at **Stanford University** for performance, stability, and control experimentation.  

This repository contains the **Ground Control Unit (GCU)** — a hybrid **Arduino Giga R1 + Python GUI** system that provides real-time control, data visualization, and telemetry logging for the ENDURANCE turbojet engine test stand.

The GCU software coordinates:
- Sensor acquisition and actuator control on the **Arduino Giga R1**
- Real-time plotting, user interface, and data logging on the **Python host GUI**

---

## ⚙️ System Architecture

| Layer | Platform | Description |
|--------|-----------|-------------|
| **Embedded Controller** | Arduino **Giga R1 WiFi** | Handles sensor readings, actuator control, and serial telemetry |
| **Ground Station GUI** | Python 3 / Tkinter | Provides operator interface, live data plotting, and CSV logging |

**Communication Protocol:** USB Serial @ 57,600 baud  
**Direction:**  
- **Python → Arduino:** ASCII commands (e.g., `PUMP:50`)  
- **Arduino → Python:** sensor telemetry (`TEMP:422.3`, `MASS FLOW:0.48`, etc.)

---

## ✅ Implemented Features

### 🧩 Arduino Firmware (Embedded GCU)

#### **1. Sensor Interfaces**
- **Thermocouple** via **MAX6675/MAX31855**  
  - Reads exhaust gas temperature through `Thermocouple` class  
- **Load Cell / Fuel Flow Sensor** via UART2 (Serial2)  
  - Reads mass flow and computes average over sampled intervals (`Weight` class)  
- **Analog inputs** for pump voltage or system health sensors  

#### **2. Actuator Control**
- **Fuel Pump** (PWM DC motor): `Pump` class using motor driver (L298N or equivalent)  
- **Throttle Control (ESC):** `Engine` class using Servo PWM (1000–2000 µs)  
- **Propane and Shutoff Valves:** `ServoMotor` class controlling hobby servos (0–180° rotation)  
- **Initialization Routine:** sets all actuators to safe starting positions  

#### **3. Command Interface**
Arduino receives ASCII commands via serial:
