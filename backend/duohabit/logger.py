import logging
from logging.handlers import RotatingFileHandler
import os

# Папка для логов
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Уровень логирования из окружения (по умолчанию INFO)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
numeric_level = getattr(logging, LOG_LEVEL, logging.INFO)

# Основной логгер
logger = logging.getLogger("backend_python")
logger.setLevel(numeric_level)

# Формат логов
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# Файл с ротацией: max 5МБ на файл, хранить до 5 файлов
file_handler = RotatingFileHandler(
    filename=os.path.join(LOG_DIR, "backend_python.log"),
    maxBytes=5*1024*1024,
    backupCount=5,
    encoding="utf-8"
)
file_handler.setLevel(numeric_level)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Вывод в консоль
console_handler = logging.StreamHandler()
console_handler.setLevel(numeric_level)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
