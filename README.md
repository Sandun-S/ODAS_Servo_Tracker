
# ODAS-Based 3D Sound Source Tracker with Servo Control

This project uses the ODAS (Open embeddeD Audition System) framework with a modified ODAS Web server to track a sound source in real-time and control two servos (Pan and Tilt) on an ESP32 accordingly.

---

## 🔧 System Components

- **ODAS Core**: Provides sound source localization
- **ODAS Web (modified)**: Sends `tracking` and `potential` source data via TCP (ports 9000, 9001)
- **Python Listener**:
  - Receives the TCP streams, parses JSON
  - Locks to best/strongest source
  - Converts direction to Azimuth and Elevation
  - Sends UDP command to ESP32
- **ESP32**:
  - Receives `AZ <deg> EL <deg>` via UDP
  - Converts az/el to servo angles
  - Controls 2x Servo Motors (Pan and Tilt)

---

## ⚙️ How It Works

```mermaid
flowchart TD
    subgraph ODAS System
      A1[ODAS Core] --> A2[ODAS Web - Modified servers.js]
    end

    A2 -->|TCP JSON| B1[Python Listener]
    B1 -->|UDP: "AZ <deg> EL <deg>"| C1[ESP32 Board]
    C1 -->|PWM| D1[Pan Servo]
    C1 -->|PWM| D2[Tilt Servo]
```

---

## 📡 Communication Ports

| Component        | Protocol | Port | Description                        |
|------------------|----------|------|------------------------------------|
| ODAS → Python    | TCP      | 9000 | Tracking sources                   |
| ODAS → Python    | TCP      | 9001 | Potential sources                  |
| Python → ESP32   | UDP      | 4210 | Command in format `AZ <angle> EL <angle>` |

---

## 🧠 Features

- Tracks strongest sound source using ODAS energy values
- Azimuth/Elevation calculation from 3D source coordinates
- Gracefully switches source only when significantly stronger
- Maps angles to servo range for 2D physical movement

---

## 📁 File Overview

| File                | Description                              |
|---------------------|------------------------------------------|
| `servers.js`        | Modified ODAS Web file to add TCP output |
| `esp32_servo.ino`   | Receives UDP and controls servos         |
| `odas_listener.py`  | Listens TCP → Parses → Sends UDP         |

---

## 🛠️ Setup Instructions

### 1. ODAS + ODAS Web

- Clone ODAS and ODAS Web
- Replace `servers.js` in ODAS Web with the modified one
- Run ODAS and ODAS Web

### 2. ESP32

- Flash `esp32_servo.ino`
- Set `PAN_PIN`, `TILT_PIN` to connected GPIOs
- Adjust `WiFi` credentials and `local_IP` if needed

### 3. Python Listener

```bash
pip install --upgrade json
```

Then run:

```bash
python odas_listener.py
```

---

## 🧪 Example UDP Payload

```text
AZ 123.4 EL 42.0
```

This means: rotate pan servo to 123.4°, tilt to 42.0°.

---

## 🖥 Sample Output (Terminal)

```
🔐 New Lock ID 3 - Az: 110.5°, El: 33.0°
🔒 Continue Tracking ID 3 - Az: 111.2°, El: 32.7°
🔁 Switched to stronger source ID 5 - Az: 95.3°, El: 45.0°
```

---

## 📜 License

MIT — Use freely with credit.

---

## 🙌 Acknowledgments

Built on top of:
- ODAS by Emanuël Habets
- ESP32 Arduino Core
- Servo library + WiFi UDP
