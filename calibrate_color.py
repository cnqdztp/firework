import cv2
import numpy as np
import os
import sys
import configparser

def nothing(x):
    pass

print("🐠 Fish Tank Calibration Tool 🐠")
print("===============================")
print("This tool helps your camera find the red fish.")

# Read settings file
config = configparser.ConfigParser()
config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')

if not os.path.exists(config_file):
    print("⚠️ Settings file not found. We'll create a new one for you.")
else:
    print("✓ Found settings file.")

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
    
    print(f"✓ Using camera #{CAMERA_INDEX}")
    
except Exception as e:
    print(f"⚠️ Couldn't read settings. Using defaults.")
    
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

# Create windows with friendly names
cv2.namedWindow('Original Image')
cv2.namedWindow('Fish Detection Mask')
cv2.namedWindow('Adjust Settings', cv2.WINDOW_NORMAL)  # Make this window resizable

# Set a fixed size for the settings window to ensure labels are visible
cv2.resizeWindow('Adjust Settings', 400, 700)

# Create trackbars with shorter, clearer names that fit in the window
cv2.createTrackbar('Red Low 1', 'Adjust Settings', H_LOW1, 180, nothing)
cv2.createTrackbar('Red High 1', 'Adjust Settings', H_HIGH1, 180, nothing)
cv2.createTrackbar('Red Low 2', 'Adjust Settings', H_LOW2, 180, nothing)
cv2.createTrackbar('Red High 2', 'Adjust Settings', H_HIGH2, 180, nothing)
cv2.createTrackbar('Sat Min', 'Adjust Settings', S_LOW, 255, nothing)
cv2.createTrackbar('Sat Max', 'Adjust Settings', S_HIGH, 255, nothing)
cv2.createTrackbar('Val Min', 'Adjust Settings', V_LOW, 255, nothing)
cv2.createTrackbar('Val Max', 'Adjust Settings', V_HIGH, 255, nothing)

# More intuitive slider names
cv2.createTrackbar('Smooth', 'Adjust Settings', BLUR_SIZE, 15, nothing)
cv2.createTrackbar('Reduce Noise', 'Adjust Settings', ERODE_ITERATIONS, 10, nothing)
cv2.createTrackbar('Fill Gaps', 'Adjust Settings', DILATE_ITERATIONS, 10, nothing)
cv2.createTrackbar('Min Size', 'Adjust Settings', MIN_CONTOUR_AREA, 2000, nothing)
cv2.createTrackbar('Max Size', 'Adjust Settings', MAX_CONTOUR_AREA, 20000, nothing)

print("\n🎛️ Calibration Started")
print("-------------------")
print("You should see three windows:")
print("1. Original Image - Shows what the camera sees")
print("2. Fish Detection Mask - Shows what the program detects as fish")
print("3. Adjust Settings - Sliders to adjust detection")

print("\n👉 Quick Guide:")
print("- Adjust the sliders until your fish is highlighted in the 'Fish Detection Mask' window")
print("- Green boxes in the 'Original Image' mean the fish is detected")
print("- The fish should be highlighted in white in the 'Fish Detection Mask'")

print("\n⌨️ Keyboard Controls:")
print("- Press 'S' to save your settings")
print("- Press 'C' to try a different camera")
print("- Press 'Q' to quit without saving")

# Create legend to explain sliders
legend_img = np.zeros((230, 390, 3), np.uint8)
legend_img[:] = (50, 50, 50)  # Dark gray background

# Add explanatory text
cv2.putText(legend_img, "SETTINGS GUIDE", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
cv2.putText(legend_img, "Red Low/High 1: First red range", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 140, 255), 1)
cv2.putText(legend_img, "Red Low/High 2: Second red range", (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 140, 255), 1)
cv2.putText(legend_img, "Sat Min/Max: Color intensity", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
cv2.putText(legend_img, "Val Min/Max: Brightness", (10, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
cv2.putText(legend_img, "Smooth: Blur small details", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
cv2.putText(legend_img, "Reduce Noise: Remove small dots", (10, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
cv2.putText(legend_img, "Fill Gaps: Connect nearby areas", (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

# Display the legend in its own window
cv2.namedWindow('Settings Guide')
cv2.imshow('Settings Guide', legend_img)
cv2.moveWindow('Settings Guide', 50 + 400 + 40, 400)  # Position below settings window

# Main calibration loop
while True:
    # Capture frame
    ret, frame = cap.read()
    if not ret:
        print("❌ Can't get image from camera")
        break
    
    # Get values from sliders
    h_low1 = cv2.getTrackbarPos('Red Low 1', 'Adjust Settings')
    h_high1 = cv2.getTrackbarPos('Red High 1', 'Adjust Settings')
    h_low2 = cv2.getTrackbarPos('Red Low 2', 'Adjust Settings')
    h_high2 = cv2.getTrackbarPos('Red High 2', 'Adjust Settings')
    s_low = cv2.getTrackbarPos('Sat Min', 'Adjust Settings')
    s_high = cv2.getTrackbarPos('Sat Max', 'Adjust Settings')
    v_low = cv2.getTrackbarPos('Val Min', 'Adjust Settings')
    v_high = cv2.getTrackbarPos('Val Max', 'Adjust Settings')
    
    blur_size = cv2.getTrackbarPos('Smooth', 'Adjust Settings')
    erode_iter = cv2.getTrackbarPos('Reduce Noise', 'Adjust Settings')
    dilate_iter = cv2.getTrackbarPos('Fill Gaps', 'Adjust Settings')
    min_area = cv2.getTrackbarPos('Min Size', 'Adjust Settings')
    max_area = cv2.getTrackbarPos('Max Size', 'Adjust Settings')
    
    # Make sure blur is odd number (technical requirement)
    if blur_size % 2 == 0:
        blur_size += 1
    if blur_size < 1:
        blur_size = 1
    
    # Convert frame to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Create mask for red color (combining both red ranges)
    lower_red1 = np.array([h_low1, s_low, v_low])
    upper_red1 = np.array([h_high1, s_high, v_high])
    lower_red2 = np.array([h_low2, s_low, v_low])
    upper_red2 = np.array([h_high2, s_high, v_high])
    
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)
    
    # Apply smoothing and cleanup operations
    kernel = np.ones((5,5), np.uint8)
    
    if blur_size > 0:
        mask = cv2.GaussianBlur(mask, (blur_size, blur_size), 0)
    
    if erode_iter > 0:
        mask = cv2.erode(mask, kernel, iterations=erode_iter)
    
    if dilate_iter > 0:
        mask = cv2.dilate(mask, kernel, iterations=dilate_iter)
    
    # Find contours in the mask (detected objects)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Create a copy of the original frame to draw on
    result = frame.copy()
    
    # Check for fish-sized objects
    valid_contours = []
    if contours:
        valid_contours = [c for c in contours if min_area < cv2.contourArea(c) < max_area]
        
        # Draw boxes around detected fish
        for contour in valid_contours:
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)
            area = cv2.contourArea(contour)
            cv2.putText(result, f"Fish detected! Size: {area:.0f}", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # Add helpful instructions on screen
    cv2.putText(result, "FISH TANK CALIBRATION", (10, 25), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    cv2.putText(result, "Press 'S' to SAVE settings", (10, 55), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(result, "Press 'C' to change camera", (10, 85), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
    cv2.putText(result, "Press 'Q' to quit without saving", (10, 115), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    # Show camera info
    cv2.putText(result, f"Camera #{CAMERA_INDEX}", (result.shape[1]-150, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Add calibration summary
    if len(valid_contours) > 0:
        calibration_status = f"✓ Found {len(valid_contours)} fish-like objects"
        status_color = (0, 255, 0)  # Green
    else:
        calibration_status = "❌ No fish detected - adjust sliders"
        status_color = (0, 0, 255)  # Red
    
    cv2.putText(result, calibration_status, (10, result.shape[0]-30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
    
    # Convert detection mask to color for better visualization
    mask_colored = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    
    # Add text to mask image
    cv2.putText(mask_colored, "DETECTION MASK - Fish should appear white", (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Show the images
    cv2.imshow('Original Image', result)
    cv2.imshow('Fish Detection Mask', mask_colored)
    
    # Arrange windows for better visibility
    cv2.moveWindow('Original Image', 50, 50)
    cv2.moveWindow('Fish Detection Mask', 50, 50 + frame.shape[0] + 40)
    cv2.moveWindow('Adjust Settings', 50 + frame.shape[1] + 20, 50)
    
    # Wait for key press
    key = cv2.waitKey(1) & 0xFF
    
    # If 's' or 'S' is pressed, save settings
    if key == ord('s') or key == ord('S'):
        try:
            config.set('Camera', 'camera_index', str(CAMERA_INDEX))
            
            config.set('Detection', 'min_contour_area', str(min_area))
            config.set('Detection', 'max_contour_area', str(max_area))
            config.set('Detection', 'h_low1', str(h_low1))
            config.set('Detection', 'h_high1', str(h_high1))
            config.set('Detection', 'h_low2', str(h_low2))
            config.set('Detection', 'h_high2', str(h_high2))
            config.set('Detection', 's_low', str(s_low))
            config.set('Detection', 's_high', str(s_high))
            config.set('Detection', 'v_low', str(v_low))
            config.set('Detection', 'v_high', str(v_high))
            config.set('Detection', 'blur_size', str(blur_size))
            config.set('Detection', 'erode_iterations', str(erode_iter))
            config.set('Detection', 'dilate_iterations', str(dilate_iter))
            
            with open(config_file, 'w') as f:
                config.write(f)
            
            print("\n✅ Settings saved successfully!")
            print("→ You can now close this window and start the fish tank.")
            
        except Exception as e:
            print(f"\n❌ Error saving settings: {e}")
    
    # If 'c' or 'C' is pressed, change camera
    elif key == ord('c') or key == ord('C'):
        try:
            cap.release()
            cv2.destroyAllWindows()
            
            new_index = input(f"\nCurrently using camera #{CAMERA_INDEX}. Enter new camera number: ")
            CAMERA_INDEX = int(new_index)
            
            print(f"→ Trying camera #{CAMERA_INDEX}...")
            cap = cv2.VideoCapture(CAMERA_INDEX)
            if not cap.isOpened():
                print(f"❌ Camera #{CAMERA_INDEX} not found. Returning to previous camera.")
                CAMERA_INDEX = config.getint('Camera', 'camera_index')
                cap = cv2.VideoCapture(CAMERA_INDEX)
            else:
                print(f"✓ Camera #{CAMERA_INDEX} working!")
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            
            # Recreate windows
            cv2.namedWindow('Original Image')
            cv2.namedWindow('Fish Detection Mask')
            cv2.namedWindow('Adjust Settings', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Adjust Settings', 400, 700)
            
            # Recreate sliders
            cv2.createTrackbar('Red Low 1', 'Adjust Settings', h_low1, 180, nothing)
            cv2.createTrackbar('Red High 1', 'Adjust Settings', h_high1, 180, nothing)
            cv2.createTrackbar('Red Low 2', 'Adjust Settings', h_low2, 180, nothing)
            cv2.createTrackbar('Red High 2', 'Adjust Settings', h_high2, 180, nothing)
            cv2.createTrackbar('Sat Min', 'Adjust Settings', s_low, 255, nothing)
            cv2.createTrackbar('Sat Max', 'Adjust Settings', s_high, 255, nothing)
            cv2.createTrackbar('Val Min', 'Adjust Settings', v_low, 255, nothing)
            cv2.createTrackbar('Val Max', 'Adjust Settings', v_high, 255, nothing)
            cv2.createTrackbar('Smooth', 'Adjust Settings', blur_size, 15, nothing)
            cv2.createTrackbar('Reduce Noise', 'Adjust Settings', erode_iter, 10, nothing)
            cv2.createTrackbar('Fill Gaps', 'Adjust Settings', dilate_iter, 10, nothing)
            cv2.createTrackbar('Min Size', 'Adjust Settings', min_area, 2000, nothing)
            cv2.createTrackbar('Max Size', 'Adjust Settings', max_area, 20000, nothing)
            
            # Recreate legend window
            cv2.namedWindow('Settings Guide')
            cv2.imshow('Settings Guide', legend_img)
            
        except Exception as e:
            print(f"❌ Error changing camera: {e}")
    
    # If 'q' or 'Q' is pressed, quit
    elif key == ord('q') or key == ord('Q'):
        print("\n→ Exiting without saving")
        break

# Clean up
cap.release()
cv2.destroyAllWindows()
print("\n👋 Calibration tool closed.")
