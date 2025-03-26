@echo off
cd /d "%~dp0"

echo Interactive Fish Tank with Firework Effects
echo -------------------------------------------
echo 1. Start fish tank
echo 2. Calibrate fish tank area (set boundaries)
echo 3. Calibrate color detection
echo 4. Change camera index
echo 5. Exit
echo.

choice /C 12345 /N /M "Select an option (1-5): "

if errorlevel 5 goto :end
if errorlevel 4 goto :change_camera
if errorlevel 3 goto :calibrate_color
if errorlevel 2 goto :calibrate_area
if errorlevel 1 goto :prepare

:prepare
:: First, create a config.json file from config.ini for the web app
echo Creating config.json from config.ini...
python -c "import configparser, json; config = configparser.ConfigParser(); config.read('config.ini'); result = {s: dict(config.items(s)) for s in config.sections()}; open('config.json', 'w').write(json.dumps(result))"

goto :start

:start
:: Start the HTTP server
start cmd /k "python -m http.server 8080"

:: Start the fish tracker
start cmd /k "python fish_tracker.py"

:: Wait a moment for servers to start
timeout /t 3

:: Start Chrome in kiosk mode
start chrome --kiosk --incognito http://localhost:8080

echo Fish tank started. Close this window to exit.
echo To stop completely, close all command windows that were opened.
goto :end

:calibrate_area
:: Run the tank area calibration tool
start cmd /k "python calibrate_tank_area.py"
echo Tank area calibration tool started.
echo Follow the on-screen instructions to define the fish tank boundaries.
echo When finished, restart this script to apply the settings.
goto :end

:calibrate_color
:: Run the color calibration tool
start cmd /k "python calibrate_color.py"
echo Color calibration tool started.
echo Follow the on-screen instructions to calibrate fish detection.
echo When finished, restart this script to apply the settings.
goto :end

:change_camera
:: Change the camera index in config.ini
echo Current camera settings:
python -c "import configparser; config = configparser.ConfigParser(); config.read('config.ini'); print(f\"Camera index: {config['Camera']['camera_index']}\")"
echo.
set /p new_index="Enter new camera index: "

python -c "import configparser; config = configparser.ConfigParser(); config.read('config.ini'); config['Camera']['camera_index'] = '%new_index%'; f = open('config.ini', 'w'); config.write(f); f.close(); print('Camera index updated!')"

echo Camera index updated to %new_index% in config.ini
echo.
goto :end

:end