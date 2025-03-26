import requests
import time
import json
import configparser
import os

# Get server port from config
config = configparser.ConfigParser()
config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')

try:
    config.read(config_file)
    if 'Server' in config:
        server_port = config.getint('Server', 'port')
    else:
        server_port = 5000
except:
    server_port = 5000

print(f"🔍 Testing fish position API on port {server_port}")
print("-------------------------------------")

# Try to connect to the API
api_url = f"http://localhost:{server_port}/position"
print(f"Connecting to: {api_url}")

success = False
attempts = 0
max_attempts = 10

while not success and attempts < max_attempts:
    try:
        response = requests.get(api_url, timeout=0.5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Connection successful!")
            print(f"Fish position: x={data['x']:.2f}, y={data['y']:.2f}")
            success = True
        else:
            print(f"❌ Connection failed with status code {response.status_code}")
            attempts += 1
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed - server not responding (attempt {attempts+1}/{max_attempts})")
        attempts += 1
    except Exception as e:
        print(f"❌ Error: {e}")
        attempts += 1
    
    if not success and attempts < max_attempts:
        print("Retrying in 1 second...")
        time.sleep(1)

if not success:
    print("\n❗ Could not connect to the fish position API. Possible issues:")
    print("1. Fish tracker is not running")
    print("2. Server port is incorrect (check config.ini)")
    print("3. Server is running but has an error")
    print("\nTry running fish_tracker.py directly to see if there are errors.")
else:
    print("\nNow checking if config.json is correctly created...")
    try:
        with open('config.json', 'r') as f:
            config_json = json.load(f)
            print("✅ config.json exists and is valid JSON")
            if 'Server' in config_json and 'port' in config_json['Server']:
                print(f"✅ Server port in config.json: {config_json['Server']['port']}")
            else:
                print("❌ Server port not found in config.json")
    except FileNotFoundError:
        print("❌ config.json not found - this file is needed for the web interface")
    except json.JSONDecodeError:
        print("❌ config.json exists but is not valid JSON")
    except Exception as e:
        print(f"❌ Error reading config.json: {e}")

print("\nNow monitoring fish position for 5 seconds to check for updates...")
start_time = time.time()
positions = []

while time.time() - start_time < 5:
    try:
        response = requests.get(api_url, timeout=0.5)
        if response.status_code == 200:
            data = response.json()
            positions.append((data['x'], data['y']))
            print(f"Position: x={data['x']:.2f}, y={data['y']:.2f}")
        time.sleep(0.5)
    except:
        pass

if len(positions) > 1:
    # Check if the position is changing
    is_changing = any(p1 != p2 for p1, p2 in zip(positions, positions[1:]))
    if is_changing:
        print("✅ Fish position is updating correctly")
    else:
        print("⚠️ Fish position is not changing - fish might not be detected")
else:
    print("❌ Couldn't get multiple position updates")

print("\n🔍 API Debug Summary:")
if success:
    print("✅ API connection: Working")
else:
    print("❌ API connection: Failed")

print("\nIf API is working but effects still don't appear, check:")
print("1. Open browser console (F12) to see any JavaScript errors")
print("2. Make sure the port in index.html matches the port in config.json")
print("3. Try refreshing the page after fish_tracker.py is running")
