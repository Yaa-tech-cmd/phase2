"""Weather Report: fetch live data from Open-Meteo and print a readable summary.

Usage:
    python weather_report.py              # defaults to Mombasa
    python weather_report.py Nairobi
    python weather_report.py "Dar es Salaam"

No API key needed. Requires: pip install requests
"""

import sys
from datetime import datetime

import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Open-Meteo returns a numeric code for the sky condition; translate it to words.
WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Freezing fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    80: "Light showers", 81: "Showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Severe thunderstorm with hail",
}


def find_city(name):
    """Look up a city name and return its details (name, country, lat, lon)."""
    response = requests.get(GEOCODE_URL, params={"name": name, "count": 1}, timeout=10)
    response.raise_for_status()
    results = response.json().get("results")
    if not results:
        raise ValueError(f"Could not find a place called '{name}'.")
    return results[0]


def get_weather(latitude, longitude):
    """Fetch current conditions plus a 3-day forecast."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,"
                   "wind_speed_10m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
        "timezone": "auto",
        "forecast_days": 3,
    }
    response = requests.get(FORECAST_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def describe(code):
    return WEATHER_CODES.get(code, "Unknown conditions")


def print_report(city, data):
    now = data["current"]
    daily = data["daily"]
    line = "=" * 44

    print(line)
    print(f"  WEATHER REPORT: {city['name']}, {city['country']}")
    print(line)
    print(f"  Updated:      {datetime.fromisoformat(now['time']):%A %d %B %Y, %H:%M}")
    print()
    print("  RIGHT NOW")
    print(f"  Conditions:   {describe(now['weather_code'])}")
    print(f"  Temperature:  {now['temperature_2m']:.1f} °C "
          f"(feels like {now['apparent_temperature']:.1f} °C)")
    print(f"  Humidity:     {now['relative_humidity_2m']}%")
    print(f"  Wind speed:   {now['wind_speed_10m']:.1f} km/h")
    print()
    print("  3-DAY FORECAST")
    print("  " + "-" * 40)
    for i, day in enumerate(daily["time"]):
        label = datetime.fromisoformat(day).strftime("%a %d %b")
        print(f"  {label}: {describe(daily['weather_code'][i])}")
        print(f"      High {daily['temperature_2m_max'][i]:.1f} °C | "
              f"Low {daily['temperature_2m_min'][i]:.1f} °C | "
              f"Rain {daily['precipitation_sum'][i]:.1f} mm")
    print(line)
    print("  Data source: Open-Meteo.com")


def main():
    city_name = " ".join(sys.argv[1:]) or "Mombasa"
    try:
        city = find_city(city_name)
        data = get_weather(city["latitude"], city["longitude"])
        print_report(city, data)
    except ValueError as err:
        print(f"Error: {err}")
    except requests.exceptions.RequestException as err:
        print(f"Could not reach the weather service. Check your internet connection.\n({err})")


if __name__ == "__main__":
    main()
