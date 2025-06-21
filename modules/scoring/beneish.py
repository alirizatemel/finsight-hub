from modules.utils import safe_divide
from modules.financial_snapshot import build_snapshot
from modules.logger import logger

def calculate_beneish_m_score(company, balance, income, cashflow, curr, prev):
    try:
        #Gerekli kalemleri al
        snap_curr = build_snapshot(balance, income, cashflow, period=curr)
        snap_prev = build_snapshot(balance, income, cashflow, period=prev)

        # 1. DSRI
        DSRI = safe_divide(safe_divide(snap_curr.trade_receivables, snap_curr.sales), safe_divide(snap_prev.trade_receivables, snap_prev.sales))
        
        # 2. GMI
        GMI = safe_divide(safe_divide(snap_prev.sales - snap_prev.cogs, snap_prev.sales),
                          safe_divide(snap_curr.sales - snap_curr.cogs, snap_curr.sales))
        
        # 3. AQI
        aqi_curr = 1 - safe_divide(snap_curr.current_assets + snap_curr.pp_e, snap_curr.total_assets)
        aqi_prev = 1 - safe_divide(snap_prev.current_assets + snap_prev.pp_e, snap_prev.total_assets)
        AQI = safe_divide(aqi_curr, aqi_prev)

        # 4. SGI
        SGI = safe_divide(snap_curr.sales, snap_prev.sales)
        
        # 5. DEPI
        depi_curr = safe_divide(snap_curr.depreciation, snap_curr.depreciation + snap_curr.pp_e)
        depi_prev = safe_divide(snap_prev.depreciation, snap_prev.depreciation + snap_prev.pp_e)
        DEPI = safe_divide(depi_prev, depi_curr)
         
        # 6. SGAI
        sgai_numerator = safe_divide((snap_curr.g_and_a_exp + snap_curr.marketing_exp), snap_curr.sales)
        sgai_denominator = safe_divide((snap_prev.g_and_a_exp + snap_prev.marketing_exp), snap_prev.sales)
        SGAI = safe_divide(sgai_numerator, sgai_denominator)

        
        # 7. TATA
        TATA = safe_divide(snap_curr.net_profit - snap_curr.operating_cash_flow, snap_curr.total_assets) if None not in (
            snap_curr.net_profit, snap_curr.operating_cash_flow, snap_curr.total_assets) else 0
        
        # 8. LVGI
        LVGI = safe_divide(snap_curr.total_liabilities / snap_curr.total_assets, snap_prev.total_liabilities / snap_prev.total_assets)

        m_score = (
            -4.84 + 0.92 * DSRI + 0.528 * GMI + 0.404 * AQI + 0.892 * SGI +
            0.115 * DEPI - 0.172 * SGAI + 4.679 * TATA - 0.327 * LVGI
        )

        return round(m_score, 2)

    except Exception as e:
        logger.exception(f"{company} Beneish M-Score hesaplanırken hata: {e}")
        return None

def m_skor_karne_yorum(m_skor):
    if m_skor is None:
        return "M-Skor verisi eksik", ["❌ M-Skor hesaplanamadı"]

    passed = m_skor < -2.22
    yorum = "✅ Düşük risk (finansal manipülasyon ihtimali düşük)" if passed else "⚠️ Yüksek risk (bozulma/makyaj riski)"
    return f"{m_skor:.2f}", [f"M-Skor = {m_skor:.2f} → {yorum}"]
   
class BeneishScorer:
    def __init__(self, company, balance, income, cashflow, curr, prev):
        self.company = company
        self.balance = balance
        self.income = income
        self.cashflow = cashflow
        self.curr = curr
        self.prev = prev

    def calculate(self):
        m_score = calculate_beneish_m_score(
            self.company, self.balance, self.income, self.cashflow, self.curr, self.prev
        )
        karne, lines = m_skor_karne_yorum(m_score)
        
        return m_score, karne, lines
