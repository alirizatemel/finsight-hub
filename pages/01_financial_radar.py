import streamlit as st # type: ignore
import pandas as pd
from modules.data_loader import load_financial_data
from modules.scores import calculate_piotroski_f_score, calculate_beneish_m_score, peter_lynch_score_card, graham_score

st.title("📊 Bilanço Skorları Toplu Analiz")

radar_file = "companies/fintables_radar.xlsx"

loglar = []

try:
    df_radar = pd.read_excel(radar_file)
    df_radar["Şirket"] = df_radar["Şirket"].str.strip()
    sirketler = df_radar["Şirket"].dropna().unique()
    loglar.append(f"🔄 Toplam {len(sirketler)} şirket bulundu.")
except Exception as e:
    st.error(f"Dosya okunamadı: {e}")
    st.stop()

# Örnek bir şirketten dönem kolonlarını al

def donem_sirasi(donem_str):
    yil, ay = map(int, donem_str.split("/"))
    return yil * 100 + ay  # Örn: 2024/12 → 202412, 2024/03 → 202403

ornek_sirket = sirketler[0]
try:
    bilanco_ornek, _, _ = load_financial_data(ornek_sirket)
    donemler = [col for col in bilanco_ornek.columns if "/" in col]
    donemler = sorted(
    [col for col in bilanco_ornek.columns if "/" in col],
    key=donem_sirasi,
    reverse=True
)
except Exception as e:
    st.error(f"{ornek_sirket} şirketinden dönem bilgileri alınamadı: {e}")
    st.stop()

# Seçilebilir dönem (sadece current_period seçiliyor)
current_period = st.selectbox("Current Period", options=donemler)

# 1 yıl önceki dönemi bul (örneğin 2024/12 -> 2023/12)
def bir_yil_once(donem):
    try:
        yil, ay = map(int, donem.split("/"))
        return f"{yil-1}/{ay}"
    except:
        return None

previous_period = bir_yil_once(current_period)

# Eğer 1 yıl öncesi listede yoksa uyarı göster
if previous_period not in donemler:
    st.warning(f"{current_period} için bir yıl önceki dönem ({previous_period}) verisi bulunamadı.")
else:
    st.markdown(f"**Previous Period:** `{previous_period}`")

# F ve M skorları hesapla
sonuclar = []
for sirket in sirketler:
    try:
        row = df_radar[df_radar["Şirket"] == sirket]
        if row.empty:
            loglar.append(f"⛔ {sirket} → Şirket bulunamadı.")
            continue  # return yerine continue kullanılmalı
        bilanco, gelir, nakit = load_financial_data(sirket)
        f,f_detay = calculate_piotroski_f_score(row, bilanco, gelir, current_period, previous_period)
        m = calculate_beneish_m_score(sirket, bilanco, gelir, nakit, current_period, previous_period)
        lynch_skor, _, _ = peter_lynch_score_card(row)
        graham_skor = graham_score(row)
        sonuclar.append({"Şirket": sirket, "F-Skor": f, "M-Skor": round(m, 2),"L-Skor":lynch_skor,"Graham Skoru":graham_skor})
        loglar.append(f"✅ {sirket} → F: {f}, M: {round(m, 2)}")
    except FileNotFoundError:
        loglar.append(f"⛔ {sirket} → Excel dosyası bulunamadı.")
    except Exception as e:
        loglar.append(f"⚠️ {sirket} → Hata: {e}")

# Skor tablosunu göster
if sonuclar:
    skor_df = pd.DataFrame(sonuclar)
    st.dataframe(skor_df.sort_values("F-Skor", ascending=False), use_container_width=True)
else:
    st.info("Hiçbir şirket için skor hesaplanamadı.")

# Logları göster
with st.expander("🪵 Loglar"):
    for log in loglar:
        st.write(log)
