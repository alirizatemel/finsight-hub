import streamlit as st # type: ignore
import pandas as pd
from modules.data_loader import load_financial_data
from modules.scores import calculate_piotroski_f_score, calculate_beneish_m_score, peter_lynch_score_card, graham_score

@st.cache_data(show_spinner=False)   
def get_financials(company: str):
    """
    Returns (balance_df, income_df, cashflow_df) for a given company.
    Cached so repeated calls don't hit the disk again.
    """
    return load_financial_data(company)


st.title("📊 Bilanço Skorları Toplu Analiz")

radar_file = "companies/fintables_radar.xlsx"

loglar = []

try:
    df_radar = pd.read_excel(radar_file)
    df_radar["Şirket"] = df_radar["Şirket"].str.strip()
    companies = df_radar["Şirket"].dropna().unique()
    loglar.append(f"🔄 Toplam {len(companies)} şirket bulundu.")
except Exception as e:
    st.error(f"Dosya okunamadı: {e}")
    st.stop()

# Örnek bir şirketten dönem kolonlarını al

def period_sort_key(period_str):
    yil, ay = map(int, period_str.split("/"))
    return yil * 100 + ay  # Örn: 2024/12 → 202412, 2024/03 → 202403

ornek_sirket = companies[0]
try:
    example_balance_sheet, _, _ = load_financial_data(ornek_sirket)
    period_list = sorted(
        [col for col in example_balance_sheet.columns if "/" in col],
        key=period_sort_key,
        reverse=True
    )
except Exception as e:
    st.error(f"{ornek_sirket} şirketinden dönem bilgileri alınamadı: {e}")
    st.stop()

# Seçilebilir dönem (sadece current_period seçiliyor)
current_period = st.selectbox("Current Period", options=period_list)

# 1 yıl önceki dönemi bul (örneğin 2024/12 -> 2023/12)
def one_year_back(period):
    try:
        yil, ay = map(int, period.split("/"))
        return f"{yil-1}/{ay}"
    except:
        return None

previous_period = one_year_back(current_period)

# Eğer 1 yıl öncesi listede yoksa uyarı göster
if previous_period not in period_list:
    st.error(f"{current_period} için bir yıl önceki dönem ({previous_period}) verisi bulunamadı. Başka bir dönem seçiniz.")
    st.stop()
else:
    st.markdown(f"**Previous Period:** `{previous_period}`")

with st.spinner("Skorlar hesaplanıyor..."):
    # F ve M skorları hesapla
    results  = []
    progress = st.progress(0)    
    for i, company in enumerate(companies, start=1):
        try:
            row = df_radar[df_radar["Şirket"] == company]
            if row.empty:
                loglar.append(f"⛔ {company} → Şirket bulunamadı.")
                continue  
            balance, income, cashflow = get_financials(company) 
            f,f_detay = calculate_piotroski_f_score(row, balance, income, current_period, previous_period)
            m = calculate_beneish_m_score(company, balance, income, cashflow, current_period, previous_period)
            lynch_skor, _, _ = peter_lynch_score_card(row)
            graham_skor = graham_score(row)
            results.append({
                "Şirket": company, 
                "F-Skor": f, 
                "M-Skor": m,
                "L-Skor":lynch_skor,
                "Graham Skoru":graham_skor})
            
        except FileNotFoundError:
            loglar.append(f"⛔ {company} → Excel dosyası bulunamadı.")
        except Exception as e:
            loglar.append(f"⚠️ {company} → Hata: {e}")
        
        progress.progress(i / len(companies)) 

# Skor tablosunu göster
if results:
    skor_df = pd.DataFrame(results)
    st.dataframe(skor_df.sort_values("F-Skor", ascending=False), use_container_width=True)
else:
    st.info("Hiçbir şirket için skor hesaplanamadı.")

# Logları göster
with st.expander("🪵 Loglar"):
    for log in loglar:
        st.write(log)
