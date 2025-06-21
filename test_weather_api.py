import json
import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": 45.42,
	"longitude": -75.7,
	"daily": ["sunset", "sunrise", "uv_index_max"],
	"hourly": ["temperature_2m", "relative_humidity_2m", "precipitation_probability", "rain", "snowfall", "uv_index"],
	"current": ["temperature_2m", "rain", "precipitation", "apparent_temperature", "wind_gusts_10m", "wind_direction_10m", "wind_speed_10m"],
	"timezone": "America/New_York"
}
responses = openmeteo.weather_api(url, params=params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation {response.Elevation()} m asl")
print(f"Timezone {response.Timezone()}{response.TimezoneAbbreviation()}")
print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

# Current values. The order of variables needs to be the same as requested.
current = response.Current()
current_temperature_2m = current.Variables(0).Value()
current_rain = current.Variables(1).Value()
current_precipitation = current.Variables(2).Value()
current_apparent_temperature = current.Variables(3).Value()
current_wind_gusts_10m = current.Variables(4).Value()
current_wind_direction_10m = current.Variables(5).Value()
current_wind_speed_10m = current.Variables(6).Value()

print(f"Current time {current.Time()}")
print(f"Current temperature_2m {current_temperature_2m}")
print(f"Current rain {current_rain}")
print(f"Current precipitation {current_precipitation}")
print(f"Current apparent_temperature {current_apparent_temperature}")
print(f"Current wind_gusts_10m {current_wind_gusts_10m}")
print(f"Current wind_direction_10m {current_wind_direction_10m}")
print(f"Current wind_speed_10m {current_wind_speed_10m}")

# Process hourly data. The order of variables needs to be the same as requested.
hourly = response.Hourly()
hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
hourly_precipitation_probability = hourly.Variables(2).ValuesAsNumpy()
hourly_rain = hourly.Variables(3).ValuesAsNumpy()
hourly_snowfall = hourly.Variables(4).ValuesAsNumpy()
hourly_uv_index = hourly.Variables(5).ValuesAsNumpy()

hourly_data = {"date": pd.date_range(
	start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
	end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
	freq = pd.Timedelta(seconds = hourly.Interval()),
	inclusive = "left"
)}

hourly_data["temperature_2m"] = hourly_temperature_2m
hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
hourly_data["precipitation_probability"] = hourly_precipitation_probability
hourly_data["rain"] = hourly_rain
hourly_data["snowfall"] = hourly_snowfall
hourly_data["uv_index"] = hourly_uv_index

hourly_dataframe = pd.DataFrame(data = hourly_data)
# print(hourly_dataframe)
print(hourly_dataframe.to_json(orient = "records", date_format = "iso"))

# Process daily data. The order of variables needs to be the same as requested.
daily = response.Daily()
daily_sunset = daily.Variables(0).ValuesInt64AsNumpy()
daily_sunrise = daily.Variables(1).ValuesInt64AsNumpy()
daily_uv_index_max = daily.Variables(2).ValuesAsNumpy()

daily_data = {"date": pd.date_range(
	start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
	end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
	freq = pd.Timedelta(seconds = daily.Interval()),
	inclusive = "left"
)}

daily_data["sunset"] = daily_sunset
daily_data["sunrise"] = daily_sunrise
daily_data["uv_index_max"] = daily_uv_index_max

daily_dataframe = pd.DataFrame(data = daily_data)
# print(daily_dataframe)
# print(daily_dataframe.to_json(orient = "records", date_format = "iso"))

# Create unified JSON data structure
def create_unified_weather_json():
    # Helper function to safely convert values
    def safe_convert(value):
        if isinstance(value, bytes):
            return value.decode('utf-8')
        elif hasattr(value, 'tolist'):  # numpy array
            return value.tolist()
        elif hasattr(value, 'item') and value.size == 1:  # numpy scalar
            return value.item()
        else:
            return value
    
    # Location information
    location_info = {
        "latitude": safe_convert(response.Latitude()),
        "longitude": safe_convert(response.Longitude()),
        "elevation": safe_convert(response.Elevation()),
        "timezone": safe_convert(response.Timezone()),
        "timezone_abbreviation": safe_convert(response.TimezoneAbbreviation()),
        "utc_offset_seconds": safe_convert(response.UtcOffsetSeconds())
    }
    
    # Current weather data
    current_weather = {
        "time": pd.to_datetime(current.Time(), unit="s", utc=True).isoformat(),
        "temperature_2m": safe_convert(current_temperature_2m),
        "rain": safe_convert(current_rain),
        "precipitation": safe_convert(current_precipitation),
        "apparent_temperature": safe_convert(current_apparent_temperature),
        "wind_gusts_10m": safe_convert(current_wind_gusts_10m),
        "wind_direction_10m": safe_convert(current_wind_direction_10m),
        "wind_speed_10m": safe_convert(current_wind_speed_10m)
    }
    
    # Hourly weather data
    hourly_weather = {
        "date_range": {
            "start": pd.to_datetime(hourly.Time(), unit="s", utc=True).isoformat(),
            "end": pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True).isoformat(),
            "interval_seconds": hourly.Interval()
        },
        "data": {
            "temperature_2m": safe_convert(hourly_temperature_2m),
            "relative_humidity_2m": safe_convert(hourly_relative_humidity_2m),
            "precipitation_probability": safe_convert(hourly_precipitation_probability),
            "rain": safe_convert(hourly_rain),
            "snowfall": safe_convert(hourly_snowfall),
            "uv_index": safe_convert(hourly_uv_index)
        }
    }
    
    # Daily weather data
    daily_weather = {
        "date_range": {
            "start": pd.to_datetime(daily.Time(), unit="s", utc=True).isoformat(),
            "end": pd.to_datetime(daily.TimeEnd(), unit="s", utc=True).isoformat(),
            "interval_seconds": daily.Interval()
        },
        "data": {
            "sunset": [pd.to_datetime(ts, unit="s", utc=True).isoformat() for ts in daily_sunset],
            "sunrise": [pd.to_datetime(ts, unit="s", utc=True).isoformat() for ts in daily_sunrise],
            "uv_index_max": safe_convert(daily_uv_index_max)
        }
    }
    
    # Unified JSON structure
    unified_weather_data = {
        "location": location_info,
        "current": current_weather,
        "hourly": hourly_weather,
        "daily": daily_weather,
        "generated_at": pd.Timestamp.now(tz='UTC').isoformat()
    }
    
    return unified_weather_data

# Generate and print the unified JSON
weather_json = create_unified_weather_json()
print("\n=== UNIFIED WEATHER JSON DATA ===")
# print(json.dumps(weather_json, indent=2, ensure_ascii=False))