import os
import streamlit as st # type: ignore
import pandas as pd
from modules.data_loader import load_financial_data
from modules.scanner import run_scan                 # NEW (shared scanner)

from streamlit import column_config as cc # type: ignore
from config import RADAR_XLSX

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "scanner.log")


loglar = []

@st.cache_data(show_spinner=False)
def load_radar() -> pd.DataFrame:
    """Read Fintables radar sheet once & cache."""
    df = pd.read_excel(RADAR_XLSX)
    df["Şirket"] = df["Şirket"].str.strip()
    return df

@st.cache_data(show_spinner=False)   
def get_financials(company: str):
    """
    Returns (balance_df, income_df, cashflow_df) for a given company.
    Cached so repeated calls don't hit the disk again.
    """
    return load_financial_data(company)


def link_to_analysis(ticker: str) -> str:
    """
    Tek-hisse analiz sayfasına tıklanabilir HTML köprüsü döndürür.
    (Markdown yerine <a href=…> kullanıyoruz.)
    """
    return f'<a href="/stock_analysis?symbol={ticker}" target="_self">{ticker}</a>'

st.title("📊 Bilanço Skorları Toplu Analiz")

try:
    df_radar = load_radar()
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

ornek_sirket = None
for c in companies:
    try:
        example_balance_sheet, _, _ = load_financial_data(c)
        ornek_sirket = c
        break
    except FileNotFoundError:
        continue

if ornek_sirket is None:
    st.error("Hiçbir şirket için bilanço Excel'i bulunamadı.")
    st.stop()

# artık example_balance_sheet zaten var
period_list = sorted(
    [col for col in example_balance_sheet.columns if "/" in col],
    key=period_sort_key,
    reverse=True
)

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

st.sidebar.header("🔍 Skor Filtreleri")

with st.sidebar.expander("Filtreler", expanded=True):
    f_min, f_max = st.slider("F-Skor Aralığı", 0, 9, (0, 9), key="f")
    m_min, m_max = st.slider("M-Skor Aralığı", -5.0, 5.0, (-5.0, 5.0), 0.1, key="m")
    l_min, l_max = st.slider("Lynch Aralığı", 0, 3, (0, 3), key="l")
    g_min, g_max = st.slider("Graham Aralığı", 0, 5, (0, 5), key="g")

    colA, colB = st.columns(2)
    with colA:
        apply = st.button("🔍 Filtrele", key="apply_filter")

    with colB:
        reset = st.button("🔄 Sıfırla", key="reset_filter")

if reset:
    st.session_state.pop("score_df", None)


# -------------------------------------------------------------------------
# DB‑first logic (same UX as Trap Radar)
# -------------------------------------------------------------------------
with st.sidebar:
    st.header("Veri Kaynağı")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Veritabanından Yükle"):
            st.session_state.scan = True
            st.session_state.force_refresh = False
    with col2:
        if st.button("Skorları Yenile"):
            st.session_state.scan = True
            st.session_state.force_refresh = True

# -------------------------------------------------------------------------
# DB‑first logic  (load / refresh)
# -------------------------------------------------------------------------
if st.session_state.get("scan"):

    df_scan, logs, _ = run_scan(df_radar)

    # ❷ HER İKİ DURUMDA DA DF’Yİ HAFIZADA TUT
    st.session_state.score_df = df_scan
    st.session_state.scan = False            # tarama bitti
    st.session_state.force_refresh = False

# ❸ EĞER SCAN YOKSA AMA DF BELLEKTEYSE ONU KULLAN
elif "score_df" in st.session_state:
    df_scan = st.session_state.score_df

# ❹ HİÇBİR ŞEY YOKSA KULLANICIYA BİLGİ VER, STOP ETME
else:
    st.info("Önce “Veritabanından Yükle” veya “Skorları Yenile” seçeneğini tıklayın.")
    st.stop()


score_df = df_scan     # rename for clarity below

symbol_col = "hisse"

if symbol_col not in score_df.columns:
    st.error(f"❌ '{symbol_col}' kolonu bulunamadı. Veri kaydedilememiş olabilir.")
    st.stop()

score_df["Link"] = "/stock_analysis?symbol=" + score_df[symbol_col]


# Skor kolonlarını numeriğe çevir, olmayanlar NaN olur
for col in ["f_skor", "m_skor", "lynch", "graham", "MOS"]:
    score_df[col] = pd.to_numeric(score_df[col], errors="coerce")

# MOS'u yalnızca 0–1 aralığında ise %'ye çevir
if "MOS_scaled" not in st.session_state:
    score_df["MOS"] = score_df["MOS"] * 100
    st.session_state.MOS_scaled = True

# --- Uygula / sıfırla filtre --------------------------------------------
if apply:
    filtered_df = score_df[
        (score_df["f_skor"] >= f_min) & (score_df["f_skor"] <= f_max) &
        (score_df["m_skor"] >= m_min) & (score_df["m_skor"] <= m_max) &
        (score_df["lynch"] >= l_min) & (score_df["lynch"] <= l_max) &
        (score_df["graham"] >= g_min) & (score_df["graham"] <= g_max)
    ]
    st.markdown(f"**🔎 Filtrelenmiş Şirket Sayısı:** {len(filtered_df)}")
    
    st.dataframe(
        filtered_df.sort_values("f_skor", ascending=False),
        column_config={
            "Link": cc.LinkColumn(
                label="Link",    # hangi kolon URL’yi tutuyor
                display_text="Analize Git"
            ),
            "MOS": cc.NumberColumn(
                label="MOS",
                format="%.1f%%", 
            ),
        },
        hide_index=True,
        use_container_width=True,
    )
    

else:
    st.markdown(f"**📋 Tüm Şirketler:** {len(score_df)}")
    #st.dataframe(score_df.sort_values("F-Skor", ascending=False), use_container_width=True)
    st.dataframe(
        score_df.sort_values("f_skor", ascending=False),
        column_config={
            "Link": cc.LinkColumn(
                label="Link",    # hangi kolon URL’yi tutuyor
                display_text="Analize Git"
            ),
            "MOS": cc.NumberColumn(
                label="MOS",
                format="%.1f%%", 
            ),
        },
        hide_index=True,
        use_container_width=True,
    )



# Logları göster
with st.expander("🪵 İşlem Logları (scanner.log)", expanded=False):
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            logs = f.read()
            st.text_area("Log İçeriği", logs, height=300)
    else:
        st.info("Henüz log dosyası oluşturulmamış.")
