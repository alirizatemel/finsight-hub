import numpy as np

def safe_divide(numerator, denominator):
    if denominator in [0, None, np.nan] or numerator in [None, np.nan]:
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



