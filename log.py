import logging

logger = logging.getLogger("weather_dashboard")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    console_handler = logging.StreamHandler()
    log_format = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

logger.info("Logger initialized successfully.")
