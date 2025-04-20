
"""Financial scoring functions aggregated from the original notebooks."""

import pandas as pd
import matplotlib.pyplot as plt # type: ignore
import matplotlib.dates as mdates # type: ignore
from modules.utils import safe_divide
import streamlit as st # type: ignore
from modules.data_loader import load_financial_data
from modules.financial_snapshot import build_snapshot

def calculate_piotroski_f_score(row, balance, income, curr, prev):
    net_profit = row["Net Dönem Karı"].values[0]
    operating_cash_flow = row["İşletme Faaliyetlerinden Nakit Akışları"].values[0]
    total_assets = row["Toplam Varlıklar"].values[0]
    f_score = 0
    detail = {}

    detail["Net Kar > 0"] = int(net_profit > 0)
    detail["ROA > 0"] = int((net_profit / total_assets) > 0 if total_assets else 0)
    detail["Nakit Akışı > 0"] = int(operating_cash_flow > 0)
    detail["Nakit Akışı > Net Kar"] = int(operating_cash_flow > net_profit)
    f_score += sum(detail.values())

    snap_curr = build_snapshot(balance, income, None, period=curr)
    snap_prev = build_snapshot(balance, income, None, period=prev)

    if None not in (snap_curr.short_term_liabilities, snap_curr.long_term_liabilities, snap_curr.total_assets, snap_prev.short_term_liabilities, snap_prev.long_term_liabilities, snap_prev.total_assets):
        leverage_ratio_curr = (snap_curr.short_term_liabilities + snap_curr.long_term_liabilities) / snap_curr.total_assets
        leverage_ratio_prev = (snap_prev.short_term_liabilities + snap_prev.long_term_liabilities) / snap_prev.total_assets
        detail["Borç Oranı Azalmış"] = int(leverage_ratio_curr < leverage_ratio_prev)
        f_score += detail["Borç Oranı Azalmış"]
    else:
        detail["Borç Oranı Azalmış"] = 0

    if None not in (snap_curr.current_assets, snap_curr.short_term_liabilities, snap_prev.current_assets, snap_prev.short_term_liabilities):
        snap_curr.current_ratio = snap_curr.current_assets / snap_curr.short_term_liabilities
        snap_prev.current_ratio = snap_prev.current_assets / snap_prev.short_term_liabilities
        detail["Cari Oran Artmış"] = int(snap_curr.current_ratio > snap_prev.current_ratio)
        f_score += detail["Cari Oran Artmış"]
    else:
        detail["Cari Oran Artmış"] = 0

    detail["Öz Kaynak Artmış"] = int(snap_curr.equity >= snap_prev.equity) if snap_curr.equity and snap_prev.equity else 0
    f_score += detail["Öz Kaynak Artmış"]

    if None not in (snap_curr.gross_profit, snap_prev.gross_profit, snap_curr.revenue, snap_prev.revenue):
        detail["Brüt Kar Marjı Artmış"] = int((snap_curr.gross_profit / snap_curr.revenue) > (snap_prev.gross_profit / snap_prev.revenue))
        detail["Varlık Devir Hızı Artmış"] = int((snap_curr.revenue / snap_curr.total_assets) > (snap_prev.revenue / snap_prev.total_assets))
        f_score += detail["Brüt Kar Marjı Artmış"] + detail["Varlık Devir Hızı Artmış"]
    else:
        detail["Brüt Kar Marjı Artmış"] = 0
        detail["Varlık Devir Hızı Artmış"] = 0

    return f_score, detail

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
        print(f"{company} Beneish M-Score hesaplanırken hata: {e}")
        return None

def peter_lynch_score_card(row):
    row = row.iloc[0]
    score = 0
    lines = []

    try:
        market_cap = row.get("Piyasa Değeri")
        operating_cf = row.get("İşletme Faaliyetlerinden Nakit Akışları")
        fcf = row.get("Yıllıklandırılmış Serbest Nakit Akışı")

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


def period_order(period_str):
    try:
        year, month = period_str.split("/")
        return pd.to_datetime(f"{year}-{month}-01")
    except:
        return pd.NaT

def graham_score(row):
    if not row.empty:
        row = row.iloc[0]
    score = 0
    if pd.notnull(row['F/K']) and row['F/K'] < 15:
        score += 1
    if pd.notnull(row['PD/DD']) and row['PD/DD'] < 1.5:
        score += 1
    if pd.notnull(row['Cari Oran']) and 2 < row['Cari Oran'] < 100:
        score += 1
    if pd.notnull(row['İşletme Faaliyetlerinden Nakit Akışları']) and row['İşletme Faaliyetlerinden Nakit Akışları'] > 0:
        score += 1
    if pd.notnull(row['Yıllıklandırılmış Serbest Nakit Akışı']) and row['Yıllıklandırılmış Serbest Nakit Akışı'] > 0:
        score += 1
    return score

def graham_score_card(row):
    row = row.iloc[0]
    score = 0
    lines = []

    kriterler = [
        ("F/K", row.get("F/K"), lambda x: x < 15, "F/K < 15"),
        ("PD/DD", row.get("PD/DD"), lambda x: x < 1.5, "PD/DD < 1.5"),
        ("Cari Oran", row.get("Cari Oran"), lambda x: 2 < x < 100, "2 < Cari Oran < 100"),
        ("Nakit Akışı", row.get("İşletme Faaliyetlerinden Nakit Akışları"), lambda x: x > 0, "İşletme Nakit Akışı > 0"),
        ("Serbest Nakit Akışı", row.get("Yıllıklandırılmış Serbest Nakit Akışı"), lambda x: x > 0, "Yıllıklandırılmış FCF > 0")
    ]

    for label, value, condition, desc in kriterler:
        if pd.notnull(value):
            passed = condition(value)
            lines.append(f"- {label} = {value} → {'✅' if passed else '❌'} ({desc})")
            score += int(passed)
        else:
            lines.append(f"- {label} verisi eksik")

    description = f"Graham Skoru: {score} / 5"
    return score, description, lines


def m_skor_karne_yorum(m_skor):
    if m_skor is None:
        return "M-Skor verisi eksik", ["❌ M-Skor hesaplanamadı"]

    passed = m_skor < -2.22
    yorum = "✅ Düşük risk (finansal manipülasyon ihtimali düşük)" if passed else "⚠️ Yüksek risk (bozulma/makyaj riski)"
    return f"{m_skor:.2f}", [f"M-Skor = {m_skor:.2f} → {yorum}"]


def f_skor_karne_yorum(f_score):
    if f_score is None:
        return "F-Skor verisi eksik"
    
    yorum = f"F-Skor: {f_score} → "
    if f_score >= 7:
        yorum += "✅ Sağlam – Finansal göstergeler güçlü"
    elif 4 <= f_score <= 6:
        yorum += "🟡 Orta seviye – Gelişme sinyalleri izlenmeli"
    else:
        yorum += "❌ Zayıf – Finansal sağlık düşük, temkinli yaklaşılmalı"
    return yorum

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
        print("⛔ Geçersiz piyasa değeri — FCF verimi hesaplanamadı.")
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
    if market_cap.empty or market_cap.values[0] <= 0:
        print("⛔ Piyasa değeri geçersiz.")
        return None
    pdg = market_cap.values[0]

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
    f_score, detail = calculate_piotroski_f_score(row, balance, income, current_period, previous_period)
    f_karne = f_skor_karne_yorum(f_score)

    # 2. Beneish M-Skor
    m_skor = calculate_beneish_m_score(company, balance, income, cashflow, current_period, previous_period)
    m_karne, m_lines = m_skor_karne_yorum(m_skor)

    # 3. Graham Skoru
    graham_skor, graham_karne, graham_lines = graham_score_card(row)

    # 4. Peter Lynch Skoru
    lynch_skor, lynch_karne, lynch_lines = peter_lynch_score_card(row)

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
        "detail": detail
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

    except FileNotFoundError as e:
        st.error(f"⛔ Dosya bulunamadı: {e}")
    except Exception as e:
        st.error(f"⚠️ Hata oluştu: {e}")


