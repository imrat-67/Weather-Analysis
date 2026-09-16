from dataclasses import dataclass

from pydantic import BaseModel


@dataclass
class City:
    city: str
    country: str


class CsvWritable():
    def to_csv(self, path: str, index: bool = False) -> None:
        ...


class LocationBase(BaseModel):
    city: str
    country: str


class GeoLocation(LocationBase):
    latitude: float
    longitude: float
    timezone: str


class WeatherBase(LocationBase):
    weather_code: int


class CurrentWeather(WeatherBase):
    temperature_2m: float
    relative_humidity_2m: float
    apparent_temperature: float
    wind_speed_10m: float
    pressure_msl: float


class ForecastWeather(WeatherBase):
    date: str
    temperature_2m_max: float
    temperature_2m_min: float
    precipitation_sum: float
    wind_speed_10m_max: float
