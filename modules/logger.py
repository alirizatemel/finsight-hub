# modules/logger.py
import logging
import os

LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "scanner.log")

# logger nesnesini oluştur
logger = logging.getLogger("radar_scanner")
logger.setLevel(logging.INFO)

# log formatı
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

# dosya handler
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# terminale de yaz (opsiyonel)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# tekrar log eklenmesini engelle
logger.propagate = False
