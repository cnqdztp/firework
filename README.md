# Magic Fish Tank

This project creates an interactive fish tank that displays visual effects (like fireworks) that follow your fish as they swim around.

## Hardware Requirements

- Raspberry Pi (any model with camera support)
- Camera module or USB webcam
- Transparent fish tank or display with fish (like an iPad showing fish)
- Display monitor
- HDMI cables and power supplies

## Software Requirements

- Python 3
- OpenCV
- Flask
- Flask-CORS
- NumPy
- Web browser (Chrome/Chromium recommended)

## Installation

1. Install the required Python packages:

```bash
pip install opencv-python flask flask-cors numpy
```

## Fish Tank Area Calibration

If your fish tank or display isn't filling the entire camera view, or if the camera is at an angle to the tank creating distortion, you should first calibrate the tank area:

1. Run the calibration tool by selecting option 2 from the start menu or directly:
   ```bash
   python calibrate_tank_area.py
   ```
   
2. When the tool opens, you'll see the camera feed with instructions
   
3. Click on the FOUR CORNERS of your fish tank in this order:
   - Top Left
   - Top Right  
   - Bottom Right
   - Bottom Left
   
4. After setting all four corners, you'll see:
   - A highlighted polygon showing the tank area
   - A preview window showing the perspective-corrected view
   
5. You can click near any corner to fine-tune its position if needed
   
6. When satisfied, press 'S' to save the calibration
   
7. The tank area will now be used for fish detection, ignoring everything outside the defined boundaries

This calibration helps eliminate false detections from outside the tank and corrects for perspective distortion if your camera is at an angle.

## Color Calibration for Fish Detection

For the best detection results, use the color calibration tool:

```bash
python calibrate_color.py
```

The calibration tool allows you to:
- Adjust color thresholds in real-time
- Fine-tune morphological operations (blur, erode, dilate)
- Set minimum and maximum contour sizes for detection
- Test different camera indices
- Save settings directly to `config.ini`

After calibrating, press 's' to save the settings to `config.ini`.

## Configuration

The project uses a `config.ini` file to store all settings:

### Camera Settings
- `camera_index`: Which camera to use (0 for first camera, 1 for second camera, etc.)
- `width` and `height`: Camera resolution

### Tank Area Settings
- Coordinates for the four corners of the fish tank area
- Used to restrict detection to only the tank and correct perspective distortion

### Detection Settings
- HSV color ranges for red fish detection
- Contour size limits
- Blur, erode, and dilate parameters

### Server Settings
- `port`: Flask server port
- `web_port`: Web server port

## Changing Camera

If you have multiple cameras connected, you can easily switch between them:

1. Using the start menu: Select option 4 and enter the new camera index
2. Using the area or color calibration tools: Press 'C' during calibration
3. Directly edit `config.ini`: Change the `camera_index` value

## Running the Project

### On Windows

Simply double-click the `start_fish_tank.bat` file and select from the menu:
1. Start fish tank
2. Calibrate fish tank area (set boundaries)
3. Calibrate color detection
4. Change camera index
5. Exit

### On Linux/Mac

Make the scripts executable:

```bash
chmod +x start_fish_tank.sh stop_fish_tank.sh
```

Start the application:

```bash
./start_fish_tank.sh
```

Stop the application:

```bash
./stop_fish_tank.sh
```

## Visual Effects

You can choose from different visual effects for the fish trail:

1. **Bubbles** - Bubble-like particles that float upward (default)
2. **Fireworks** - Explosion effects that burst around your fish
3. **Flower Blossoms** - Petal-like particles that float gently
4. **Sparkles** - Star-shaped particles that flicker and twinkle
5. **Pixel Dust** - Small square particles with pulsing effects

Color schemes include:
- Blue
- Purple
- Rainbow (full color spectrum)
- Fire (orange/red tones)
- Green

## Troubleshooting

### Fish Detection Issues

- **Fish not detected**: Run the color calibration tool to adjust HSV ranges
- **Wrong camera selected**: Update the camera_index in config.ini or use option 4 in the start menu
- **False positives from outside tank**: Run the tank area calibration tool (option 2)
- **Distorted tracking due to camera angle**: Run the tank area calibration to correct perspective

### Server/Display Issues

- **Server connection errors**: Ensure ports 5000 and 8080 are available
- **Slow performance**: Lower camera resolution or reduce particle count

## Advanced Tips

- For better results, ensure consistent lighting on the fish tank
- Avoid reflections on the tank glass that might confuse the tracking
- Position the camera to capture the entire fish tank clearly
- If using an iPad or display as a "tank", be sure to define the tank area precisely
