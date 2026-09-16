import csv
from pathlib import Path
from log import logger
from models import City


def load_city_records() -> list[City]:
    file_path = Path(__file__).resolve().parent / "data" / "cities.csv"

    logger.info(f"Reading cities from {file_path}")

    if not file_path.exists():
        logger.critical(f"Critical Error: {file_path} file not found at all!")
        return []

    cities_list = []

    try:

        with open(file_path, mode="r", encoding="utf-8", newline="") as file:
            csv_reader = csv.DictReader(file)

            for row in csv_reader:
                cities_list.append(City(city=row["city"], country=row["country"]))

        logger.debug(f"Loaded {len(cities_list)} cities from CSV")
        return cities_list

    except Exception as e:
        logger.error(f"Something failed that should have worked: File write/read error. Detail: {e}")
        return []


def load_cities() -> list[str]:
    return [record.city for record in load_city_records()]


if __name__ == "__main__":
    print(load_cities())
