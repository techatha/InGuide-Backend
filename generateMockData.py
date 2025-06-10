import json
from datetime import datetime, timedelta


def generate_mock_sensor_data(num_points=5, start_timestamp="2024-06-07T10:00:00Z"):
    """
    Generates a list of mock sensor data points for a window frame.

    Args:
        num_points (int): The number of data points in the window.
        start_timestamp (str): The starting timestamp in ISO format.

    Returns:
        list: A list of dictionaries, each representing a sensor data point.
    """
    data_points = []
    current_time = datetime.fromisoformat(start_timestamp.replace('Z', '+00:00'))  # Handle Z for UTC

    for i in range(num_points):
        # Simulate slight variations
        acc_x = 0.1 + i * 0.005
        acc_y = 0.05 + i * 0.003
        acc_z = 9.8 + i * 0.001
        acc_gx = 0.01 + i * 0.0001
        acc_gy = 0.02 + i * 0.0002
        acc_gz = 0.03 + i * 0.0003
        gyro_x = 0.001 + i * 0.00001
        gyro_y = 0.002 + i * 0.00002
        gyro_z = 0.003 + i * 0.00003
        gps_lat = 34.0522 + i * 0.0001
        gps_lon = -118.2437 - i * 0.00015

        data_point = {
            "timestamp": current_time.isoformat(timespec='seconds') + 'Z',  # Format back to 'Z'
            "time_imu": round(1000.123 + i * 1.0, 3),  # Simulate integer part incrementing
            "time_gps": round(1000.456 + i * 1.0, 3),
            "acc_x": round(acc_x, 4),
            "acc_y": round(acc_y, 4),
            "acc_z": round(acc_z, 4),
            "acc_gx": round(acc_gx, 4),
            "acc_gy": round(acc_gy, 4),
            "acc_gz": round(acc_gz, 4),
            "gyro_x": round(gyro_x, 5),
            "gyro_y": round(gyro_y, 5),
            "gyro_z": round(gyro_z, 5),
            "gps_lat": round(gps_lat, 6),
            "gps_lon": round(gps_lon, 6)
        }
        data_points.append(data_point)
        current_time += timedelta(seconds=1)  # Increment time by 1 second for each point

    return data_points


if __name__ == "__main__":
    reading_interval = 500  # Your desired reading interval

    mock_data = {
        "interval": reading_interval,
        "data": generate_mock_sensor_data(num_points=10)  # Generates a window of 5 data points
    }

    # Print the JSON object
    print(json.dumps(mock_data, indent=2))

    # Optional: Save to a file for easy use with Postman/curl
    # with open("mock_prediction_data.json", "w") as f:
    #     json.dump(mock_data, f, indent=2)
    # print("\nMock data saved to mock_prediction_data.json")
