import numpy as np
import pandas as pd

# ------------------------------------------------------------------
#  Güvenli hücre erişimi: Series   -> ilk eleman
#                        ndarray   -> ilk eleman
#                        skalar    -> aynen
# ------------------------------------------------------------------
def scalar(x):
    if isinstance(x, (pd.Series, np.ndarray)):
        return x.iloc[0] if isinstance(x, pd.Series) else x[0]
    return x

# ---------------------------------------------------------------
#  Yardımcı: boş veya NaN → np.nan, aksi hâlde skalar değer döner
# ---------------------------------------------------------------
def safe_float(x):
    x = scalar(x)
    return np.nan if pd.isna(x) else float(x)
# ---------------------------------------------------------------

def safe_divide(numerator, denominator):
    if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
        return 0
    return numerator / denominator

def get_value(df, kalem_adlari, kolon):
    """
    Gerekli kalemi bulur. Eğer 'Hasılat' aranıyorsa, Yurt İçi + Yurt Dışı şeklinde toplar.
    """
    if isinstance(kalem_adlari, str):
        kalem_adlari = [kalem_adlari]

    df["Kalem"] = df["Kalem"].astype(str).str.strip()

    for kalem in kalem_adlari:
        if kalem == "Toplam Hasılat":
            # Özel durum: Yurt İçi + Yurt Dışı
            ic = df[df["Kalem"] == "Yurt İçi Satışlar"][kolon]
            dis = df[df["Kalem"] == "Yurt Dışı Satışlar"][kolon]
            toplam = 0
            if not ic.empty:
                toplam += ic.values[0]
            if not dis.empty:
                toplam += dis.values[0]
            if toplam > 0:
                return toplam

        value = df[df["Kalem"] == kalem][kolon]
        if not value.empty:
            return value.values[0]

    return 0

def period_order(period_str):
    try:
        year, month = period_str.split("/")
        return pd.to_datetime(f"{year}-{month}-01")
    except:
        return pd.NaT

