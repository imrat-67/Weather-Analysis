from datetime import datetime

from analysis import (
    filter_by_temperature,
    show_city_forecast,
    show_humidity_analysis,
    show_summary,
    show_temperature_comparison,
)
from data_store import (
    add_condition_names,
    delete_old_weather_files,
    export_analysis,
    fetch_fresh_data,
    load_or_fetch_data,
)
from log import logger


class WeatherDashboard:
    def __init__(self) -> None:
        self.current_df = None
        self.forecast_df = None

    def start(self) -> None:
        logger.info("Application started")

        try:
            self.current_df, self.forecast_df = load_or_fetch_data()
            self.menu_loop()
        except (KeyboardInterrupt, EOFError):
            print("\nProgram stopped by user. Goodbye.")
            logger.info("Application stopped by user")

    def menu_loop(self) -> None:
        while True:
            show_menu()
            choice = input("Enter your choice (0-7): ").strip()

            match choice:
                case "1":
                    show_summary(self.current_df)
                case "2":
                    show_temperature_comparison(self.current_df)
                case "3":
                    show_humidity_analysis(self.current_df)
                case "4":
                    show_city_forecast(self.current_df, self.forecast_df)
                case "5":
                    filter_by_temperature(self.current_df)
                case "6":
                    self.refetch_data()
                case "7":
                    self.export_data()
                case "0":
                    logger.info("User selected option 0: Exit")
                    print("Thank you for using Weather Analytics Dashboard! Goodbye")
                    break
                case _:
                    logger.warning(f"Invalid menu choice: {choice}")
                    print("Invalid choice. Please enter a number from 0 to 7.")

    def refetch_data(self) -> None:
        logger.info("User selected option 6: Re-fetch Data")
        answer = input("Re-fetch all weather data from the API? (y/n): ").strip().lower()

        if answer != "y":
            logger.info("User cancelled re-fetch")
            print("Re-fetch cancelled. Returning to menu.")
            return

        logger.info("User confirmed re-fetch")
        delete_old_weather_files()
        current_df, forecast_df = fetch_fresh_data()
        self.current_df = add_condition_names(current_df)
        self.forecast_df = add_condition_names(forecast_df)

        print("Data saved to CSV files.")
        print("DataFrames reloaded successfully.")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("Data saved and DataFrames reloaded")

    def export_data(self) -> None:
        logger.info("User selected option 7: Export to CSV")
        export_path = export_analysis(self.current_df)

        print("Analysis exported successfully!")
        print(f"File: {export_path}")
        print(f"Records: {len(self.current_df)} cities")


def show_menu() -> None:
    print("\nWeather Analytics Dashboard")
    print("1. Summary Table")
    print("2. Temperature Comparison Table")
    print("3. Humidity Analysis")
    print("4. 7-Day Forecast for a City")
    print("5. Filter Cities by Temperature")
    print("6. Re-fetch Fresh Data")
    print("7. Export Analysis to CSV")
    print("0. Exit")


if __name__ == "__main__":
    WeatherDashboard().start()
