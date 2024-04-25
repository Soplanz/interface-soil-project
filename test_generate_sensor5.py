import random
import requests
import json
from datetime import datetime, timedelta
import time

# URL of your backend endpoint
sensor_name = 'moisture_sensor5'
url = f"http://localhost:8000/receive-data/{sensor_name}"

# Starting timestamp
timestamp = datetime.now()

# Continuously send data
while True:
    try:
        # Construct data payload
        data = {
            "sensor_id": sensor_name,  # Add sensor ID to the payload
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "longitude": -6.3705264, 
            "latitude": 106.8268372,
            "temperature": 0,
            "humidity": random.randint(0, 100),
            "pressure": random.randint(0, 100)
        }

        # Send data as a POST request
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print("Data sent successfully:", data)
        else:
            print("Failed to send data:", data)

        # Increment timestamp by 2 seconds for the next data point
        timestamp += timedelta(seconds=2)

        # Wait for 2 seconds before sending the next data point
        time.sleep(2)
    except Exception as e:
        print("Error occurred while sending data:", e)