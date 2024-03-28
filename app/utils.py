from datetime import datetime
import requests

def get_nearest_hour(timestamp_str):
    dt = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
    nearest_hour = dt.hour
    nearest_dt = datetime(dt.year, dt.month, dt.day, nearest_hour)

    # Convert the result back to a string
    return str(nearest_dt.strftime('%Y%m%d%H%M'))

def get_today_info(latitude: str, longitude: str):
    api_data = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,relative_humidity_2m,dew_point_2m,precipitation,rain,weather_code,evapotranspiration,wind_speed_10m,wind_direction_10m&timezone=auto&forecast_days=1").json()
    api_dict = {
        'timestamp'         : api_data['hourly']['time'],
        'temperature'       : api_data['hourly']['temperature_2m'],
        'humidity'          : api_data['hourly']['relative_humidity_2m'],
        'dew_point'         : api_data['hourly']['dew_point_2m'],
        'precipitation'     : api_data['hourly']['precipitation'],
        'rain'              : api_data['hourly']['rain'],
        'weather_code'      : api_data['hourly']['weather_code'],
        'evapotranspiration': api_data['hourly']['evapotranspiration'],
        'wind_speed'        : api_data['hourly']['wind_speed_10m'],
        'wind_direction'    : api_data['hourly']['wind_direction_10m']
    }

    features_col = [
        'temperature',
        'humidity',
        'dew_point',
        'precipitation',
        'rain',
        'weather_code',
        'evapotranspiration',
        'wind_speed',
        'wind_direction'
    ]

    api_dict['timestamp'] = [time.replace('-', '').replace(':', '').replace('T', '') for time in api_dict['timestamp']]
    return api_dict, features_col