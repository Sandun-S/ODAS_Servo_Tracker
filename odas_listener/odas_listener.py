import socket
import json
import math
import select
import time
import threading

# === Configuration ===
ESP32_IP = '192.168.137.209'
ESP32_PORT = 4210
UDP_PORTS = [9900, 9901]
BUFFER_SIZE = 4096

# === Parameters ===
ENERGY_THRESHOLD = 0.500
ACTIVITY_THRESHOLD = 0.0
grace_period_sec = 0
SEND_INTERVAL = 0.01  # seconds

# === Shared Runtime State ===
state = {
    "last_strong_time": 0,
    "locked_tracking_id": None,
    "az": 0.0,
    "el": 0.0,
    "potential_sources": [],
    "tracking_sources": [],
    "lock": threading.Lock()
}

# === UDP Sockets ===
sockets = []
for port in UDP_PORTS:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', port))
    sockets.append(sock)
esp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print(f"📡 Listening on UDP ports {UDP_PORTS}...")

def direction_to_angles(x, y, z):
    # azimuth = (math.degrees(math.atan2(x, y)) + 360) % 360
    # y = -y  # Invert Y-axis to match hardware direction
    azimuth = (math.degrees(math.atan2(x, -y)) + 360) % 360
    elevation = math.degrees(math.asin(z))
    return azimuth, elevation

def find_best_matching_id(potential_list, tracking_list):
    best_pot = max(potential_list, key=lambda s: s.get("E", 0))
    E = best_pot.get("E", 0)
    if E > ENERGY_THRESHOLD:
        for track in tracking_list:
            dx = best_pot['x'] - track['x']
            dy = best_pot['y'] - track['y']
            dz = best_pot['z'] - track['z']
            dist = math.sqrt(dx**2 + dy**2 + dz**2)
            if dist < 0.15 and track.get("activity", 0) > ACTIVITY_THRESHOLD:
                return track.get("id"), best_pot
    return None, best_pot

def process_tracking_data():
    current_time = time.time()
    with state["lock"]:
        locked_id = state["locked_tracking_id"]
        tracks = state["tracking_sources"]
        pots = state["potential_sources"]

        if not pots or not tracks:
            return

        # Always find the best potential source
        new_id, best_pot = find_best_matching_id(pots, tracks)
        best_E = best_pot.get("E", 0)

        # If there's a locked ID, compare its energy with the new best one
        if locked_id is not None:
            current_match = next((s for s in tracks if s.get("id") == locked_id), None)
            if current_match and current_match.get("activity", 0) > ACTIVITY_THRESHOLD:
                current_az, current_el = direction_to_angles(current_match["x"], current_match["y"], current_match["z"])
                current_E = next((s.get("E", 0) for s in pots if abs(s['x'] - current_match['x']) < 0.01 and abs(s['y'] - current_match['y']) < 0.01), 0)

                # Only switch if new source is significantly stronger (e.g., +20% more E)
                if best_E > current_E * 1.2:
                    state["locked_tracking_id"] = new_id
                    state["az"], state["el"] = direction_to_angles(best_pot["x"], best_pot["y"], best_pot["z"])
                    state["last_strong_time"] = current_time
                    print(f"🔁 Switched to stronger source ID {new_id} - Az: {state['az']:.1f}°, El: {state['el']:.1f}°")
                    return
                else:
                    state["az"], state["el"] = current_az, current_el
                    state["last_strong_time"] = current_time
                    print(f"🔒 Continue Tracking ID {locked_id} - Az: {current_az:.1f}°, El: {current_el:.1f}°")
                    return

        # If no lock or we lost the lock
        if new_id is not None:
            az, el = direction_to_angles(best_pot["x"], best_pot["y"], best_pot["z"])
            state["locked_tracking_id"] = new_id
            state["last_strong_time"] = current_time
            state["az"], state["el"] = az, el
            print(f"🔐 New Lock ID {new_id} - Az: {az:.1f}°, El: {el:.1f}°")



def listener_task():
    while True:
        readable, _, _ = select.select(sockets, [], [])
        for sock in readable:
            data, _ = sock.recvfrom(BUFFER_SIZE)
            try:
                msg = json.loads(data.decode())
                if "src" not in msg or not msg["src"]:
                    continue
                port = sock.getsockname()[1]
                with state["lock"]:
                    if port == 9901:
                        state["potential_sources"] = msg["src"]
                    elif port == 9900:
                        state["tracking_sources"] = msg["src"]
                process_tracking_data()
            except Exception as e:
                print("⚠️ Error:", e)

def sender_task():
    while True:
        time.sleep(SEND_INTERVAL)
        with state["lock"]:
            command = f"AZ {state['az']:.1f} EL {state['el']:.1f}\n"
            esp_sock.sendto(command.encode(), (ESP32_IP, ESP32_PORT))

# === Start Threads ===
threading.Thread(target=listener_task, daemon=True).start()
threading.Thread(target=sender_task, daemon=True).start()

# Keep main thread alive
while True:
    time.sleep(1)