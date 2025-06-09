# server.py
import socket, threading, pickle
from mss import mss
from PIL import Image
import pyautogui
import io

def capture_screen():
    with mss() as sct:
        screenshot = sct.grab(sct.monitors[0])
        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        return buffer.getvalue()

def handle_events(conn):
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break
            event = pickle.loads(data)
            if event['type'] == 'move':
                pyautogui.moveTo(event['x'], event['y'])
            elif event['type'] == 'click':
                pyautogui.click()
            elif event['type'] == 'key':
                pyautogui.write(event['key'])
        except:
            break

def main():
    s = socket.socket()
    s.bind(('0.0.0.0', 9999))
    s.listen(1)
    print("Waiting for connection...")
    conn, _ = s.accept()
    threading.Thread(target=handle_events, args=(conn,), daemon=True).start()
    while True:
        try:
            img_data = capture_screen()
            conn.sendall(pickle.dumps(img_data))
        except:
            break
    conn.close()

main()
