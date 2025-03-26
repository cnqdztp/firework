import cv2
import numpy as np
import time
from flask import Flask, jsonify
from flask_cors import CORS
import threading
import configparser
import os
import sys

# Read configuration
config = configparser.ConfigParser()
config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')

if not os.path.exists(config_file):
    print(f"Error: Configuration file not found: {config_file}")
    print("Please run calibrate_tank_area.py first to set up your fish tank area.")
    sys.exit(1)

try:
    config.read(config_file)
    
    # Camera settings
    CAMERA_INDEX = config.getint('Camera', 'camera_index')
    CAMERA_WIDTH = config.getint('Camera', 'width')
    CAMERA_HEIGHT = config.getint('Camera', 'height')
    
    # Detection settings
    MIN_CONTOUR_AREA = config.getint('Detection', 'min_contour_area')
    MAX_CONTOUR_AREA = config.getint('Detection', 'max_contour_area')
    H_LOW1 = config.getint('Detection', 'h_low1')
    H_HIGH1 = config.getint('Detection', 'h_high1')
    H_LOW2 = config.getint('Detection', 'h_low2')
    H_HIGH2 = config.getint('Detection', 'h_high2')
    S_LOW = config.getint('Detection', 's_low')
    S_HIGH = config.getint('Detection', 's_high')
    V_LOW = config.getint('Detection', 'v_low')
    V_HIGH = config.getint('Detection', 'v_high')
    BLUR_SIZE = config.getint('Detection', 'blur_size')
    ERODE_ITERATIONS = config.getint('Detection', 'erode_iterations')
    DILATE_ITERATIONS = config.getint('Detection', 'dilate_iterations')
    
    # Tank area settings
    if 'TankArea' in config:
        TANK_AREA = [
            (config.getint('TankArea', 'top_left_x'), config.getint('TankArea', 'top_left_y')),
            (config.getint('TankArea', 'top_right_x'), config.getint('TankArea', 'top_right_y')),
            (config.getint('TankArea', 'bottom_right_x'), config.getint('TankArea', 'bottom_right_y')),
            (config.getint('TankArea', 'bottom_left_x'), config.getint('TankArea', 'bottom_left_y'))
        ]
        TANK_AREA_DEFINED = all(p != (0, 0) for p in TANK_AREA[1:])
    else:
        # Default to full frame if not defined
        TANK_AREA = [(0, 0), (CAMERA_WIDTH, 0), (CAMERA_WIDTH, CAMERA_HEIGHT), (0, CAMERA_HEIGHT)]
        TANK_AREA_DEFINED = False
    
    # Server settings
    SERVER_PORT = config.getint('Server', 'port')
    
    print(f"Configuration loaded from {config_file}")
    print(f"Using camera index: {CAMERA_INDEX}")
    
    if TANK_AREA_DEFINED:
        print("Fish tank area loaded from calibration.")
    else:
        print("No fish tank area defined. Will use full camera view.")
    
except Exception as e:
    print(f"Error reading configuration: {e}")
    print("Using default settings")
    
    # Default settings if config file can't be read
    CAMERA_INDEX = 0
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    MIN_CONTOUR_AREA = 300
    MAX_CONTOUR_AREA = 10000
    H_LOW1 = 0
    H_HIGH1 = 10
    H_LOW2 = 160
    H_HIGH2 = 180
    S_LOW = 100
    S_HIGH = 255
    V_LOW = 100
    V_HIGH = 255
    BLUR_SIZE = 7
    ERODE_ITERATIONS = 1
    DILATE_ITERATIONS = 2
    SERVER_PORT = 5000
    TANK_AREA = [(0, 0), (CAMERA_WIDTH, 0), (CAMERA_WIDTH, CAMERA_HEIGHT), (0, CAMERA_HEIGHT)]
    TANK_AREA_DEFINED = False

# Setup perspective transformation if tank area is defined
def setup_perspective_transform():
    if not TANK_AREA_DEFINED:
        return None
    
    # Calculate width and height for the corrected view
    width = int(max(
        np.sqrt((TANK_AREA[1][0] - TANK_AREA[0][0])**2 + (TANK_AREA[1][1] - TANK_AREA[0][1])**2),
        np.sqrt((TANK_AREA[2][0] - TANK_AREA[3][0])**2 + (TANK_AREA[2][1] - TANK_AREA[3][1])**2)
    ))
    
    height = int(max(
        np.sqrt((TANK_AREA[3][0] - TANK_AREA[0][0])**2 + (TANK_AREA[3][1] - TANK_AREA[0][1])**2),
        np.sqrt((TANK_AREA[2][0] - TANK_AREA[1][0])**2 + (TANK_AREA[2][1] - TANK_AREA[1][1])**2)
    ))
    
    # Define destination points (perspective corrected)
    dst_pts = np.array([
        [0, 0],
        [width, 0],
        [width, height],
        [0, height]
    ], dtype=np.float32)
    
    # Source points (from calibration)
    src_pts = np.array(TANK_AREA, dtype=np.float32)
    
    # Calculate transformation matrix
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    
    return {
        'matrix': M,
        'width': width,
        'height': height,
        'points': TANK_AREA
    }

# Apply mask to restrict detection to tank area only
def apply_tank_area_mask(frame):
    if not TANK_AREA_DEFINED:
        return frame
    
    # Create a mask of the tank area
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    points = np.array(TANK_AREA, dtype=np.int32).reshape((-1, 1, 2))
    cv2.fillPoly(mask, [points], 255)
    
    # Apply mask to frame
    return cv2.bitwise_and(frame, frame, mask=mask)

# Initialize Flask app for communication
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
fish_position = {"x": 0.5, "y": 0.5}  # Default position (center)
last_valid_position = {"x": 0.5, "y": 0.5}  # Keep track of last valid detection
position_history = []  # Track recent positions for smoothing

# Create a thread for the Flask server
def run_server():
    app.run(host='0.0.0.0', port=SERVER_PORT)


@app.route('/position')
def get_position():
    return jsonify(fish_position)

# Start the server in a separate thread
server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

# Initialize camera
print(f"Attempting to open camera with index {CAMERA_INDEX}...")
cap = cv2.VideoCapture(CAMERA_INDEX)

# Check if camera opened successfully
if not cap.isOpened():
    print(f"Error: Could not open camera with index {CAMERA_INDEX}.")
    print("Available camera indices might be different. Try updating the 'camera_index' in config.ini.")
    sys.exit(1)

# Set camera resolution to optimize performance
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

# Initialize background subtractor for motion detection
bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=25, detectShadows=False)

# Parameters for red fish detection (red appears at both ends of the hue spectrum in HSV)
lower_red1 = np.array([H_LOW1, S_LOW, V_LOW])
upper_red1 = np.array([H_HIGH1, S_HIGH, V_HIGH])
lower_red2 = np.array([H_LOW2, S_LOW, V_LOW])
upper_red2 = np.array([H_HIGH2, S_HIGH, V_HIGH])

# Ensure blur size is odd
if BLUR_SIZE % 2 == 0:
    BLUR_SIZE += 1

detect_confidence = 0  # Counter to track consecutive detections

# Set up perspective transformation
perspective_transform = setup_perspective_transform()
if perspective_transform:
    print(f"Perspective transformation set up with dimensions {perspective_transform['width']}x{perspective_transform['height']}")

print(f"Red fish tracking started using camera {CAMERA_INDEX}. Press 'q' to quit.")
print(f"Red detection ranges: H({H_LOW1}-{H_HIGH1} and {H_LOW2}-{H_HIGH2}), S({S_LOW}-{S_HIGH}), V({V_LOW}-{V_HIGH})")
print(f"Contour area limits: {MIN_CONTOUR_AREA} - {MAX_CONTOUR_AREA}")
print(f"Server running on port {SERVER_PORT}")

# Function to check if a detection is valid (not a sudden jump)
def is_valid_detection(x, y, prev_x, prev_y, threshold=0.2):
    # Calculate normalized distance
    distance = np.sqrt((x - prev_x)**2 + (y - prev_y)**2)
    return distance < threshold

# Function to get smooth position based on recent history
def get_smooth_position(positions, current_pos):
    # Add current position to history
    positions.append(current_pos.copy())
    
    # Keep only the last 5 positions
    if len(positions) > 5:
        positions.pop(0)
    
    # Calculate weighted average (more recent positions have higher weight)
    weights = np.linspace(0.5, 1.0, len(positions))
    x_avg = sum(p["x"] * w for p, w in zip(positions, weights)) / sum(weights)
    y_avg = sum(p["y"] * w for p, w in zip(positions, weights)) / sum(weights)
    
    return {"x": x_avg, "y": y_avg}

# Allow background subtractor to learn the background
print("Learning background... Please wait.")
for i in range(30):
    ret, frame = cap.read()
    if ret:
        # Apply tank area mask
        masked_frame = apply_tank_area_mask(frame)
        bg_subtractor.apply(masked_frame)
        time.sleep(0.05)

# Main processing loop
while True:
    # Capture frame
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture image")
        break
    
    # Apply mask to restrict detection to tank area
    masked_frame = apply_tank_area_mask(frame)
    
    # Apply background subtraction to isolate moving objects
    fg_mask = bg_subtractor.apply(masked_frame)
    
    # Convert to HSV for better color filtering
    hsv = cv2.cvtColor(masked_frame, cv2.COLOR_BGR2HSV)
    
    # Create mask for red color (combining both red ranges)
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(mask1, mask2)
    
    # Combine with foreground mask to get only moving red objects
    # We use a reduced weight for the foreground mask to not be too strict
    combined_mask = cv2.bitwise_and(red_mask, fg_mask)
    
    # Apply morphological operations to remove noise
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.GaussianBlur(combined_mask, (BLUR_SIZE, BLUR_SIZE), 0)
    mask = cv2.erode(mask, kernel, iterations=ERODE_ITERATIONS)
    mask = cv2.dilate(mask, kernel, iterations=DILATE_ITERATIONS)
    
    # Find contours in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Create debug visualization
    debug_view = frame.copy()
    
    # Add tank area boundary to debug view
    if TANK_AREA_DEFINED:
        # Draw the tank area boundary
        pts = np.array(TANK_AREA, np.int32).reshape((-1, 1, 2))
        cv2.polylines(debug_view, [pts], True, (0, 255, 255), 2)
    
    # Add mask visualization to debug view (red overlay)
    mask_overlay = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    mask_overlay[:,:,0] = 0  # Set blue channel to 0
    mask_overlay[:,:,1] = 0  # Set green channel to 0
    
    # Apply mask overlay only in tank area
    if TANK_AREA_DEFINED:
        tank_mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        pts = np.array(TANK_AREA, np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(tank_mask, [pts], 255)
        mask_overlay_region = cv2.bitwise_and(mask_overlay, mask_overlay, mask=tank_mask)
        debug_view = cv2.addWeighted(debug_view, 1.0, mask_overlay_region, 0.5, 0)
    else:
        debug_view = cv2.addWeighted(debug_view, 1.0, mask_overlay, 0.5, 0)
    
    fish_detected = False
    
    # If perspective correction is available, create a corrected view
    if perspective_transform and TANK_AREA_DEFINED:
        corrected_view = cv2.warpPerspective(frame, perspective_transform['matrix'], 
                                             (perspective_transform['width'], perspective_transform['height']))
    
    # Process contours to find the fish
    if contours:
        # Find the largest contour that meets our size criteria
        valid_contours = [c for c in contours if MIN_CONTOUR_AREA < cv2.contourArea(c) < MAX_CONTOUR_AREA]
        
        if valid_contours:
            # Get the largest valid contour
            fish_contour = max(valid_contours, key=cv2.contourArea)
            
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(fish_contour)
            
            # Calculate center of the fish
            fish_center_x = x + w//2
            fish_center_y = y + h//2
            
            # Convert to normalized coordinates (0-1 range)
            if perspective_transform and TANK_AREA_DEFINED:
                # Transform point to corrected view space
                pts = np.array([[fish_center_x, fish_center_y]], dtype=np.float32)
                pts = pts.reshape(-1, 1, 2)
                transformed_pts = cv2.perspectiveTransform(pts, perspective_transform['matrix'])
                transformed_x = transformed_pts[0][0][0]
                transformed_y = transformed_pts[0][0][1]
                
                # Normalize using the transformed view dimensions
                norm_x = transformed_x / perspective_transform['width']
                norm_y = transformed_y / perspective_transform['height']
            else:
                # If no perspective correction, just use the original frame dimensions
                norm_x = fish_center_x / frame.shape[1]
                norm_y = fish_center_y / frame.shape[0]
            
            # Check if detection is valid (not a sudden jump)
            if is_valid_detection(norm_x, norm_y, last_valid_position["x"], last_valid_position["y"]) or detect_confidence > 3:
                # Update last valid position
                last_valid_position["x"] = norm_x
                last_valid_position["y"] = norm_y
                
                # Get smoothed position
                smooth_position = get_smooth_position(position_history, last_valid_position)
                
                # Update global fish position with the smoothed values
                fish_position["x"] = smooth_position["x"]
                fish_position["y"] = smooth_position["y"]
                
                # Mark as detected and increase confidence
                fish_detected = True
                detect_confidence = min(detect_confidence + 1, 10)
                
                # Draw rectangle around the fish
                cv2.rectangle(debug_view, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.circle(debug_view, (fish_center_x, fish_center_y), 5, (0, 0, 255), -1)
                cv2.putText(debug_view, f"Fish: {fish_position['x']:.2f}, {fish_position['y']:.2f}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                # Draw rectangle with different color to show invalid detection
                cv2.rectangle(debug_view, (x, y), (x+w, y+h), (0, 165, 255), 2)
                cv2.putText(debug_view, "Invalid detection", (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)
    
    # If fish not detected, decrease confidence
    if not fish_detected:
        detect_confidence = max(detect_confidence - 1, 0)
        cv2.putText(debug_view, f"No detection (conf: {detect_confidence})", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    # Add camera index information to the debug view
    cv2.putText(debug_view, f"Camera: {CAMERA_INDEX}", (frame.shape[1]-150, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Display the debug view
    cv2.imshow('Red Fish Tracker', debug_view)
    
    # If we have a corrected view, display that too (resized for visibility)
    if perspective_transform and TANK_AREA_DEFINED:
        # Resize if too big
        h, w = corrected_view.shape[:2]
        max_height = 300
        if h > max_height:
            ratio = max_height / h
            corrected_view = cv2.resize(corrected_view, (int(w * ratio), max_height))
        
        cv2.imshow('Corrected Tank View', corrected_view)
    
    # Break the loop with 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
    # Add a small delay to reduce CPU usage
    time.sleep(0.01)

# Release resources
cap.release()
cv2.destroyAllWindows()
print("Fish tracking stopped.")