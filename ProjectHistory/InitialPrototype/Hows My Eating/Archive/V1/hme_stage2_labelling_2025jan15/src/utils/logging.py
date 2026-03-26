import sys
import logging

def setup_logging(log_file_path: str) -> logging.Logger:
    """Sets up logging with both file and console handlers."""
    logger = logging.getLogger("step1_logger")
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers (to prevent duplicate logging)
    if logger.hasHandlers():
        logger.handlers.clear()

    # File Handler
    file_handler = logging.FileHandler(log_file_path, mode="a")
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)
    
    # Console Handler (for debugging)
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger