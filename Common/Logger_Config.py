import logging
from colorama import init, Fore, Style

# Auto-reset color after each print
init(autoreset=True)

class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.ERROR: Fore.RED,
        logging.WARNING: Fore.YELLOW,
        logging.INFO: Fore.CYAN,
        logging.DEBUG: Fore.GREEN
    }

    def format(self, record):
        color = self.COLORS.get(record.levelno, "")
        record.levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)

def setup_logger():
    formatter = ColorFormatter("%(levelname)s: %(message)s")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.addHandler(handler)

    return logger

logging = setup_logger()
