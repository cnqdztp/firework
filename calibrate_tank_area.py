import cv2
import numpy as np
import json
import os
import configparser
import sys

# Global variables
points = []  # To store the 4 corner points
current_point = 0  # Current point being selected
drawing = False  # Flag for drawing reference lines
frame_copy = None  # Copy of the current frame for drawing
tank_area_defined = False  # Flag to check if tank area is defined

# Read configuration
config = configparser.ConfigParser()
config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')

if not os.path.exists(config_file):
    print("⚠️ Settings file not found. Creating a new one.")
    # Create default config
    config['Camera'] = {}
    config['Camera']['camera_index'] = '0'
    config['Camera']['width'] = '640'
    config['Camera']['height'] = '480'
    
    config['Detection'] = {}
    config['Detection']['min_contour_area'] = '300'
    config['Detection']['max_contour_area'] = '10000'
    
    config['TankArea'] = {}
    config['TankArea']['top_left_x'] = '0'
    config['TankArea']['top_left_y'] = '0'
    config['TankArea']['top_right_x'] = '640'
    config['TankArea']['top_right_y'] = '0'
    config['TankArea']['bottom_right_x'] = '640'
    config['TankArea']['bottom_right_y'] = '480'
    config['TankArea']['bottom_left_x'] = '0'
    config['TankArea']['bottom_left_y'] = '480'
    
    with open(config_file, 'w') as f:
        config.write(f)
else:
    config.read(config_file)
    print("✓ Found settings file.")

# Get camera settings
try:
    CAMERA_INDEX = config.getint('Camera', 'camera_index')
    CAMERA_WIDTH = config.getint('Camera', 'width')
    CAMERA_HEIGHT = config.getint('Camera', 'height')
    
    # Try to load existing tank area points if they exist
    if 'TankArea' in config:
        points = [
            (config.getint('TankArea', 'top_left_x'), config.getint('TankArea', 'top_left_y')),
            (config.getint('TankArea', 'top_right_x'), config.getint('TankArea', 'top_right_y')),
            (config.getint('TankArea', 'bottom_right_x'), config.getint('TankArea', 'bottom_right_y')),
            (config.getint('TankArea', 'bottom_left_x'), config.getint('TankArea', 'bottom_left_y'))
        ]
        
        # Check if we have valid points (all 4 corners)
        if len(points) == 4 and all(p != (0, 0) for p in points[1:]):
            current_point = 4
            tank_area_defined = True
            print("✓ Loaded existing tank area calibration.")
        else:
            # Reset points if we don't have all 4 defined properly
            points = []
except Exception as e:
    print(f"⚠️ Error reading settings: {e}")
    CAMERA_INDEX = 0
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480

# Ask about camera
print("\n📹 Camera Selection")
print("-----------------")
print(f"Currently using camera #{CAMERA_INDEX}")
try:
    user_input = input("Want to try a different camera? Enter a number (or press Enter to keep current): ")
    if user_input.strip():
        CAMERA_INDEX = int(user_input)
        print(f"→ Switching to camera #{CAMERA_INDEX}")
except ValueError:
    print("→ Keeping current camera")

# Initialize camera
print(f"\nStarting camera #{CAMERA_INDEX}...")
cap = cv2.VideoCapture(CAMERA_INDEX)

if not cap.isOpened():
    print(f"❌ Camera #{CAMERA_INDEX} not found or can't be opened.")
    print("Tips:")
    print("- Make sure camera is connected")
    print("- Try a different camera number (usually 0 for built-in, 1 for external)")
    print("- Close other programs that might be using the camera")
    sys.exit(1)

print("✓ Camera working!")

# Set camera resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

# Create a named window
cv2.namedWindow('Fish Tank Calibration')

# Mouse callback function
def mouse_callback(event, x, y, flags, param):
    global points, current_point, drawing, frame_copy, tank_area_defined
    
    if event == cv2.EVENT_LBUTTONDOWN:
        if current_point < 4:
            points.append((x, y))
            current_point += 1
            
            # Redraw frame with the new point
            if frame_copy is not None:
                draw_points_and_lines()
            
            # Check if all 4 points are defined
            if current_point == 4:
                tank_area_defined = True
                print(f"✓ All four corners defined: {points}")
                
                # Show the preview
                draw_points_and_lines()
        else:
            # If 4 points already defined, allow repositioning by clicking near a point
            for i, point in enumerate(points):
                # Check if click is near a point
                if abs(point[0] - x) < 20 and abs(point[1] - y) < 20:
                    points[i] = (x, y)
                    print(f"Updated point {i+1} to ({x}, {y})")
                    draw_points_and_lines()
                    break

# Function to draw points and connecting lines
def draw_points_and_lines():
    global frame_copy, points
    
    # Create a copy of the current frame to draw on
    display_frame = frame_copy.copy()
    
    # Draw each point
    point_names = ["Top Left", "Top Right", "Bottom Right", "Bottom Left"]
    colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (255, 255, 0)]
    
    for i, point in enumerate(points):
        if i < len(points):
            # Draw circle for the point
            cv2.circle(display_frame, point, 5, colors[i], -1)
            
            # Add label
            if i < current_point:
                cv2.putText(display_frame, point_names[i], (point[0] + 10, point[1] + 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, colors[i], 2)
    
    # Draw connecting lines to show the tank boundary
    if len(points) > 1:
        for i in range(len(points)):
            if i < current_point - 1:
                cv2.line(display_frame, points[i], points[i+1], (255, 255, 255), 2)
        
        # Connect last point to first point if all 4 points are defined
        if current_point == 4:
            cv2.line(display_frame, points[3], points[0], (255, 255, 255), 2)
            
            # Fill the area with semi-transparent overlay
            overlay = display_frame.copy()
            pts = np.array(points, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.fillPoly(overlay, [pts], (0, 150, 0, 128))
            
            # Apply the overlay
            alpha = 0.3
            display_frame = cv2.addWeighted(overlay, alpha, display_frame, 1 - alpha, 0)
    
    # Add instructions
    instructions = [
        ("FISH TANK AREA CALIBRATION", (10, 30), (255, 255, 255)),
        ("Click on the FOUR CORNERS of your fish tank", (10, 60), (255, 255, 255)),
        ("1. Top Left → 2. Top Right → 3. Bottom Right → 4. Bottom Left", (10, 90), (200, 200, 200)),
        ("Press 'R' to restart", (10, 120), (0, 165, 255)),
        ("Press 'S' to save calibration", (10, 150), (0, 255, 0)),
        ("Press 'Q' to quit without saving", (10, 180), (0, 0, 255))
    ]
    
    for text, position, color in instructions:
        cv2.putText(display_frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    # Show calibration status
    if tank_area_defined:
        status = "✓ Tank area defined - Verify and adjust if needed"
        color = (0, 255, 0)
    else:
        status = f"Click to set corner {current_point + 1}/4"
        color = (0, 165, 255)
    
    cv2.putText(display_frame, status, (10, display_frame.shape[0] - 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
    # Show preview area
    preview_frame = get_transformed_view()
    if preview_frame is not None:
        h, w = preview_frame.shape[:2]
        max_height = 200
        if h > max_height:
            ratio = max_height / h
            preview_frame = cv2.resize(preview_frame, (int(w * ratio), max_height))
            
        # Put the preview in the top-right corner
        h, w = preview_frame.shape[:2]
        display_frame[10:10+h, display_frame.shape[1]-w-10:display_frame.shape[1]-10] = preview_frame
        
        # Add preview label
        cv2.putText(display_frame, "PREVIEW", (display_frame.shape[1]-w-10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Display the result
    cv2.imshow('Fish Tank Calibration', display_frame)

# Function to get perspective corrected view of tank area
def get_transformed_view():
    global frame_copy, points
    
    if frame_copy is None or len(points) < 4:
        return None
    
    # Define target rectangle (perspective corrected view)
    # Use width and height of the tank area
    width = int(max(
        np.sqrt((points[1][0] - points[0][0])**2 + (points[1][1] - points[0][1])**2),
        np.sqrt((points[2][0] - points[3][0])**2 + (points[2][1] - points[3][1])**2)
    ))
    
    height = int(max(
        np.sqrt((points[3][0] - points[0][0])**2 + (points[3][1] - points[0][1])**2),
        np.sqrt((points[2][0] - points[1][0])**2 + (points[2][1] - points[1][1])**2)
    ))
    
    # Avoid division by zero
    if width == 0 or height == 0:
        return None
    
    dst_pts = np.array([
        [0, 0],
        [width, 0],
        [width, height],
        [0, height]
    ], dtype=np.float32)
    
    src_pts = np.array(points, dtype=np.float32)
    
    # Calculate perspective transform matrix
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    
    # Apply perspective transformation
    warped = cv2.warpPerspective(frame_copy, M, (width, height))
    
    return warped

# Set mouse callback
cv2.setMouseCallback('Fish Tank Calibration', mouse_callback)

print("\n🔍 Fish Tank Area Calibration")
print("---------------------------")
print("This tool helps you define the exact area of your fish tank.")
print("Follow these steps:")
print("1. Click on the four corners of your fish tank, in this order:")
print("   • Top Left")
print("   • Top Right")
print("   • Bottom Right")
print("   • Bottom Left")
print("\nAfter defining all corners:")
print("- You can fine-tune by clicking near any point to reposition it")
print("- Press 'S' to save the calibration")
print("- Press 'R' to restart")
print("- Press 'Q' to quit without saving")

# Main loop
while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Can't get image from camera")
        break
    
    # Store a copy of the current frame
    frame_copy = frame.copy()
    
    # Draw the current state
    draw_points_and_lines()
    
    # Handle keyboard input
    key = cv2.waitKey(1) & 0xFF
    
    # Save calibration
    if key == ord('s') or key == ord('S'):
        if tank_area_defined:
            try:
                # Ensure the TankArea section exists
                if 'TankArea' not in config:
                    config.add_section('TankArea')
                
                # Save points to config
                config['TankArea']['top_left_x'] = str(points[0][0])
                config['TankArea']['top_left_y'] = str(points[0][1])
                config['TankArea']['top_right_x'] = str(points[1][0])
                config['TankArea']['top_right_y'] = str(points[1][1])
                config['TankArea']['bottom_right_x'] = str(points[2][0])
                config['TankArea']['bottom_right_y'] = str(points[2][1])
                config['TankArea']['bottom_left_x'] = str(points[3][0])
                config['TankArea']['bottom_left_y'] = str(points[3][1])
                
                with open(config_file, 'w') as f:
                    config.write(f)
                
                print("\n✅ Tank area calibration saved!")
                print("→ You can now close this tool and start the fish tracking program.")
                
                # Save a reference image for verification
                cv2.imwrite("tank_calibration.jpg", frame_copy)
                print("→ Saved reference image to 'tank_calibration.jpg'")
                
            except Exception as e:
                print(f"\n❌ Error saving calibration: {e}")
        else:
            print("\n⚠️ Please define all four corners before saving.")
    
    # Reset points
    elif key == ord('r') or key == ord('R'):
        points = []
        current_point = 0
        tank_area_defined = False
        print("\n↺ Reset calibration. Please define the corners again.")
    
    # Quit
    elif key == ord('q') or key == ord('Q'):
        print("\n→ Exiting without saving.")
        break

# Clean up
cap.release()
cv2.destroyAllWindows()
print("\n👋 Fish tank area calibration tool closed.")
