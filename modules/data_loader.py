
import pandas as pd
from pathlib import Path

def load_financial_data(symbol: str, base_dir: Path = Path("companies")):
    """Load Bilanço, Gelir Tablosu (Dönemsel) and Nakit Akış (Dönemsel) sheets for a ticker."""
    path = base_dir / symbol / f"{symbol} (TRY).xlsx"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    bilanco  = pd.read_excel(path, sheet_name="Bilanço")
    gelir    = pd.read_excel(path, sheet_name="Gelir Tablosu (Dönemsel)")
    cashflow = pd.read_excel(path, sheet_name="Nakit Akış (Dönemsel)")

    for df in (bilanco, gelir, cashflow):
        df['Kalem'] = df['Kalem'].astype(str).str.strip()

    return bilanco, gelir, cashflow
