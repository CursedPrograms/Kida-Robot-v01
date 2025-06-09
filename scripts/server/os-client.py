# client.py
import socket, pickle, threading
import tkinter as tk
from PIL import Image, ImageTk
import io

def send_event(sock, event):
    sock.sendall(pickle.dumps(event))

def listen_for_screen(sock, label):
    while True:
        try:
            data = b''
            while True:
                packet = sock.recv(4096)
                if not packet:
                    return
                data += packet
                try:
                    img_data = pickle.loads(data)
                    break
                except:
                    continue
            image = Image.open(io.BytesIO(img_data))
            photo = ImageTk.PhotoImage(image)
            label.config(image=photo)
            label.image = photo
        except:
            break

def on_click(event, sock):
    send_event(sock, {'type': 'click'})

def on_move(event, sock):
    send_event(sock, {'type': 'move', 'x': event.x, 'y': event.y})

def on_key(event, sock):
    send_event(sock, {'type': 'key', 'key': event.char})

def main():
    sock = socket.socket()
    sock.connect(('YOUR_PI_IP', 9999))

    root = tk.Tk()
    label = tk.Label(root)
    label.pack()

    label.bind("<Button-1>", lambda e: on_click(e, sock))
    label.bind("<Motion>", lambda e: on_move(e, sock))
    root.bind("<Key>", lambda e: on_key(e, sock))

    threading.Thread(target=listen_for_screen, args=(sock, label), daemon=True).start()
    root.mainloop()

main()
