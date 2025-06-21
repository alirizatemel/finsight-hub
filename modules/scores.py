
"""Financial scoring functions aggregated from the original notebooks."""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt # type: ignore
import matplotlib.dates as mdates # type: ignore
from modules.utils import safe_divide, safe_float, scalar
import streamlit as st # type: ignore
from typing import Optional 
from modules.data_loader import load_financial_data
from modules.financial_snapshot import build_snapshot
from modules.ratios import calculate_roa_ttm
from modules.scoring.beneish import BeneishScorer
from modules.scoring.graham import GrahamScorer
from modules.scoring.lynch import LynchScorer
from modules.scoring.piotroski import PiotroskiScorer
from modules.logger import logger 

def monte_carlo_dcf_simple(
    last_fcf: float,
    forecast_years: int = 5,
    n_sims: int = 10_000,
    wacc_mu: float = 0.15, wacc_sigma: float = 0.03,
    g_mu: float = 0.04,  g_sigma: float = 0.01,
    seed: Optional[int] = 42, 
) -> np.ndarray:
    """
    Vectorised Monte-Carlo DCF (PV of explicit FCFs + Gordon terminal value).

    IMPORTANT fixes
    • Guarantees WACC > g and WACC > 0.
    • Caps g at −5 % (conservative) and 15 %.  
    • Discounts the terminal value N years (not N+1).  
    • Returns np.ndarray of intrinsic values (length = n_sims).
    """
    if seed is not None:
        np.random.seed(seed)

    # --- draw parameters ----------------------------------------------------
    waccs = np.clip(np.random.normal(wacc_mu, wacc_sigma, n_sims), 0.01, None)
    gs    = np.random.normal(g_mu,  g_sigma,  n_sims)

    # make sure all scenarios satisfy 0 % ≤ g < WACC – 1 pt
    bad = (gs >= waccs - 0.01) | (gs < -0.05) | (gs > 0.15)
    while bad.any():
        waccs[bad] = np.clip(
            np.random.normal(wacc_mu, wacc_sigma, bad.sum()), 0.01, None
        )
        gs[bad] = np.random.normal(g_mu, g_sigma, bad.sum())
        bad = (gs >= waccs - 0.01) | (gs < -0.05) | (gs > 0.15)

    # --- explicit-period FCFs ----------------------------------------------
    years          = np.arange(1, forecast_years + 1)                      # 1..N
    growth_matrix  = (1 + gs[:, None]) ** years
    fcf_matrix     = last_fcf * growth_matrix                              # shape (n_sims, N)
    discount       = (1 + waccs[:, None]) ** years
    pv_fcfs        = (fcf_matrix / discount).sum(axis=1)

    # --- terminal value (PV at t = 0) ---------------------------------------
    fcf_N1   = last_fcf * (1 + gs) ** (forecast_years) * (1 + gs)          # FCFₙ₊₁
    tv       = fcf_N1 / (waccs - gs)
    pv_tv    = tv / (1 + waccs) ** forecast_years

    return pv_fcfs + pv_tv

def period_order(period_str):
    try:
        year, month = period_str.split("/")
        return pd.to_datetime(f"{year}-{month}-01")
    except:
        return pd.NaT

def fcf_yield_time_series(company, row):
    try:
        _, _, cashflow_df = load_financial_data(company)
        cashflow_df = cashflow_df.set_index("Kalem")

        if "İşletme Faaliyetlerinden Nakit Akışları" not in cashflow_df.index:
            st.warning("⛔ İşletme nakit akışı verisi bulunamadı.")
            return

        # OFCF + CAPEX → FCF hesapla
        ofcf = cashflow_df.loc["İşletme Faaliyetlerinden Nakit Akışları"]

        if "Maddi ve Maddi Olmayan Duran Varlık Alımları" in cashflow_df.index:
            capex = cashflow_df.loc["Maddi ve Maddi Olmayan Duran Varlık Alımları"]
        elif "Yatırım Faaliyetlerinden Kaynaklanan Nakit Akışları" in cashflow_df.index:
            capex = cashflow_df.loc["Yatırım Faaliyetlerinden Kaynaklanan Nakit Akışları"]
        else:
            st.warning("⛔ Yatırım harcamaları (CAPEX) verisi eksik.")
            return

        fcf_series = ofcf - capex

        # Piyasa değeri
        try:
            market_cap = pd.to_numeric(row["Piyasa Değeri"], errors="coerce").squeeze()
            if pd.isna(market_cap) or market_cap <= 0:
                st.warning("⛔ Geçersiz piyasa değeri.")
                return
        except Exception as e:
            st.warning(f"⛔ Piyasa değeri okunamadı: {e}")
            return

        # FCF verimi
        fcf_yield = (fcf_series / market_cap * 100).dropna()
        fcf_yield = fcf_yield.loc[~fcf_yield.index.duplicated()]
        sorted_idx = sorted(fcf_yield.index, key=period_order)
        fcf_yield = fcf_yield[sorted_idx]

        # Grafik çizimi
        fig, ax = plt.subplots(figsize=(10, 5))
        x = [period_order(p) for p in fcf_yield.index]
        y = fcf_yield.values

        ax.plot(x, y, marker="o", linestyle="-", label="FCF Verimi (%)", color="tab:blue")
        ax.fill_between(x, 0, y, alpha=0.1, color="tab:blue")

        ax.set_title(f"{company} – FCF Verimi Zaman Serisi")
        ax.set_ylabel("FCF Verimi (%)")
        ax.set_xlabel("Dönem")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()

        st.pyplot(fig)

    except Exception as e:
        st.error(f"⚠️ {company} için grafik oluşturulamadı: {e}")

def fcf_detailed_analysis(company, row):
    # 1) Excel verilerini oku
    _, income_df, cashflow_df = load_financial_data(company)

    income_df = income_df.set_index("Kalem")
    cashflow_df = cashflow_df.set_index("Kalem")

    # 3) Temel seriler
    sales_series        = income_df.loc["Satış Gelirleri"]
    net_profit_series   = cashflow_df.loc["Dönem Karı (Zararı)"]
    operating_cf_series = cashflow_df.loc["İşletme Faaliyetlerinden Nakit Akışları"]

    # 4) CAPEX seçimi
    if "Maddi ve Maddi Olmayan Duran Varlık Alımları" in cashflow_df.index:
        capex_series = cashflow_df.loc["Maddi ve Maddi Olmayan Duran Varlık Alımları"]
    elif "Yatırım Faaliyetlerinden Kaynaklanan Nakit Akışları" in cashflow_df.index:
        capex_series = cashflow_df.loc["Yatırım Faaliyetlerinden Kaynaklanan Nakit Akışları"]
    else:
        raise ValueError("CAPEX verisi bulunamadı.")

    # 5) FCF ve FCF verimi
    fcf_series   = operating_cf_series - capex_series
    market_cap   = (pd.to_numeric(row["Piyasa Değeri"], errors="coerce").squeeze())
    if pd.isna(market_cap) or market_cap <= 0:
        logger.exception("⛔ Geçersiz piyasa değeri — FCF verimi hesaplanamadı.")
        return None
    fcf_yield = (fcf_series / market_cap * 100).dropna()

    # 6) DataFrame oluştur (dönemler index)
    df = pd.DataFrame({
        "Satışlar"              : sales_series,
        "Net Kâr"              : net_profit_series,
        "Faaliyet Nakit Akışı" : operating_cf_series,
        "CAPEX"                : capex_series,
        "FCF"                  : fcf_series,
        "FCF Verimi (%)"       : fcf_yield,
    })

    # 7) Dönemleri kronolojik sıraya koy
    df = df.loc[sorted(df.index, key=period_order)]

    return df

def fcf_detailed_analysis_plot(company, row):
    # Excel verisini oku
    _, income_df, cashflow_df = load_financial_data(company)

    income_df = income_df.set_index("Kalem")
    cashflow_df = cashflow_df.set_index("Kalem")

    # Verileri çek
    sales_series = income_df.loc["Satış Gelirleri"]
    net_profit = cashflow_df.loc["Dönem Karı (Zararı)"]
    operating_cf_series = cashflow_df.loc["İşletme Faaliyetlerinden Nakit Akışları"]

    # CAPEX kontrolü
    if "Maddi ve Maddi Olmayan Duran Varlık Alımları" in cashflow_df.index:
        capex_series = cashflow_df.loc["Maddi ve Maddi Olmayan Duran Varlık Alımları"]
    elif "Yatırım Faaliyetlerinden Kaynaklanan Nakit Akışları" in cashflow_df.index:
        capex_series = cashflow_df.loc["Yatırım Faaliyetlerinden Kaynaklanan Nakit Akışları"]
    else:
        raise ValueError("CAPEX verisi bulunamadı.")

    # FCF ve FCF Verimi
    fcf_series = operating_cf_series - capex_series

    market_cap = row['Piyasa Değeri']
    if market_cap.empty or scalar(market_cap) <= 0:
        logger.exception("⛔ Piyasa değeri geçersiz.")
        return None
    pdg = scalar(market_cap)

    fcf_yield = (fcf_series / pdg * 100).dropna()

    # Tablolaştır
    df = pd.DataFrame({
        "Satışlar": sales_series,
        "Net Kar": net_profit,
        "Faaliyet Nakit Akışı": operating_cf_series,
        "CAPEX": capex_series,
        "FCF": fcf_series,
        "FCF Verimi (%)": fcf_yield
    }).T

    # Dönemleri sırala
    df = df.T
    df = df.sort_index(key=lambda x: [period_order(d) for d in x])
    df.index = pd.to_datetime(df.index, format="%Y/%m", errors="coerce")

    df_ma = df.rolling(3).mean()

    # Grafik çizimi
    x = df.index
    fig, axes = plt.subplots(5, 1, figsize=(14, 16), sharex=True)

    for i, (kolon, renk, ma_renk) in enumerate([
        ("Satışlar", "tab:blue", "tab:cyan"),
        ("Net Kar", "tab:green", "lime"),
        ("FCF", "tab:purple", "violet"),
        ("CAPEX", "tab:orange", "gold"),
        ("FCF Verimi (%)", "tab:red", "tomato"),
    ]):
        y = df[kolon] / (1e9 if "Verimi" not in kolon else 1)
        y_ma = df_ma[kolon] / (1e9 if "Verimi" not in kolon else 1)

        axes[i].plot(x, y, linestyle='-', marker='o', color=renk, label=kolon)
        axes[i].plot(x, y_ma, linestyle='--', color=ma_renk, label="Hareketli Ortalama")
        axes[i].fill_between(x, 0, y, alpha=0.1, color=renk)
        axes[i].set_ylabel(kolon + ("\n(Milyar TL)" if "Verimi" not in kolon else ""))
        axes[i].legend()
        axes[i].grid(True)

    axes[-1].set_xlabel("Tarih")
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    fig.suptitle(f"{company} | FCF Odaklı Finansal Analiz", fontsize=16)
    plt.xticks(rotation=45)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # Artık show() değil, Streamlit ile gösterim:
    st.pyplot(fig)

def calculate_scores(company, row, balance, income, cashflow, current_period, previous_period):
    # 1. Piotroski F-Skor
    f_score, f_karne, f_detail = PiotroskiScorer(row, balance, income, current_period, previous_period).calculate()

    # 2. Beneish M-Skor
    m_skor, m_karne, m_lines  = BeneishScorer(company, balance, income, cashflow, current_period, previous_period).calculate()

    # 3. Graham Skoru
    graham_skor, graham_karne, graham_lines = GrahamScorer(row).calculate()

    # 4. Peter Lynch Skoru
    lynch_skor, lynch_karne, lynch_lines = LynchScorer(row).calculate()

    return {
        "f_score": f_score,
        "f_karne": f_karne,
        "m_skor": m_skor,
        "m_karne": m_karne,
        "m_lines": m_lines,
        "graham_skor": graham_skor,
        "graham_karne": graham_karne,
        "graham_lines": graham_lines,
        "lynch_skor": lynch_skor,
        "lynch_karne": lynch_karne,
        "lynch_lines": lynch_lines,
        "detail": f_detail
    }

def generate_report(company, scores, show_details=False):
    """Skor nesnesinden okunabilir bir metin raporu üret."""
    lines = [
        f"📌 Şirket: {company}",
        f"Piotroski F-Skor: {scores['f_karne']}",
        f"Beneish M-Skor: {scores['m_karne']}",
        f"Graham Skoru: {scores['graham_skor']}",
        f"Peter Lynch Skoru: {scores['lynch_skor']}",
        ""
    ]

    if show_details:
        lines.append("🔍 F-Skor Detayları:")
        for k, v in scores.get("detail", {}).items():
            lines.append(f"- {k}: {v}")

    lines.append("\n🧾 Graham Karne:")
    lines.append(scores.get("graham_karne", "-"))

    lines.append("\n🧾 Lynch Karne:")
    lines.append(scores.get("lynch_karne", "-"))

    return lines

def show_company_scorecard(company, row, current_period, previous_period):
    """Tüm süreci birleştirip skor kartını ekrana bas."""
    try:
        balance, income, cashflow = load_financial_data(company)
        scores = calculate_scores(
            company,
            row,
            balance,
            income,
            cashflow,
            current_period,
            previous_period,
        )

        # === Genel Başlık ===
        st.subheader(f"📌 Şirket: {company}")

        # === Ana Skorlar ===
        # === F-Detayları  ===
        st.markdown(f"**Piotroski F-Skor:** {scores['f_karne']}")
        with st.expander("🧾 F-Skor Detayları", expanded=False):
            for k, v in scores.get("detail", {}).items():
                st.markdown(f"- {k}: {v}")
        
        # === M-Skor Detayları ===
        st.markdown(f"**Beneish M-Skor:** {scores['m_karne']}")
        with st.expander("🧾 Beneish M‑Skor Yorumu", expanded=False):
            for line in scores.get("m_lines", []):
                st.markdown(line)
        
        # === Graham Karne ===
        st.markdown(f"**Graham Skoru:** {scores['graham_skor']} / 5")
        with st.expander("🧾 Graham Kriterleri", expanded=False):
            for line in scores.get("graham_lines", []):
                st.markdown(line)

        # === Peter Lynch Karne ===
        st.markdown(f"**Peter Lynch Skoru:** {scores['lynch_skor']} / 3")
        with st.expander("🧾 Peter Lynch Kriterleri", expanded=False):
            for line in scores.get("lynch_lines", []):
                st.markdown(line)
        return {
            "company": company,
            "periods": {
                "current": current_period,
                "previous": previous_period,
            },
            "scores": {
                "piotroski": scores["f_score"],
                "piotroski_card": scores["f_karne"],
                "piotroski_detail": scores.get("detail", {}),
                "beneish": scores["m_skor"],
                "beneish_card": scores["m_karne"],
                "beneish_lines": scores.get("m_lines", []),
                "graham": scores["graham_skor"],
                "graham_lines": scores.get("graham_lines", []),
                "lynch": scores["lynch_skor"],
                "lynch_lines": scores.get("lynch_lines", []),
            }
        }
    except FileNotFoundError as e:
        st.error(f"⛔ Dosya bulunamadı: {e}")
    except Exception as e:
        st.error(f"⚠️ Hata oluştu: {e}")

def monte_carlo_dcf_jump_diffusion(
    last_fcf,
    forecast_years=5,
    n_sims=10000,
    wacc_mu=0.15,
    g_mu=0.04,
    mu=0.10,
    sigma=0.25,
    lambda_=0.1,       # sıçrama yoğunluğu
    jump_mu=0.05,      # ortalama sıçrama büyüklüğü
    jump_sigma=0.10    # sıçrama oynaklığı
):
    results = []
    for _ in range(n_sims):
        fcf = last_fcf
        cashflows = []
        for t in range(1, forecast_years + 1):
            growth = np.random.normal(mu, sigma)
            jump_occurs = np.random.poisson(lambda_)
            jump = jump_occurs * np.random.normal(jump_mu, jump_sigma)
            fcf *= (1 + growth + jump)
            cashflows.append(fcf / ((1 + wacc_mu) ** t))
        terminal = fcf * (1 + g_mu) / (wacc_mu - g_mu)
        cashflows.append(terminal / ((1 + wacc_mu) ** forecast_years))
        results.append(sum(cashflows))
    return results
