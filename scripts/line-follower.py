# line_follower.py
import state
from arduino import send_command
import time
import logging

# Configuration
LOOP_DELAY = 0.05               # 50ms loop delay
LINE_THRESHOLD = 500            # Adjust based on your sensor calibration
TURN_SPEED_MULTIPLIER = 0.8     # Reduce speed when turning
SEARCH_TIMEOUT = 3.0            # Seconds to search for line before stopping
MAX_SEARCH_TURNS = 6            # Maximum number of search attempts

# Line following state
last_line_position = "CENTER"   # Track where we last saw the line
line_lost_time = None
search_turn_count = 0
search_direction = "RIGHT"      # Start searching right when line is lost

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_line_sensors():
    """
    Read line follower sensor values from state.py
    Returns tuple of (left, middle, right) sensor values
    Returns None for any sensor that's not working
    """
    def parse_sensor(value):
        if value is None:
            return None
        try:
            # Handle both "Sensor: 500" format and direct numeric values
            if isinstance(value, str) and ": " in value:
                return int(value.split(": ")[1])
            elif isinstance(value, (int, float)):
                return int(value)
            else:
                return int(str(value))
        except (ValueError, IndexError, AttributeError):
            return None

    left = parse_sensor(getattr(state, 'lfLeftValue', None))
    middle = parse_sensor(getattr(state, 'lfMidValue', None))
    right = parse_sensor(getattr(state, 'lfRightValue', None))

    return left, middle, right

def detect_line_position(left, middle, right):
    """
    Determine line position based on sensor readings.
    Returns position string and confidence level.
    
    Assumes sensors return higher values when over the line (bright surface)
    Adjust logic if your sensors work inversely (lower values on line)
    """
    # Convert to boolean line detection (True = line detected)
    left_on_line = left is not None and left > LINE_THRESHOLD
    middle_on_line = middle is not None and middle > LINE_THRESHOLD
    right_on_line = right is not None and right > LINE_THRESHOLD

    # Pattern matching for line position
    if middle_on_line:
        if left_on_line and right_on_line:
            return "CENTER_WIDE", 95    # All sensors on line (wide line or intersection)
        elif left_on_line:
            return "SLIGHT_LEFT", 85    # Line slightly to the left
        elif right_on_line:
            return "SLIGHT_RIGHT", 85   # Line slightly to the right
        else:
            return "CENTER", 90         # Only middle sensor on line
    
    elif left_on_line and not right_on_line:
        return "LEFT", 80               # Line to the left
    
    elif right_on_line and not left_on_line:
        return "RIGHT", 80              # Line to the right
    
    elif left_on_line and right_on_line:
        return "GAP", 70                # Possible gap in line or very wide line
    
    else:
        return "LOST", 0                # No line detected

def calculate_line_following_command(position, confidence):
    """
    Calculate the appropriate movement command based on line position.
    """
    global last_line_position
    
    if confidence == 0:  # Line lost
        return handle_line_lost()
    
    # Update last known position for line recovery
    if confidence > 70:
        last_line_position = position
    
    # Command mapping based on line position
    command_map = {
        "CENTER": "FORWARD",
        "CENTER_WIDE": "FORWARD",
        "SLIGHT_LEFT": "SLIGHT_LEFT",
        "SLIGHT_RIGHT": "SLIGHT_RIGHT", 
        "LEFT": "LEFT",
        "RIGHT": "RIGHT",
        "GAP": "FORWARD"  # Continue forward through gaps
    }
    
    return command_map.get(position, "STOP")

def handle_line_lost():
    """
    Handle line recovery when the line is lost.
    Implements a search pattern to relocate the line.
    """
    global line_lost_time, search_turn_count, search_direction
    
    current_time = time.time()
    
    # Initialize line lost tracking
    if line_lost_time is None:
        line_lost_time = current_time
        search_turn_count = 0
        logger.warning("Line lost! Starting search pattern...")
    
    elapsed = current_time - line_lost_time
    
    # Check if we've been searching too long
    if elapsed > SEARCH_TIMEOUT or search_turn_count >= MAX_SEARCH_TURNS:
        logger.error("Line search timeout - stopping robot")
        return "STOP"
    
    # Search pattern: alternate left and right turns
    if search_turn_count % 2 == 0:
        command = "RIGHT" if search_direction == "RIGHT" else "LEFT"
    else:
        # Reverse direction for next search
        command = "LEFT" if search_direction == "RIGHT" else "RIGHT"
        search_direction = "LEFT" if search_direction == "RIGHT" else "RIGHT"
    
    search_turn_count += 1
    logger.info(f"Searching for line: {command} (attempt {search_turn_count})")
    
    return command

def reset_line_lost_state():
    """Reset the line lost tracking when line is found again."""
    global line_lost_time, search_turn_count
    line_lost_time = None
    search_turn_count = 0

def line_follower_step():
    """
    Single step of line following logic.
    """
    left, middle, right = read_line_sensors()
    
    # Detect line position
    position, confidence = detect_line_position(left, middle, right)
    
    # Reset line lost state if we found the line again
    if confidence > 70:
        reset_line_lost_state()
    
    # Calculate movement command
    command = calculate_line_following_command(position, confidence)
    
    # Send command to Arduino
    send_command(command)
    
    # Update system status
    sensor_status = []
    if left is not None:
        sensor_status.append(f"L={left}")
    if middle is not None:
        sensor_status.append(f"M={middle}")
    if right is not None:
        sensor_status.append(f"R={right}")
    
    status = f"LineFollower: {command} | Position: {position}({confidence}%) | Sensors: {', '.join(sensor_status)}"
    
    if line_lost_time is not None:
        elapsed = time.time() - line_lost_time
        status += f" | Searching: {elapsed:.1f}s"
    
    state.systemStatus = status
    print(status)

def run_line_follower():
    """
    Continuous loop for line following with error handling.
    """
    logger.info("Starting line follower system...")
    
    try:
        while True:
            try:
                line_follower_step()
                time.sleep(LOOP_DELAY)
            except Exception as e:
                logger.error(f"Error in line follower step: {e}")
                send_command("STOP")  # Safety stop on error
                time.sleep(0.1)  # Brief pause before retrying
                
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
    except Exception as e:
        logger.error(f"Fatal error in line follower: {e}")
    finally:
        send_command("STOP")
        state.systemStatus = "LineFollower: STOPPED"
        logger.info("Line follower stopped safely.")

def calibrate_sensors():
    """
    Utility function to help calibrate line sensor thresholds.
    Run this to see sensor values on different surfaces.
    """
    print("Line sensor calibration mode...")
    print("Place robot on different surfaces and observe values:")
    print("Press Ctrl+C to stop calibration")
    
    try:
        while True:
            left, middle, right = read_line_sensors()
            position, confidence = detect_line_position(left, middle, right)
            
            print(f"Sensors: L={left:4}, M={middle:4}, R={right:4} | "
                  f"Position: {position:12} ({confidence:2}%) | "
                  f"Threshold: {LINE_THRESHOLD}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nCalibration complete!")

def test_line_following():
    """
    Test function to run line following for a limited time.
    """
    print("Testing line following for 30 seconds...")
    start_time = time.time()
    
    try:
        while time.time() - start_time < 30:
            line_follower_step()
            time.sleep(LOOP_DELAY)
    except KeyboardInterrupt:
        pass
    finally:
        send_command("STOP")
        print("Line following test complete.")

# Advanced line following with PID-like behavior
class PIDLineFollower:
    """
    Advanced line follower with PID-like control for smoother following.
    """
    def __init__(self):
        self.last_error = 0
        self.integral = 0
        
        # PID constants (tune these for your robot)
        self.kp = 1.0    # Proportional gain
        self.ki = 0.1    # Integral gain  
        self.kd = 0.5    # Derivative gain
        
    def calculate_error(self, left, middle, right):
        """
        Calculate line position error.
        Returns error value: negative = line to left, positive = line to right
        """
        if left is None or middle is None or right is None:
            return None
            
        # Weight the sensors to calculate position error
        # This assumes higher values mean line detection
        left_weight = 1 if left > LINE_THRESHOLD else 0
        middle_weight = 1 if middle > LINE_THRESHOLD else 0
        right_weight = 1 if right > LINE_THRESHOLD else 0
        
        # Calculate weighted position (-1 to +1)
        if left_weight + middle_weight + right_weight == 0:
            return None  # No line detected
            
        position = (right_weight - left_weight) / max(1, left_weight + middle_weight + right_weight)
        return position * 100  # Scale for easier tuning
    
    def update(self, left, middle, right):
        """
        Update PID controller and return movement command.
        """
        error = self.calculate_error(left, middle, right)
        
        if error is None:
            return "SEARCH"  # No line detected
        
        # PID calculation
        self.integral += error
        derivative = error - self.last_error
        
        pid_output = (self.kp * error + 
                     self.ki * self.integral + 
                     self.kd * derivative)
        
        self.last_error = error
        
        # Convert PID output to movement commands
        if abs(pid_output) < 10:
            return "FORWARD"
        elif pid_output < -20:
            return "LEFT"
        elif pid_output < -10:
            return "SLIGHT_LEFT"
        elif pid_output > 20:
            return "RIGHT"
        elif pid_output > 10:
            return "SLIGHT_RIGHT"
        else:
            return "FORWARD"

# Create PID controller instance
pid_controller = PIDLineFollower()

def run_pid_line_follower():
    """
    Run the advanced PID-based line follower.
    """
    logger.info("Starting PID line follower...")
    
    try:
        while True:
            left, middle, right = read_line_sensors()
            command = pid_controller.update(left, middle, right)
            
            if command == "SEARCH":
                command = handle_line_lost()
            else:
                reset_line_lost_state()
            
            send_command(command)
            
            # Status update
            error = pid_controller.calculate_error(left, middle, right)
            status = f"PID_LineFollower: {command} | Error: {error:.1f} | L={left}, M={middle}, R={right}"
            state.systemStatus = status
            print(status)
            
            time.sleep(LOOP_DELAY)
            
    except KeyboardInterrupt:
        send_command("STOP")
        logger.info("PID line follower stopped safely.")

if __name__ == "__main__":
    # Choose which line follower to run
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "calibrate":
            calibrate_sensors()
        elif mode == "test":
            test_line_following()
        elif mode == "pid":
            run_pid_line_follower()
        else:
            print("Usage: python line_follower.py [calibrate|test|pid]")
    else:
        # Default: run basic line follower
        run_line_follower()