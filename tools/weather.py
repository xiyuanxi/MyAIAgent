import os

import requests
from langchain_core.tools import tool


@tool
def get_weather(city: str, query_type: str, days: int = 3, date: str = "") -> str:
    """Query weather information for a city.

    Args:
        city: City name, e.g. "Beijing", "New York", "London"
        query_type: One of "current", "forecast", "hourly", "history", or "hourly_history"
        days: Number of forecast days (1-14), used when query_type is "forecast" or "hourly"
        date: Date in YYYY-MM-DD format, used when query_type is "history" or "hourly_history"
    """
    print(f"[Tool Called] get_weather(city={city}, query_type={query_type})")
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return "Error: WEATHER_API_KEY is not configured. Please set it in your .env file."
    base_url = "http://api.weatherapi.com/v1"

    try:
        if query_type == "current":
            resp = requests.get(f"{base_url}/current.json", params={"key": api_key, "q": city}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            c = data["current"]
            return f"{data['location']['name']}: {c['temp_c']}°C, {c['condition']['text']}, Humidity {c['humidity']}%, Wind {c['wind_kph']} km/h"

        elif query_type == "forecast":
            days = min(max(days, 1), 14)
            resp = requests.get(f"{base_url}/forecast.json", params={"key": api_key, "q": city, "days": days}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            lines = [f"{data['location']['name']} {days}-day forecast:"]
            for day in data["forecast"]["forecastday"]:
                d = day["day"]
                lines.append(f"- {day['date']}: {d['maxtemp_c']}°C/{d['mintemp_c']}°C, {d['condition']['text']}")
            return "\n".join(lines)

        elif query_type == "hourly":
            days = min(max(days, 1), 14)
            resp = requests.get(f"{base_url}/forecast.json", params={"key": api_key, "q": city, "days": days}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            lines = [f"{data['location']['name']} hourly forecast ({days} day(s)):"]
            for day in data["forecast"]["forecastday"]:
                lines.append(f"\n[{day['date']}]")
                for hour in day["hour"]:
                    time_str = hour["time"].split(" ")[1]
                    lines.append(
                        f"  {time_str} | {hour['temp_c']}°C | {hour['condition']['text']} | "
                        f"Humidity {hour['humidity']}% | Wind {hour['wind_kph']} km/h | "
                        f"Rain {hour['chance_of_rain']}%"
                    )
            return "\n".join(lines)

        elif query_type == "history":
            if not date:
                return "Error: 'date' parameter is required for history queries (format: YYYY-MM-DD)"
            resp = requests.get(f"{base_url}/history.json", params={"key": api_key, "q": city, "dt": date}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            day = data["forecast"]["forecastday"][0]["day"]
            return f"{data['location']['name']} on {date}: {day['maxtemp_c']}°C/{day['mintemp_c']}°C, {day['condition']['text']}, Humidity {day['avghumidity']}%"

        elif query_type == "hourly_history":
            if not date:
                return "Error: 'date' parameter is required for hourly_history queries (format: YYYY-MM-DD)"
            resp = requests.get(f"{base_url}/history.json", params={"key": api_key, "q": city, "dt": date}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            lines = [f"{data['location']['name']} hourly history for {date}:"]
            for hour in data["forecast"]["forecastday"][0]["hour"]:
                time_str = hour["time"].split(" ")[1]
                lines.append(
                    f"  {time_str} | {hour['temp_c']}°C | {hour['condition']['text']} | "
                    f"Humidity {hour['humidity']}% | Wind {hour['wind_kph']} km/h"
                )
            return "\n".join(lines)

        else:
            return f"Error: Unknown query_type '{query_type}'. Use 'current', 'forecast', 'hourly', 'history', or 'hourly_history'."

    except requests.HTTPError as e:
        return f"Weather API error for {city}: HTTP {e.response.status_code}"
    except requests.RequestException as e:
        return f"Unable to reach weather service for {city}: {type(e).__name__}"
