import serial
import time
import threading
import config
import state

# -----------------------------
# Global Arduino connections
# -----------------------------
arduinos = {}

# -----------------------------
# Connect to Arduino
# -----------------------------
def connect_arduino(dev_name, port, baud):
    try:
        ser = serial.Serial(port, baud, timeout=1)
        time.sleep(2)  # Allow Arduino to reset
        arduinos[dev_name] = ser
        print(f"✅ Connected {dev_name} on {port}")
        return ser
    except serial.SerialException as e:
        print(f"❌ Could not connect {dev_name} on {port}: {e}")
        return None

# -----------------------------
# Update dev01 sensors
# -----------------------------
def update_state_dev01(line, dev_name="dev01"):
    line = line.strip()
    if line.startswith("MOTION:"):
        try:
            parts = [p.strip() for p in line.split("|")]
            for part in parts:
                if part.startswith("MOTION:"):
                    state.motionValue = f"MOTION: {part.split(':')[1]}"
                elif part.startswith("PHOTO:"):
                    state.photoValue = f"PHOTO: {part.split(':')[1]}"
                elif part.startswith("UV:"):
                    state.uvValue = f"UV: {part.split(':')[1]}"
                elif part.startswith("METAL:"):
                    state.metalValue = f"METAL: {part.split(':')[1]}"
                elif part.startswith("BALL:"):
                    state.ballSwitchValue = f"BALL: {part.split(':')[1]}"
                elif part.startswith("LF["):
                    inside = part.split("[", 1)[1].rstrip("]")
                    vals = {kv.split(":")[0]: kv.split(":")[1] for kv in inside.split()}
                    state.lfLeftValue = f"LF_LEFT: {vals.get('L', 'N/A')}"
                    state.lfMidValue = f"LF_MID: {vals.get('M', 'N/A')}"
                    state.lfRightValue = f"LF_RIGHT: {vals.get('R', 'N/A')}"
            print(f"📊 {dev_name} updated sensors: "
                  f"{state.motionValue}, {state.photoValue}, {state.uvValue}, "
                  f"{state.metalValue}, {state.ballSwitchValue}, "
                  f"{state.lfLeftValue}/{state.lfMidValue}/{state.lfRightValue}")
        except Exception as e:
            print(f"⚠️ {dev_name} parse error: {e} | line={line}")
    elif "Motion detected" in line:
        state.systemStatus = "⚠️ Motion detected!"
        print(f"👀 {dev_name} ALERT: {line}")
    elif "METAL DETECTED" in line:
        state.systemStatus = "⚡ METAL DETECTED!"
        print(f"🧲 {dev_name} ALERT: {line}")
    elif "Ball switch triggered" in line:
        state.systemStatus = "🏀 Ball switch triggered!"
        print(f"🔘 {dev_name} ALERT: {line}")
    else:
        print(f"⚠️ {dev_name} Unknown serial data: {line}")

# -----------------------------
# Update dev00 sensors
# -----------------------------
def update_state_dev00(line, dev_name="dev00"):
    line = line.strip()
    if line.startswith("LASER:") or line.startswith("ULTRASONIC:") \
        or line.startswith("SERVO:") or line.startswith("BUTTON:") \
        or line.startswith("SPEED:"):
        update_state(line, dev_name)
    else:
        print(f"⚠️ {dev_name} Unknown serial data: {line}")

# -----------------------------
# Generic single-line state updater
# -----------------------------
# -----------------------------
# Generic single-line state updater
# -----------------------------
def update_state(line, dev_name="dev0"):
    line = line.strip()
    try:
        if line.startswith("LASER:"):
            val_str = line.split(":", 1)[1]
            state.laserValue = f"LASER: {val_str.strip()}"
        elif line.startswith("ULTRASONIC0:"):
            val_str = line.split(":", 1)[1]
            state.ultrasonic0Value = f"ULTRASONIC0: {val_str.strip()}"
        elif line.startswith("ULTRASONIC1:"):
            val_str = line.split(":", 1)[1]
            state.ultrasonic1Value = f"ULTRASONIC1: {val_str.strip()}"
        elif line.startswith("SERVO:"):
            val_str = line.split(":", 1)[1]
            state.servoPosValue = f"SERVO: {val_str.strip()}"
        elif line.startswith("BUTTON:"):
            val_str = line.split(":", 1)[1]
            state.buttonValue = f"BUTTON: {val_str.strip()}"
        elif line.startswith("SPEED:"):
            val_str = line.split(":", 1)[1]
            state.motorSpeedValue = f"SPEED: {val_str.strip()}"
    except Exception as e:
        print(f"⚠️ {dev_name} failed to parse line: {line} | {e}")

# -----------------------------
# Arduino reading thread
# -----------------------------
def read_from_arduino(dev_name):
    ser = arduinos.get(dev_name)
    if not ser:
        print(f"❌ {dev_name} not connected")
        return
    while True:
        try:
            line = ser.readline().decode("utf-8").strip()
            if line:
                if dev_name == "dev01":
                    update_state_dev01(line, dev_name)
                elif dev_name == "dev00":
                    update_state_dev00(line, dev_name)
                else:
                    update_state(line, dev_name)
        except Exception as e:
            print(f"⚠️ Error reading from {dev_name}: {e}")
            time.sleep(0.5)

# -----------------------------
# Start all Arduino threads
# -----------------------------
def start_arduino_threads():
    ports = {
        "dev00": "/dev/ttyUSB0",  # Update with correct port
        "dev01": "/dev/ttyUSB1",  # Update with correct port
    }
    for dev_name, port in ports.items():
        ser = connect_arduino(dev_name, port, config.ARDUINO_BAUD)
        if ser:
            t = threading.Thread(target=read_from_arduino, args=(dev_name,), daemon=True)
            t.start()
            print(f"🔄 Started thread for {dev_name}")

def send_command(dev_name, command):
    """
    Send a string command to an Arduino device.
    Example: send_command("dev00", "FORWARD")
    """
    ser = arduinos.get(dev_name)
    if ser and ser.is_open:
        try:
            ser.write((command + "\n").encode('utf-8'))
            print(f"➡️ Sent to {dev_name}: {command}")
        except Exception as e:
            print(f"⚠️ Failed to send command to {dev_name}: {e}")
    else:
        print(f"❌ {dev_name} not connected or closed")


# -----------------------------
# Close all connections
# -----------------------------
def close_all_arduinos():
    for dev_name, ser in arduinos.items():
        try:
            ser.close()
            print(f"🔒 Closed connection to {dev_name}")
        except Exception as e:
            print(f"⚠️ Error closing {dev_name}: {e}")
