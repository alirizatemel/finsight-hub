import re
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from selenium import webdriver # type: ignore
from selenium.webdriver.chrome.options import Options # type: ignore
from selenium.webdriver.common.by import By # type: ignore
from selenium.webdriver.support.ui import WebDriverWait # type: ignore
from selenium.webdriver.support import expected_conditions as EC # type: ignore
from modules.logger import logger 


from config import COMPANIES_DIR, SON_BILANCOLAR_JSON, DOWNLOADS_DIR

TARGET_PERIOD = "2025/3"
PERIOD_RE = re.compile(r"^\d{4}/\d{1,2}$")     # 2025/3, 2024/12 vb.

def is_bilanco_outdated(excel_path: Path, target: str = TARGET_PERIOD) -> bool:
    """
    Dosya yoksa - veya - içindeki son dönem TARGET_PERIOD değilse True döner.
    """
    if not excel_path.exists():
        return True

    try:
        # Sadece başlık satırını oku – satırlara gerek yok
        cols = pd.read_excel(excel_path, sheet_name="Bilanço", nrows=0).columns
        # “Kalem”, “Unnamed: …”, boş hücreleri ve hedef regex’e uymayanları at
        period_cols = [
            str(c).strip()
            for c in cols
            if PERIOD_RE.match(str(c).strip())
        ]
        if not period_cols:
            # Hiç dönem sütunu bulunamadıysa dosya bozuk say
            return True

        latest_period = period_cols[0]   # En soldaki = en yeni
        return latest_period != target
    except Exception as e:
        logger.exception(f"⚠️ {excel_path.name} okunamadı: {e}")
        return True

def configure_driver():
    options = Options()
    options.add_argument(r"user-data-dir=C:\selenium_data")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")
    options.add_experimental_option("prefs", {
        "download.default_directory": str(DOWNLOADS_DIR),
        "download.prompt_for_download": False,
        "safebrowsing.enabled": True
    })
    return webdriver.Chrome(options=options)

def download_excel_for(ticker: str, driver, log, max_retry: int = 1):
    url = f"https://fintables.com/sirketler/{ticker}/finansal-tablolar/bilanco"

    for attempt in range(max_retry + 1):
        driver.get(url) if attempt == 0 else driver.refresh()
        try:
            WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//div[contains(text(), \"Excel'e Aktar\")]")
                )
            ).click()

            time.sleep(4)  # indirme tamamlanma payı
            src = DOWNLOADS_DIR / f"{ticker} (TRY).xlsx"
            if src.exists():
                dst_dir = COMPANIES_DIR / ticker
                dst_dir.mkdir(parents=True, exist_ok=True)
                src.replace(dst_dir / src.name)
                log(f"✅ {ticker} güncellendi.")
                return
            else:
                log(f"⚠️ {ticker}: Dosya inmedi (deneme {attempt+1}).")
        except Exception as e:
            log(f"❌ {ticker}: Buton bulunamadı (deneme {attempt+1}) – {e}")

    log(f"🚫 {ticker}: Tüm denemeler başarısız.")


def update_companies_if_needed(log=lambda msg: None):
    with open(SON_BILANCOLAR_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data).rename(columns={"code": "Şirket"})
    tickers = df["Şirket"].unique()

    driver = configure_driver()
    for ticker in tickers:
        path = COMPANIES_DIR / ticker / f"{ticker} (TRY).xlsx"
        if is_bilanco_outdated(path):
            log(f"🔄 {ticker} indiriliyor (veri eski veya eksik)…")
            download_excel_for(ticker, driver, log)
        else:
            log(f"⏩ {ticker} verisi güncel.")
    driver.quit()
