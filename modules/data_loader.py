
import pandas as pd
from pathlib import Path
from config import COMPANIES_DIR

def load_financial_data(symbol: str, base_dir: Path = Path(COMPANIES_DIR)):
    """Load Bilanço, Gelir Tablosu (Çeyreklik) and Nakit Akış (Çeyreklik) sheets for a ticker."""
    path = base_dir / f"{symbol} (TRY).xlsx"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    bilanco  = pd.read_excel(path, sheet_name="Bilanço")
    gelir    = pd.read_excel(path, sheet_name="Gelir Tablosu (Çeyreklik)")
    cashflow = pd.read_excel(path, sheet_name="Nakit Akış (Çeyreklik)")

    for df in (bilanco, gelir, cashflow):
        df['Kalem'] = df['Kalem'].astype(str).str.strip()

    return bilanco, gelir, cashflow

