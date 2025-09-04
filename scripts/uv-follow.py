import time
from arduino import send_command
import state  # assuming this module updates dev0_uvValue continuously

def uv_follow_loop(poll_interval=0.2):
    last_command = None
    while True:
        try:
            uv_value = int(getattr(state, "dev0_uvValue", 0))
        except Exception:
            uv_value = 0

        if uv_value > 100:
            command = "FORWARD"
        else:
            command = "STOP"

        if command != last_command:
            print(f"UV={uv_value}, sending command: {command}")
            send_command("dev0", command)
            last_command = command

        time.sleep(poll_interval)


if __name__ == "__main__":
    try:
        uv_follow_loop()
    except KeyboardInterrupt:
        print("UV follow stopped by user")
