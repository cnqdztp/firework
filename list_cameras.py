import cv2
import platform
import os
import subprocess
import sys
import re
import json

def list_cameras_opencv():
    """Test camera indices using OpenCV until failure."""
    available_cameras = []
    index = 0
    
    while True:
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            break
        
        ret, frame = cap.read()
        if ret:
            # Get camera name if possible
            name = f"Camera #{index}"
            try:
                name = cap.getBackendName() + " - " + name
            except:
                pass
                
            # Get resolution if possible
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            resolution = f"{width}x{height}" if width > 0 and height > 0 else "Unknown"
            
            available_cameras.append({
                "index": index,
                "name": name,
                "resolution": resolution,
                "path": str(index)  # On Windows/Mac, the path is just the index
            })
            
        cap.release()
        index += 1
        
        # Set a reasonable limit to avoid trying too many indices
        if index > 10:
            break
            
    return available_cameras

def list_cameras_windows():
    """List cameras on Windows using DirectShow through PowerShell."""
    try:
        # PowerShell command to get the list of camera devices
        ps_cmd = """
        Add-Type -AssemblyName System.Management;
        $cameras = Get-WmiObject Win32_PnPEntity | Where-Object { $_.Name -match 'Camera|Webcam' -or $_.PNPClass -eq 'Image' };
        $cameras | Select-Object Name, DeviceID | ConvertTo-Json
        """
        
        # Run the PowerShell command
        result = subprocess.run(
            ["powershell", "-Command", ps_cmd],
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0 or not result.stdout.strip():
            return []
            
        # Parse the JSON output
        devices = json.loads(result.stdout)
        if not isinstance(devices, list):
            devices = [devices]
            
        # Get OpenCV cameras to match with DirectShow devices
        opencv_cameras = list_cameras_opencv()
        
        # Create the final list combining information
        cameras = []
        for i, device in enumerate(devices):
            camera_info = {
                "index": i if i < len(opencv_cameras) else i,
                "name": device.get("Name", f"Camera #{i}"),
                "device_id": device.get("DeviceID", "Unknown"),
                "path": str(i) if i < len(opencv_cameras) else "Unknown"
            }
            
            if i < len(opencv_cameras):
                camera_info["resolution"] = opencv_cameras[i]["resolution"]
                
            cameras.append(camera_info)
            
        return cameras
    except Exception as e:
        print(f"Error listing Windows cameras: {e}")
        return list_cameras_opencv()  # Fallback to OpenCV method

def list_cameras_linux():
    """List camera devices on Linux by checking /dev/video* devices."""
    try:
        # Find all video devices
        video_devices = []
        for dev in os.listdir('/dev'):
            if dev.startswith('video'):
                try:
                    device_path = f'/dev/{dev}'
                    # Check if it's a camera by trying to open it
                    cap = cv2.VideoCapture(device_path)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret:
                            # Try to get resolution
                            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            resolution = f"{width}x{height}" if width > 0 and height > 0 else "Unknown"
                            
                            # Try to get camera name using v4l2-ctl if available
                            name = f"Camera {dev}"
                            try:
                                v4l2_output = subprocess.check_output(
                                    ['v4l2-ctl', '--device', device_path, '--all'], 
                                    stderr=subprocess.STDOUT,
                                    text=True
                                )
                                for line in v4l2_output.split('\n'):
                                    if 'Card type:' in line:
                                        name = line.split('Card type:')[1].strip()
                                        break
                            except:
                                pass
                                
                            video_devices.append({
                                "index": int(dev.replace('video', '')),
                                "name": name,
                                "path": device_path,
                                "resolution": resolution
                            })
                    cap.release()
                except:
                    pass
                    
        return video_devices
    except Exception as e:
        print(f"Error listing Linux cameras: {e}")
        return list_cameras_opencv()  # Fallback to OpenCV method

def list_cameras_macos():
    """List cameras on macOS using AVFoundation through Python."""
    try:
        # First try the OpenCV method
        opencv_cameras = list_cameras_opencv()
        
        # Then try to enhance with system_profiler
        try:
            result = subprocess.run(
                ["system_profiler", "SPCameraDataType", "-json"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                camera_data = json.loads(result.stdout).get("SPCameraDataType", [])
                
                for i, camera in enumerate(camera_data):
                    if i < len(opencv_cameras):
                        opencv_cameras[i]["name"] = camera.get("_name", opencv_cameras[i]["name"])
                        opencv_cameras[i]["model"] = camera.get("model", "Unknown")
        except:
            pass
            
        return opencv_cameras
    except Exception as e:
        print(f"Error listing macOS cameras: {e}")
        return list_cameras_opencv()  # Fallback to OpenCV method

def main():
    """Main function to list cameras based on the platform."""
    os_name = platform.system().lower()
    
    print(f"Detecting cameras on {platform.system()}...")
    
    if os_name == 'windows':
        cameras = list_cameras_windows()
    elif os_name == 'darwin':  # macOS
        cameras = list_cameras_macos()
    elif os_name == 'linux':
        cameras = list_cameras_linux()
    else:
        cameras = list_cameras_opencv()
    
    if not cameras:
        print("No cameras detected.")
        return
    
    print(f"\nFound {len(cameras)} camera(s):")
    print("=" * 50)
    
    for i, camera in enumerate(cameras):
        print(f"Camera {i+1}:")
        print(f"  • Index for OpenCV: {camera.get('index', 'Unknown')}")
        print(f"  • Name: {camera.get('name', 'Unknown')}")
        print(f"  • Path/ID: {camera.get('path', 'Unknown')}")
        if 'resolution' in camera:
            print(f"  • Resolution: {camera['resolution']}")
        print("-" * 50)
    
    print("\nTo use a specific camera in your fish_tracker.py script, modify this line:")
    print('cap = cv2.VideoCapture(0)  # Replace 0 with the index or path from above')
    print("\nFor example:")
    print('cap = cv2.VideoCapture(1)  # For the second camera')
    
    if os_name == 'windows':
        print("\nOn Windows, you can also use:")
        print('cap = cv2.VideoCapture(cv2.CAP_DSHOW + camera_index)  # For better performance with DirectShow')
    
    if os_name == 'linux':
        print("\nOn Linux, you can use the device path directly:")
        print("cap = cv2.VideoCapture('/dev/videoX')  # Replace X with the device number")

if __name__ == "__main__":
    main()
