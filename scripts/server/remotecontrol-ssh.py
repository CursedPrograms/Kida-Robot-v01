import motorcontrol

print("🛰️ KIDA Remote SSH Control Online.")
print("Controls:")
print("  w / up       → Forward")
print("  s / down     → Backward")
print("  a / left     → Left")
print("  d / right    → Right")
print("  x / stop     → Stop")
print("  q / exit     → Quit program")

try:
    while True:
        cmd = input("Command > ").strip().lower()

        if cmd in ["w", "up", "forward"]:
            motorcontrol.forward()
        elif cmd in ["s", "down", "back", "backward"]:
            motorcontrol.backward()
        elif cmd in ["a", "left"]:
            motorcontrol.left_slow()
        elif cmd in ["d", "right"]:
            motorcontrol.right_slow()
        elif cmd in ["x", "stop"]:
            motorcontrol.stop()
        elif cmd in ["q", "exit", "quit"]:
            print("🛑 Shutting down KIDA...")
            motorcontrol.stop()
            break
        else:
            print("❓ Unknown command. Try w/a/s/d, up/down/left/right, x to stop, q to quit.")

except KeyboardInterrupt:
    print("\n💥 Interrupted. Stopping motors...")
    motorcontrol.stop()