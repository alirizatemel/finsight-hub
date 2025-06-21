"""
Generic scan utilities shared by Financial Radar and Trap Radar.
"""

from datetime import datetime
import numpy as np
import pandas as pd
from typing import Tuple, List, Dict
from modules.data_loader import load_financial_data
from modules.scoring import (
    beneish, graham, lynch, piotroski
)
from modules.scores import (
    monte_carlo_dcf_simple,
    period_order,
    fcf_detailed_analysis
)
from modules.logger import logger 

# ────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────
def latest_common_period(balance: pd.DataFrame,
                         income: pd.DataFrame,
                         cash: pd.DataFrame) -> list[str]:
    bal = {c for c in balance.columns if "/" in c}
    inc = {c for c in income.columns  if "/" in c}
    cf  = {c for c in cash.columns    if "/" in c}
    return sorted(bal & inc & cf, key=period_order, reverse=True)

# ────────────────────────────────────────────────
# Generic scanner
# ────────────────────────────────────────────────
def run_scan(
        radar: pd.DataFrame,
        *,
        forecast_years: int = 5,   # default 5 yıl
        n_sims: int = 1000         # default 1000 simülasyon
) -> Tuple[pd.DataFrame, List[str], Dict]:
    """
    If `forecast_years`+`n_sims` are given, the scan also
    calculates intrinsic value & MOS (Trap_Radar use-case).
    Otherwise it only returns the core F/M/L/G scores
    (Financial Radar use-case).
    """
    records, logs = [], []
    counters = {"dönem": 0, "fcf": 0, "piyasa": 0, "diğer": 0}

    companies = radar["Şirket"].dropna().unique()

    for c in companies:
        try:
            row               = radar[radar["Şirket"] == c]
            
            bal, inc, cash    = load_financial_data(c)
            
            if bal is None or inc is None or cash is None or bal.empty or inc.empty or cash.empty:
                # Teknik loglama için
                logger.warning(f"{c}: Finansal veri setlerinden biri (bilanço, gelir, nakit akış) boş veya eksik. Şirket atlanıyor.")
                # UI'da göstermek için log listesine ekle
                logs.append(f"{c}: Gerekli finansal veri (bilanço/gelir/nakit) bulunamadı, atlandı.")
                counters["diğer"] += 1 # Atlanan şirketleri sayaca ekle
                continue  # Bu şirketi işlemeyi bırak ve döngüde bir sonrakine geç

            periods           = latest_common_period(bal, inc, cash)
            if len(periods) < 2:
                raise ValueError("ortak dönem yok")
            curr, prev        = periods[:2]

            f_score, *_        = piotroski.PiotroskiScorer(row, bal, inc,
                                                          curr, prev).calculate()
            m_score, *_       = beneish.BeneishScorer(c, bal, inc, cash,
                                                     curr, prev).calculate()
            g_score, *_       = graham.GrahamScorer(row).calculate()
            l_score, *_       = lynch.LynchScorer(row).calculate()

            record = {
                "hisse": c,
                "f_skor": f_score,
                "m_skor": m_score,
                "graham": g_score,
                "lynch":  l_score,
            }

            # Optional MOS branch (Trap Radar view)
            if forecast_years and n_sims:
                try:
                    df_fcf   = fcf_detailed_analysis(c, row)
                    if df_fcf is None or df_fcf.empty:
                        raise ValueError("FCF verileri eksik.")

                    ttm_fcf  = (df_fcf["FCF"].iloc[-4:].sum()
                                if len(df_fcf) >= 4 else df_fcf["FCF"].iloc[-1])
                    if ttm_fcf <= 0:
                        raise ValueError("Son FCF negatif.")

                    intrinsic = np.median(
                        monte_carlo_dcf_simple(ttm_fcf,
                                            forecast_years=forecast_years,
                                            n_sims=n_sims)
                    )

                    cur_price   = row.get("Son Fiyat").iat[0]
                    market_cap  = row.get("Piyasa Değeri").iat[0]
                    if cur_price and market_cap and market_cap > 0:
                        shares_out = market_cap / cur_price
                        intrinsic_ps = intrinsic / shares_out
                        premium = (intrinsic_ps - cur_price) / cur_price

                        record.update({
                            "icsel_deger_medyan": intrinsic,    # Güncellendi
                            "piyasa_degeri":      market_cap,   # Güncellendi
                            "MOS":                premium,      # Zaten doğru
                        })
                except Exception as mos_error:
                    logger.warning(f"{c}: MOS hesaplanamadı → {mos_error}")
            
            records.append(record)

        except ValueError as exc:
            msg = str(exc).lower()
            if "dönem" in msg:
                counters["dönem"] += 1
            elif "fcf" in msg:
                counters["fcf"] += 1
            elif "piyasa" in msg:
                counters["piyasa"] += 1
            else:
                counters["diğer"] += 1
            
            logger.warning(f"{c}: {exc}")
            logs.append(f"{c}: {exc}")
        except Exception as exc:
            counters["diğer"] += 1
            logger.warning(f"{c}: {exc}")
            logs.append(f"{c}: {exc}")

    df = pd.DataFrame(records)

    if not df.empty:
        df["timestamp"] = datetime.now()
        # Yeni kolon adları ile güncellendi
        for col in ["MOS", "icsel_deger_medyan", "piyasa_degeri"]:
            if col not in df.columns:
                df[col] = np.nan  # eksikse bile tüm satırlara NaN olarak ekle

    if not df.empty:
        df["timestamp"] = datetime.now()
    if "MOS" in df.columns:
        df.sort_values("MOS", ascending=False, inplace=True)

    return df, logs, counters
