from pathlib import Path

# Ana dizin (config.py'nin bulunduğu yere göre ayarlanır)
BASE_DIR = Path(__file__).resolve().parent

# Verilerin tutulduğu dizin
DATA_DIR = BASE_DIR / "data"
COMPANIES_DIR = DATA_DIR / "companies"
DOWNLOADS_DIR = BASE_DIR / "downloads"

# Örnek veri dosyası yolu
SON_BILANCOLAR_JSON = DATA_DIR / "son_bilancolar.json"

RADAR_XLSX = DATA_DIR / "fintables_radar.xlsx"

PERIODS = [
    "2023/12",
    "2023/09",
    "2023/06",
    "2023/03",
    "2022/12",
    "2022/09",
]
