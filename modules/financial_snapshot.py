# financial_snapshot.py
from dataclasses import dataclass
from typing import Optional
import pandas as pd
from modules.utils import get_value   # mevcut yardımcı işleviniz
# ------------------------------------------------------------

@dataclass
class FinancialSnapshot:
    # ---------- Balance‑sheet ----------
    short_term_liabilities:    Optional[float] = None   # Toplam Kısa Vadeli Yükümlülükler
    long_term_liabilities:     Optional[float] = None   # Toplam Uzun Vadeli Yükümlülükler
    total_liabilities:         Optional[float] = None   # (short + long)  – otomatik dolduruyoruz
    total_assets:              Optional[float] = None   # Toplam Varlıklar
    current_assets:            Optional[float] = None   # Toplam Dönen Varlıklar
    equity:                    Optional[float] = None   # Ana Ortaklığa Ait Özkaynaklar
    pp_e:                      Optional[float] = None   # Maddi Duran Varlıklar
    trade_receivables:         Optional[float] = None   # Ticari Alacaklar

    # ---------- Income‑statement ----------
    sales:                     Optional[float] = None   # Satış Gelirleri
    cogs:                      Optional[float] = None   # Satışların Maliyeti (-)
    gross_profit:              Optional[float] = None   # Brüt Kar
    g_and_a_exp:               Optional[float] = None   # Genel Yönetim Giderleri (-)
    marketing_exp:             Optional[float] = None   # Pazarlama / Satış / Dağıtım Giderleri (-)
    revenue:                   Optional[float] = None   # Toplam Hasılat

    # ---------- Cash‑flow ----------
    operating_cash_flow:              Optional[float] = None   # İşletme Faaliyetlerinden Nakit Akışları
    depreciation:              Optional[float] = None   # Amortisman ve İtfa Düzeltmeleri
    net_profit:                Optional[float] = None   # Dönem Karı (Zararı)


def build_snapshot(balance_df, income_df, cashflow_df: Optional[pd.DataFrame] = None, *, period: str) -> FinancialSnapshot:
    """
    Tüm kalemleri tek seferde okuyup FinancialSnapshot döndürür.
    `period` => '2024/12' formatında dönem etiketi.
    """

    # -------- Balance ----------
    short = get_value(balance_df, "Toplam Kısa Vadeli Yükümlülükler", period)
    long  = get_value(balance_df, "Toplam Uzun Vadeli Yükümlülükler",  period)

    snapshot = FinancialSnapshot(
        # Balance
        short_term_liabilities = short,
        long_term_liabilities  = long,
        total_liabilities      = (short or 0) + (long or 0) if None not in (short, long) else None,
        total_assets           = get_value(balance_df, "Toplam Varlıklar",         period),
        current_assets         = get_value(balance_df, "Toplam Dönen Varlıklar",   period),
        equity                 = get_value(balance_df, "Ana Ortaklığa Ait Özkaynaklar", period),
        pp_e                   = get_value(balance_df, "Maddi Duran Varlıklar",    period),
        trade_receivables      = get_value(balance_df, "Ticari Alacaklar",         period),

        # Income
        sales                  = get_value(income_df, "Satış Gelirleri",           period),
        cogs                   = get_value(income_df, "Satışların Maliyeti (-)",   period),
        gross_profit           = get_value(income_df,
                                           ["Brüt Kar (Zarar)",
                                            "Ticari Faaliyetlerden Brüt Kar (Zarar)"], period),
        g_and_a_exp            = get_value(income_df, "Genel Yönetim Giderleri (-)", period),
        marketing_exp          = get_value(income_df, "Pazarlama, Satış ve Dağıtım Giderleri (-)", period),
        revenue                = get_value(income_df, "Toplam Hasılat",            period),

        # Cash‑flow
        operating_cash_flow = (
            get_value(cashflow_df, "İşletme Faaliyetlerinden Nakit Akışları", period)
            if cashflow_df is not None else None
        ),
        depreciation = (
            get_value(cashflow_df, "Amortisman ve İtfa Gideri İle İlgili Düzeltmeler", period)
            if cashflow_df is not None else None
        ),
        net_profit   = (
            get_value(cashflow_df, "Dönem Karı (Zararı)", period)
            if cashflow_df is not None else None
        ),
    )

    return snapshot
