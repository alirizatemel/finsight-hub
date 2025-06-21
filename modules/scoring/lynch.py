import pandas as pd
from modules.utils import safe_float

def peter_lynch_score_card(row):
    row = row.iloc[0]
    score = 0
    lines = []

    try:
        market_cap = safe_float(row.get("Piyasa Değeri"))
        operating_cf = safe_float(row.get("İşletme Faaliyetlerinden Nakit Akışları"))
        fcf = safe_float(row.get("Yıllıklandırılmış Serbest Nakit Akışı"))

        # FCF Verimi
        if pd.notnull(fcf) and pd.notnull(market_cap) and market_cap > 0:
            fcf_yield = fcf / market_cap
            passed = fcf_yield >= 0.05
            lines.append(f"- FCF Verimi: {fcf_yield:.2%} → {'✅ Güçlü' if passed else '❌ Zayıf'}")
            score += int(passed)
        else:
            lines.append("- FCF veya piyasa değeri eksik")

        # Nakit Akışı
        if pd.notnull(operating_cf):
            passed = operating_cf > 0
            lines.append(f"- İşletme Nakit Akışı: {operating_cf:.0f} → {'✅ Pozitif' if passed else '❌ Negatif'}")
            score += int(passed)
        else:
            lines.append("- İşletme Nakit Akışı eksik")

        # PD/FCF
        if pd.notnull(market_cap) and pd.notnull(fcf) and fcf > 0:
            pd_fcf = market_cap / fcf
            passed = pd_fcf <= 15
            lines.append(f"- PD/FCF = {pd_fcf:.1f} → {'✅ Ucuz' if passed else '❌ Pahalı'}")
            score += int(passed)
        else:
            lines.append("- PD/FCF hesaplanamıyor")

    except Exception as e:
        lines.append(f"⚠️ Hata: {e}")

    description = f"Peter Lynch Skoru: {score} / 3"
    return score, description, lines



class LynchScorer:
    def __init__(self, row):
        self.row = row

    def calculate(self):

        l_score, summary, lines = peter_lynch_score_card(self.row)
        return l_score, summary, lines