import json
import os
import requests
from typing import List
from mcp.server.fastmcp import FastMCP
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

# Initialize FastMCP server
mcp = FastMCP("weather_mcp")

locattion_to_coordinates = {
    "ottawa": {"latitude": 45.42, "longitude": -75.7},
    "toronto": {"latitude": 43.7, "longitude": -79.42},
    "vancouver": {"latitude": 49.28, "longitude": -123.12},
    "montreal": {"latitude": 45.5, "longitude": -73.57},
    "calgary": {"latitude": 51.05, "longitude": -114.07},
    "halifax": {"latitude": 44.65, "longitude": -63.57},
    "edmonton": {"latitude": 53.55, "longitude": -113.49},
    "winnipeg": {"latitude": 49.89, "longitude": -97.14},
    "victoria": {"latitude": 48.43, "longitude": -123.37},
    "quebec city": {"latitude": 46.81, "longitude": -71.21},
    "saskatoon": {"latitude": 52.13, "longitude": -106.67},
    "regina": {"latitude": 50.45, "longitude": -104.61},
    "st. john's": {"latitude": 47.56, "longitude": -52.71},
    "charlottetown": {"latitude": 46.24, "longitude": -63.13},
    "fredericton": {"latitude": 45.95, "longitude": -66.64},
    "yellowknife": {"latitude": 62.45, "longitude": -114.37},
    "whitehorse": {"latitude": 60.72, "longitude": -135.05},
    "iqaluit": {"latitude": 63.75, "longitude": -68.52},
    "thunder bay": {"latitude": 48.38, "longitude": -89.32},
    "sudbury": {"latitude": 46.49, "longitude": -80.99},
    "nanaimo": {"latitude": 49.16, "longitude": -123.94},
    "kamloops": {"latitude": 50.67, "longitude": -120.33},
    "lethbridge": {"latitude": 49.69, "longitude": -112.83},
    "abbotsford": {"latitude": 49.05, "longitude": -122.33},
    "sherbrooke": {"latitude": 45.4, "longitude": -71.9},
    "guelph": {"latitude": 43.55, "longitude": -80.23},
    "kingston": {"latitude": 44.23, "longitude": -76.48},
    "barrie": {"latitude": 44.39, "longitude": -79.66},
    "kitchener": {"latitude": 43.45, "longitude": -80.49},
    "windsor": {"latitude": 42.31, "longitude": -83.04},
    "london": {"latitude": 42.98, "longitude": -81.25},
    "sarnia": {"latitude": 42.98, "longitude": -82.4},
    "brantford": {"latitude": 43.18, "longitude": -80.27},
    "peterborough": {"latitude": 44.3, "longitude": -78.32},
    "sault ste. marie": {"latitude": 46.53, "longitude": -84.33},
    "north bay": {"latitude": 46.31, "longitude": -79.46},
    "prince george": {"latitude": 53.92, "longitude": -122.75},
    "chilliwack": {"latitude": 49.16, "longitude": -121.95},
    "medicine hat": {"latitude": 50.04, "longitude": -110.68},
    "grande prairie": {"latitude": 55.17, "longitude": -118.79},
    "fort mcmurray": {"latitude": 56.72, "longitude": -111.38},
    "lloydminster": {"latitude": 53.28, "longitude": -110.00},
    "moose jaw": {"latitude": 50.39, "longitude": -105.55},
    "brandon": {"latitude": 49.85, "longitude": -99.95},
    "cornwall": {"latitude": 45.02, "longitude": -74.73},
    "chatham": {"latitude": 42.4, "longitude": -82.18},
    "stratford": {"latitude": 43.37, "longitude": -80.98}
}
@mcp.tool()
def get_weather_data(location: str) -> json:
    """
    Fetch weather data for a given location and number of days.
    
    Args:
        location: The location to fetch weather data for

        
    Returns:
        List of weather data dictionaries
    """
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)
    coordinates = locattion_to_coordinates.get(location.lower(), None)
    if not coordinates:
        raise ValueError(f"Location '{location}' not found in predefined locations.")
    print(f"Fetching weather data for {location} at coordinates {coordinates['latitude']}, {coordinates['longitude']}")

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "location": location,
        "latitude": coordinates["latitude"],
        "longitude": coordinates["longitude"],
        "daily": ["sunset", "sunrise", "uv_index_max"],
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation_probability", "rain", "snowfall", "uv_index"],
        "current": ["temperature_2m", "rain", "precipitation", "apparent_temperature", "wind_gusts_10m", "wind_direction_10m", "wind_speed_10m"],
        "timezone": "America/New_York"
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    # Current values. The order of variables needs to be the same as requested.
    current = response.Current()
    current_temperature_2m = current.Variables(0).Value()
    current_rain = current.Variables(1).Value()
    current_precipitation = current.Variables(2).Value()
    current_apparent_temperature = current.Variables(3).Value()
    current_wind_gusts_10m = current.Variables(4).Value()
    current_wind_direction_10m = current.Variables(5).Value()
    current_wind_speed_10m = current.Variables(6).Value()

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
    # print(hourly_dataframe.to_json(orient = "records", date_format = "iso"))

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
    # print("\n=== UNIFIED WEATHER JSON DATA ===")
    # print(json.dumps(weather_json, indent=2, ensure_ascii=False))
    return weather_json

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')