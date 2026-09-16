from functools import wraps
from typing import Callable, Iterator

import pandas as pd

from log import logger


def humidity_label(humidity: float) -> str:
    if humidity < 40:
        return "DRY"
    if humidity <= 70:
        return "COMFORTABLE"
    return "HUMID"


def log_action(message: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(message)
            return func(*args, **kwargs)

        return wrapper

    return decorator


@log_action("User selected option 1: Summary Table")
def show_summary(current_df: pd.DataFrame) -> None:
    logger.debug(f"Displaying current weather for {len(current_df)} cities")
    columns = [
        "city",
        "country",
        "temperature_2m",
        "apparent_temperature",
        "relative_humidity_2m",
        "wind_speed_10m",
        "pressure_msl",
        "condition",
    ]
    names = {
        "city": "City",
        "country": "Country",
        "temperature_2m": "Temp(C)",
        "apparent_temperature": "Feels Like",
        "relative_humidity_2m": "Humidity",
        "wind_speed_10m": "Wind(km/h)",
        "pressure_msl": "Pressure",
        "condition": "Condition",
    }
    print(current_df[columns].rename(columns=names).to_string(index=False))


@log_action("User selected option 2: Temperature Comparison")
def show_temperature_comparison(current_df: pd.DataFrame) -> None:
    table = current_df.copy()
    table["Difference"] = table["apparent_temperature"] - table["temperature_2m"]
    table["Status"] = table["Difference"].apply(get_temp_status)
    table = table.sort_values("temperature_2m", ascending=False)

    logger.debug(f"Sorted {len(table)} cities by temperature (descending)")
    print(table[["city", "temperature_2m", "apparent_temperature", "Difference", "Status"]]
          .rename(columns={
              "city": "City",
              "temperature_2m": "Actual(C)",
              "apparent_temperature": "Feels(C)",
          })
          .to_string(index=False))


def get_temp_status(difference: float) -> str:
    if difference > 0:
        return "Warmer"
    if difference < 0:
        return "Cooler"
    return "Same"


@log_action("User selected option 3: Humidity Analysis")
def show_humidity_analysis(current_df: pd.DataFrame) -> None:
    table = current_df[["city", "relative_humidity_2m"]].copy()
    table["Severity"] = table["relative_humidity_2m"].apply(humidity_label)
    table["Indicator"] = table["Severity"].map({
        "DRY": "GREEN",
        "COMFORTABLE": "YELLOW",
        "HUMID": "RED",
    })
    table = table.sort_values("relative_humidity_2m", ascending=False)
    counts = table["Severity"].value_counts()

    logger.debug(
        f"Categorized {len(table)} cities: "
        f"{counts.get('HUMID', 0)} HUMID, "
        f"{counts.get('COMFORTABLE', 0)} COMFORTABLE, "
        f"{counts.get('DRY', 0)} DRY"
    )

    print(table.rename(columns={
        "city": "City",
        "relative_humidity_2m": "Humidity (%)",
    }).to_string(index=False))
    print("\nSummary:")
    print(f"HUMID cities: {counts.get('HUMID', 0)}")
    print(f"COMFORTABLE cities: {counts.get('COMFORTABLE', 0)}")
    print(f"DRY cities: {counts.get('DRY', 0)}")
    print(f"Average humidity: {table['relative_humidity_2m'].mean():.1f}%")


@log_action("User selected option 4: 7-Day Forecast")
def show_city_forecast(current_df: pd.DataFrame, forecast_df: pd.DataFrame) -> None:
    available = ", ".join(current_df["city"])
    print(f"Available cities: {available}")

    city_name = input("Enter city name: ").strip()
    logger.debug(f"User entered city: {city_name}")

    matches = current_df[current_df["city"].str.lower() == city_name.lower()]
    if matches.empty:
        logger.warning(f"User entered invalid city name: {city_name}")
        print("City not found. Please enter a valid city name from the list.")
        return

    city = matches.iloc[0]["city"]
    country = matches.iloc[0]["country"]
    rows = pd.DataFrame(list(forecast_rows_for_city(forecast_df, city)))
    rows["Temp Range"] = rows["temperature_2m_max"] - rows["temperature_2m_min"]

    logger.info(f"Displaying 7-day forecast for {city}")
    print(f"\n7-Day Forecast for {city}, {country}")
    print_forecast_table(rows)
    print_forecast_summary(rows)


def forecast_rows_for_city(forecast_df: pd.DataFrame, city: str) -> Iterator[dict]:
    city_rows = forecast_df[forecast_df["city"].str.lower() == city.lower()]
    for row in city_rows.to_dict("records"):
        yield row


def print_forecast_table(rows: pd.DataFrame) -> None:
    columns = [
        "date",
        "temperature_2m_max",
        "temperature_2m_min",
        "Temp Range",
        "precipitation_sum",
        "wind_speed_10m_max",
        "condition",
    ]
    names = {
        "date": "Date",
        "temperature_2m_max": "Max(C)",
        "temperature_2m_min": "Min(C)",
        "precipitation_sum": "Precip(mm)",
        "wind_speed_10m_max": "Wind(km/h)",
        "condition": "Condition",
    }
    print(rows[columns].rename(columns=names).to_string(index=False))


def print_forecast_summary(rows: pd.DataFrame) -> None:
    max_row = rows.loc[rows["temperature_2m_max"].idxmax()]
    min_row = rows.loc[rows["temperature_2m_min"].idxmin()]
    wind_row = rows.loc[rows["wind_speed_10m_max"].idxmax()]

    print("\nSummary:")
    print(f"Highest: {max_row['temperature_2m_max']}C on {max_row['date']}")
    print(f"Lowest: {min_row['temperature_2m_min']}C on {min_row['date']}")
    print(f"Total precipitation: {rows['precipitation_sum'].sum():.1f}mm")
    print(f"Max wind speed: {wind_row['wind_speed_10m_max']} km/h on {wind_row['date']}")


@log_action("User selected option 5: Filter by Temperature")
def filter_by_temperature(current_df: pd.DataFrame) -> None:
    raw_value = input("Enter temperature threshold (C): ").strip()
    try:
        threshold = float(raw_value)
    except ValueError:
        logger.warning(f"Invalid input for threshold: '{raw_value}' is not a number")
        print("Invalid input. Please enter a numeric value.")
        return

    logger.debug(f"User entered threshold: {threshold}")
    table = current_df[current_df["temperature_2m"] > threshold]

    if table.empty:
        logger.info(f"No cities found above {threshold}C")
        print(f"No cities found above {threshold}C.")
        return

    logger.info(f"Found {len(table)} cities above {threshold}C")
    print(f"\nCities with temperature above {threshold}C:")
    print(table[["city", "country", "temperature_2m", "condition"]].rename(columns={
        "city": "City",
        "country": "Country",
        "temperature_2m": "Temp(C)",
        "condition": "Condition",
    }).to_string(index=False))
    print(f"\n{len(table)} out of {len(current_df)} cities match the filter.")
