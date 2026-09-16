import asyncio
import time
from typing import Any

import httpx

from cities import load_city_records
from log import logger
from models import City, CurrentWeather, ForecastWeather, GeoLocation


GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


async def geocode_city(client: httpx.AsyncClient, city: City) -> dict[str, Any] | None:
    try:
        response = await client.get(
            GEO_URL,
            params={"name": city.city, "count": 1, "language": "en", "format": "json"},
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("results"):
            logger.warning(f"Geocoding failed for {city.city}: City not found")
            return None

        result = data["results"][0]
        logger.debug(
            f"Geocoding {city.city} -> lat={result['latitude']}, lon={result['longitude']}"
        )

        return GeoLocation(
            city=city.city,
            country=result.get("country", city.country),
            latitude=result["latitude"],
            longitude=result["longitude"],
            timezone=result.get("timezone", "auto"),
        ).model_dump()
    except Exception as exc:
        logger.error(f"Geocoding failed for {city.city}: {exc}")
        return None


async def fetch_weather(
    client: httpx.AsyncClient, location: dict[str, Any]
) -> dict[str, Any] | None:
    city = location["city"]
    try:
        response = await client.get(
            WEATHER_URL,
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "current": (
                    "temperature_2m,relative_humidity_2m,apparent_temperature,"
                    "weather_code,wind_speed_10m,pressure_msl"
                ),
                "daily": (
                    "temperature_2m_max,temperature_2m_min,precipitation_sum,"
                    "wind_speed_10m_max,weather_code"
                ),
                "timezone": location["timezone"],
                "forecast_days": 7,
            },
        )
        response.raise_for_status()
        data = response.json()

        current = CurrentWeather(
            city=city,
            country=location["country"],
            temperature_2m=data["current"]["temperature_2m"],
            relative_humidity_2m=data["current"]["relative_humidity_2m"],
            apparent_temperature=data["current"]["apparent_temperature"],
            weather_code=data["current"]["weather_code"],
            wind_speed_10m=data["current"]["wind_speed_10m"],
            pressure_msl=data["current"]["pressure_msl"],
        )

        daily = data["daily"]
        forecast = [
            ForecastWeather(
                city=city,
                country=location["country"],
                date=daily["time"][index],
                temperature_2m_max=daily["temperature_2m_max"][index],
                temperature_2m_min=daily["temperature_2m_min"][index],
                precipitation_sum=daily["precipitation_sum"][index],
                wind_speed_10m_max=daily["wind_speed_10m_max"][index],
                weather_code=daily["weather_code"][index],
            ).model_dump()
            for index in range(len(daily["time"]))
        ]

        logger.debug(f"Weather data received for {city}")
        return {"current": current.model_dump(), "forecast": forecast}
    except Exception as exc:
        logger.error(f"Failed to fetch weather for {city}: {exc}")
        return None


async def fetch_all_weather() -> dict[str, list[dict[str, Any]]]:
    cities = load_city_records()
    if not cities:
        logger.critical("No cities available for API fetch.")
        return {"current": [], "forecast": []}

    async with httpx.AsyncClient(timeout=20) as client:
        start = time.perf_counter()
        logger.info(f"Starting geocoding for {len(cities)} cities...")
        locations = [
            item
            for item in await asyncio.gather(*(geocode_city(client, city) for city in cities))
            if item is not None
        ]
        logger.info(
            f"Geocoding complete. {len(locations)}/{len(cities)} cities resolved "
            f"({time.perf_counter() - start:.1f}s)"
        )

        start = time.perf_counter()
        logger.info(f"Fetching weather data for {len(locations)} cities...")
        results = [
            item
            for item in await asyncio.gather(
                *(fetch_weather(client, location) for location in locations)
            )
            if item is not None
        ]
        logger.info(
            f"Weather fetch complete. {len(results)}/{len(locations)} cities "
            f"({time.perf_counter() - start:.1f}s)"
        )

    return {
        "current": [item["current"] for item in results],
        "forecast": [row for item in results for row in item["forecast"]],
    }


def get_weather_data() -> dict[str, list[dict[str, Any]]]:
    return asyncio.run(fetch_all_weather())


if __name__ == "__main__":
    print(get_weather_data())
