
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
    card = []

    try:
        # Gerekli değişkenler
        market_cap = row['Piyasa Değeri']
        operating_cash_flow = row['İşletme Faaliyetlerinden Nakit Akışları']
        free_cash_flow = row['Yıllıklandırılmış Serbest Nakit Akışı']
        fcf_yield = None 
        # FCF Verimi = FCF / PD
        if pd.notnull(free_cash_flow) and pd.notnull(market_cap) and market_cap > 0:
            fcf_yield = free_cash_flow / market_cap
            card.append(f"FCF Verimi: {fcf_yield:.2%} → {'✅ Güçlü' if fcf_yield >= 0.05 else '❌ Zayıf'}")
            if fcf_yield >= 0.05:
                score += 1
        else:
            card.append("FCF veya piyasa değeri verisi eksik")

        # Nakit Akışı Pozitif mi?
        if pd.notnull(operating_cash_flow):
            durum = operating_cash_flow > 0
            card.append(f"İşletme Nakit Akışı = {operating_cash_flow:.0f} → {'✅ Pozitif' if durum else '❌ Negatif'}")
            if durum:
                score += 1
        else:
            card.append("İşletme cashflow akışı verisi eksik")


        # PD/FCF oranı düşük mü? (Nakde göre pahalı mı?)
        if pd.notnull(market_cap) and pd.notnull(free_cash_flow) and free_cash_flow > 0:
            price_to_fcf = market_cap / free_cash_flow
            card.append(f"PD/FCF = {price_to_fcf:.1f} → {'✅ Ucuz' if price_to_fcf <= 15 else '❌ Pahalı'}")
            if price_to_fcf <= 15:
                score += 1
        else:
            card.append("PD/FCF hesaplanamıyor (veri eksik)")

    except Exception as e:
        card.append(f"⚠️ Hata: {e}")

    karne_metni = "\n".join(card) + f"\nToplam Peter Lynch Skoru: {score} / 3"
    return score, karne_metni, fcf_yield

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
    card = []

    if pd.notnull(row['F/K']):
        durum = row['F/K'] < 15
        card.append(f"F/K = {row['F/K']} → {'✅ Uygun' if durum else '❌ Uygun değil'}")
        if durum: score += 1
    else:
        card.append("F/K = ⚠️ F/K verisi eksik")

    if pd.notnull(row['PD/DD']):
        durum = row['PD/DD'] < 1.5
        card.append(f"PD/DD = {row['PD/DD']} → {'✅ Uygun' if durum else '❌ Uygun değil'}")
        if durum: score += 1
    else:
        card.append("PD/DD verisi eksik")

    if pd.notnull(row['Cari Oran']):
        durum = 2 < row['Cari Oran'] < 100
        card.append(f"Cari Oran = {row['Cari Oran']} → {'✅ Uygun' if durum else '❌ Uygun değil'}")
        if durum: score += 1
    else:
        card.append("Cari Oran verisi eksik")

    if pd.notnull(row['İşletme Faaliyetlerinden Nakit Akışları']):
        durum = row['İşletme Faaliyetlerinden Nakit Akışları'] > 0
        card.append(f"Nakit Akışı = {row['İşletme Faaliyetlerinden Nakit Akışları']} → {'✅ Pozitif' if durum else '❌ Negatif'}")
        if durum: score += 1
    else:
        card.append("Nakit Akışı verisi eksik")

    if pd.notnull(row['Yıllıklandırılmış Serbest Nakit Akışı']):
        durum = row['Yıllıklandırılmış Serbest Nakit Akışı'] > 0
        card.append(f"Serbest Nakit Akışı = {row['Yıllıklandırılmış Serbest Nakit Akışı']} → {'✅ Pozitif' if durum else '❌ Negatif'}")
        if durum: score += 1
    else:
        card.append("Serbest Nakit Akışı verisi eksik")

    karne_metni = "\n".join(card) + f"\nToplam Graham Skoru: {score} / 5"
    return score, karne_metni

def m_skor_karne_yorum(m_skor):
    if m_skor is None:
        return "M-Skor verisi eksik"

    yorum = ""
    yorum += f"M-Skor: {m_skor:.2f} → "
    if m_skor < -2.22:
        yorum += "✅ Düşük risk (finansal manipülasyon ihtimali düşük)"
    else:
        yorum += "⚠️ Yüksek risk (bilançoda bozulma/makyaj ihtimali olabilir)"
    return yorum

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
        # Excel verisini oku
        _, _, cashflow_df=load_financial_data(company)

        if "İşletme Faaliyetlerinden Nakit Akışları" not in cashflow_df.index:
            print("⛔ 'İşletme Faaliyetlerinden Nakit Akışları' verisi bulunamadı.")
            return None

        # İşletme nakit akışı ve yatırım nakit akışı verilerini çek
        operating_cf_series = cashflow_df.loc["İşletme Faaliyetlerinden Nakit Akışları"]
        
        # Yatırım harcamaları olarak genelde "Maddi ve Maddi Olmayan Duran Varlık Alımları" (negatif değer olur)
        if "Maddi ve Maddi Olmayan Duran Varlık Alımları" in cashflow_df.index:
            capex_series = cashflow_df.loc["Maddi ve Maddi Olmayan Duran Varlık Alımları"]
        elif "Yatırım Faaliyetlerinden Kaynaklanan Nakit Akışları" in cashflow_df.index:
            capex_series = cashflow_df.loc["Yatırım Faaliyetlerinden Kaynaklanan Nakit Akışları"]
        else:
            print("⛔ Yatırım harcamaları verisi bulunamadı.")
            return None

        # FCF = OFCF - CAPEX
        fcf_series = operating_cf_series - capex_series

        # Piyasa değeri (son dönem için alınır, sabit tutulur)
        market_cap = row['Piyasa Değeri']
        if market_cap.empty or market_cap.values[0] <= 0:
            print("⛔ Piyasa değeri geçersiz.")
            return None
        pdg = market_cap.values[0]

        fcf_yield = fcf_series / pdg
        fcf_yield = fcf_yield.dropna()
        
        sorted_index = sorted(fcf_yield.index, key=period_order)
        fcf_yield = fcf_yield[sorted_index]
        
        df_sonuç = pd.DataFrame({
            "Dönem": fcf_yield.index,
            "FCF Verimi": fcf_yield.values
        })

        plt.figure(figsize=(10, 5))
        plt.plot(df_sonuç["Dönem"], df_sonuç["FCF Verimi"] * 100, marker='o')
        plt.title(f"{company} - FCF Verimi Zaman Serisi")
        plt.ylabel("FCF Verimi (%)")
        plt.xlabel("Dönem")
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
            
        # Veriyi sadeleştir
        #return pd.DataFrame({
        #    "Dönem": fcf_yield.index,
        #    "FCF Verimi": fcf_yield.values
        #})

    except Exception as e:
        print(f"⚠️ {company} için FCF zaman serisi hatası: {e}")
        return None

def fcf_detailed_analysis(company, row):
    # Excel verisini oku
    _, income_df, cashflow_df=load_financial_data(company)

    # Gerekli kalemleri al
    sales_series = income_df.loc["Satış Gelirleri"]
    net_profit = cashflow_df.loc["Dönem Karı (Zararı)"]
    operating_cf_series = cashflow_df.loc["İşletme Faaliyetlerinden Nakit Akışları"]

    # CAPEX için öncelikli kalem
    if "Maddi ve Maddi Olmayan Duran Varlık Alımları" in cashflow_df.index:
        capex_series = cashflow_df.loc["Maddi ve Maddi Olmayan Duran Varlık Alımları"]
    elif "Yatırım Faaliyetlerinden Kaynaklanan Nakit Akışları" in cashflow_df.index:
        capex_series = cashflow_df.loc["Yatırım Faaliyetlerinden Kaynaklanan Nakit Akışları"]
    else:
        raise ValueError("CAPEX verisi bulunamadı.")

    # FCF hesapla
    fcf_series = operating_cf_series - capex_series
    
    # Piyasa değeri (son dönem için alınır, sabit tutulur)
    market_cap = row['Piyasa Değeri']
    
    if market_cap.empty or market_cap.values[0] <= 0:
        print("⛔ Piyasa değeri geçersiz.")
        return None
    
    pdg = market_cap.values[0]

    fcf_yield = fcf_series / pdg
    fcf_yield = fcf_yield.dropna()
    

    # Tablolaştır
    df = pd.DataFrame({
        "Satışlar": sales_series,
        "Net Kâr": net_profit,
        "Faaliyet Nakit Akışı": operating_cf_series,
        "CAPEX": capex_series,
        "FCF": fcf_series,
        "FCF Verimi (%)": fcf_yield * 100
    })

    # ❗ Sütunları tarih sırasına göre sırala
    sorted_columns = sorted(df.columns, key=period_order)
    df = df[sorted_columns]
    return df

def fcf_detailed_analysis_plot(company, row):
    # Excel verisini oku
    _, income_df, cashflow_df=load_financial_data(company)

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
    
    # Piyasa değeri (son dönem için alınır, sabit tutulur)
    market_cap = row['Piyasa Değeri']
    if market_cap.empty or market_cap.values[0] <= 0:
        print("⛔ Piyasa değeri geçersiz.")
        return None
    pdg = market_cap.values[0]

    fcf_yield = fcf_series / pdg
    fcf_yield = fcf_yield.dropna()

    # Tablolaştır
    df = pd.DataFrame({
        "Satışlar": sales_series,
        "Net Kar": net_profit,
        "Faaliyet Nakit Akışı": operating_cf_series,
        "CAPEX": capex_series,
        "FCF": fcf_series,
        "FCF Verimi (%)": fcf_yield * 100
    }).T

    # Dönemleri sırala
    df = df.T
    df = df.sort_index(key=lambda x: [period_order(d) for d in x])
    df.index = pd.to_datetime(df.index, format="%Y/%m", errors="coerce")

    # Hareketli ortalamalar
    df_ma = df.rolling(3).mean()

    # Grafik çizimi
    x = mdates.date2num(df.index)
    fig, axes = plt.subplots(5, 1, figsize=(14, 16), sharex=True)

    for i, (kolon, renk, ma_renk) in enumerate([
        ("Satışlar", "tab:blue", "tab:cyan"),
        ("Net Kar", "tab:green", "lime"),
        ("FCF", "tab:purple", "violet"),
        ("CAPEX", "tab:orange", "gold"),
        ("FCF Verimi (%)", "tab:red", "tomato"),
    ]):
        y = df[kolon].to_numpy() / (1e9 if "Verimi" not in kolon else 1)
        y_ma = df_ma[kolon].to_numpy() / (1e9 if "Verimi" not in kolon else 1)
        axes[i].plot_date(x, y, linestyle='-', marker='o', color=renk, label=kolon)
        axes[i].plot_date(x, y_ma, linestyle='--', color=ma_renk, label="Hareketli Ortalama")
        axes[i].fill_between(x, 0, y, alpha=0.1, color=renk)
        axes[i].set_ylabel(kolon + ("\n(Milyar TL)" if "Verimi" not in kolon else ""))
        axes[i].legend()
        axes[i].grid(True)

    axes[-1].set_xlabel("Tarih")
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    fig.suptitle(f"{company} | FCF Odaklı Finansal Analiz", fontsize=16)
    plt.xticks(rotation=45)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

def calculate_scores(company, row, balance, income, cashflow, current_period, previous_period):
    f_score, detail = calculate_piotroski_f_score(row, balance, income,
                                          current_period, previous_period)
    f_karne = f_skor_karne_yorum(f_score)    

    m_skor = calculate_beneish_m_score(company, balance, income, cashflow, current_period, previous_period)
    m_karne = m_skor_karne_yorum(m_skor)

    graham_skor, graham_karne = graham_score_card(row)
    lynch_skor, lynch_karne, _ = peter_lynch_score_card(row)

    return {
        "f_score": f_score,
        "f_karne": f_karne,
        "m_skor": m_skor,
        "m_karne": m_karne,
        "graham_skor": graham_skor,
        "graham_karne": graham_karne,
        "lynch_skor": lynch_skor,
        "lynch_karne": lynch_karne,
        "detail": detail
    }

def generate_report(company, scores, show_details=False):
    text = f"""══════════════════════════════════
{company}
══════════════════════════════════
{scores['f_karne']}
{scores['m_karne']}
Graham-Skor: {scores['graham_skor']}
Lynch-Skor : {scores['lynch_skor']}
"""

    if show_details:
        for k, v in scores["detail"].items():
            text += f"{k}: {v}\n"

    text += "\n[GRAHAM KARNE]\n" + scores["graham_karne"]
    text += "\n"
    text += "\n[LYNCH KARNE]\n" + scores["lynch_karne"]

    return text

def format_report_as_html(company, text, m_skor):
    background = "#fff8dc" if m_skor is not None and m_skor > -1.78 else "#f9f9f9"
    satirlar = text.split("\n")
    company = satirlar[0].strip("═").strip()

    html = f"""
    <div style="margin-bottom: 20px; padding: 10px; border: 1px solid #ddd; background: {background}; border-radius: 8px;">
        <h3 style="margin-top:0; color:#333;">🏢 {company}</h3>
        <pre style="font-family: monospace; white-space: pre-wrap; color: #222;">
        {chr(10).join(satirlar[1:])}
        </pre>
    </div>
    """
    return html

def show_company_scorecard(company, row, current_period, previous_period, show_details=False):
    try:
        balance, income, cashflow = load_financial_data(company)
        scores = calculate_scores(company, row, balance, income, cashflow,
                                  current_period, previous_period)
        report = generate_report(company, scores, show_details)
        html = format_report_as_html(company, report, scores["m_skor"])
        st.markdown(f"<div style='max-height: 700px; overflow-y: scroll;'>{html}</div>", unsafe_allow_html=True)
    except FileNotFoundError as e:
        st.error(f"⛔ Dosya bulunamadı: {e}")
    except Exception as e:
        st.error(f"⚠️ Hata oluştu: {e}")

