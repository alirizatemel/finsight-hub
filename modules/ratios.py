import pandas as pd
from modules.utils import scalar
from modules.financial_snapshot import build_snapshot
from modules.logger import logger 

def calculate_roa_ttm(income: pd.DataFrame, balance: pd.DataFrame, period_order_fn) -> float:
    """
    Adım adım loglayarak Yıllıklandırılmış ROA hesapla:
    ROA = (TTM Net Kar) / (Ortalama Toplam Varlık) * 100

    Returns:
        float: Yüzde olarak ROA (örn: -4.92)
    """
    try:
        # 1️⃣ Geçerli ortak dönemleri sırala
        valid_periods = sorted(
            [c for c in income.columns if "/" in c and c in balance.columns],
            key=period_order_fn,
            reverse=True
        )

        # 2️⃣ Net Kar verilerini topla
        net_incomes = []
        for p in valid_periods[:4]:
            snap_curr = build_snapshot(balance, income, None, period=p)
            val = scalar(snap_curr.net_profit)
            net_incomes.append(val or 0)

        net_income_ttm = sum(net_incomes)

        # 3️⃣ Toplam Varlık verilerini al (2 dönem)
        assets = []
        for p in valid_periods[:4]:
            snap_curr = build_snapshot(balance, income, None, period=p)
            val = scalar(snap_curr.total_assets)
            assets.append(val or 0)

        if all(a > 0 for a in assets):
            avg_assets = sum(assets) / 4
        else:
            avg_assets = None

        # 4️⃣ ROA hesapla
        roa = (net_income_ttm / avg_assets) * 100 if avg_assets else 0
        return roa

    except Exception as e:
        logger.exception("🚨 ROA TTM hesaplama hatası:", e)
        return 0


