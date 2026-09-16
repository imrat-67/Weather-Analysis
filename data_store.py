from datetime import datetime

import pandas as pd

from api import get_weather_data
from constants import CURRENT_FILE, EXPORT_DIR, FORECAST_FILE
from constants import WMO_CODES
from log import logger


def add_condition_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["condition"] = df["weather_code"].map(WMO_CODES).fillna("Unknown")
    return df


def load_or_fetch_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("Checking for existing weather data...")

    if CURRENT_FILE.exists() and FORECAST_FILE.exists():
        logger.info("Existing data found, loading CSV...")
        current_df = pd.read_csv(CURRENT_FILE)
        forecast_df = pd.read_csv(FORECAST_FILE)
    else:
        logger.warning("No existing data found. Fetching from API...")
        current_df, forecast_df = fetch_fresh_data()

    return add_condition_names(current_df), add_condition_names(forecast_df)


def fetch_fresh_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    data = get_weather_data()
    current_df = pd.DataFrame(data["current"])
    forecast_df = pd.DataFrame(data["forecast"])

    if current_df.empty or forecast_df.empty:
        logger.critical("No weather data returned from API.")
        raise SystemExit("Could not fetch weather data. Please try again later.")

    save_weather_data(current_df, forecast_df)
    return current_df, forecast_df


def save_weather_data(current_df: pd.DataFrame, forecast_df: pd.DataFrame) -> None:
    logger.info(f"Saving current weather to {CURRENT_FILE}")
    current_df.to_csv(CURRENT_FILE, index=False)

    logger.info(f"Saving forecast data to {FORECAST_FILE}")
    forecast_df.to_csv(FORECAST_FILE, index=False)

    logger.info("Data saved successfully")


def delete_old_weather_files() -> None:
    logger.info("Deleting existing CSV files...")
    for path in (CURRENT_FILE, FORECAST_FILE):
        if path.exists():
            path.unlink()


def export_analysis(current_df: pd.DataFrame) -> str:
    logger.debug(f"Creating exports directory: {EXPORT_DIR}")
    EXPORT_DIR.mkdir(exist_ok=True)

    filename = f"weather_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    export_path = EXPORT_DIR / filename
    current_df.to_csv(export_path, index=False)

    logger.info(f"Exported {len(current_df)} records to {export_path}")
    return str(export_path)
