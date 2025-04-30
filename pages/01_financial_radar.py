import streamlit as st # type: ignore
import pandas as pd
from modules.data_loader import load_financial_data
from modules.scores import calculate_piotroski_f_score, calculate_beneish_m_score, peter_lynch_score_card, graham_score
from streamlit import column_config as cc

RADAR_XLSX = "companies/fintables_radar.xlsx"

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

def build_score_table(progress_cb=None):
    radar = load_radar()
    companies = radar["Şirket"].unique()
    results, logs = [], []
    total = len(companies)

    for i, c in enumerate(companies, 1):
        row = radar[radar["Şirket"] == c]

        f_skor = m_skor = None
        try:
            bal, inc, cf = get_financials(c)

            # 🔹 şirket bazlı dönem seçimi
            cols = [col for col in bal.columns if "/" in col]
            cols = sorted(cols, key=period_sort_key, reverse=True)
            if len(cols) >= 2:
                curr, prev = cols[:2]
                f_skor, _ = calculate_piotroski_f_score(row, bal, inc, curr, prev)
                m_skor    = calculate_beneish_m_score(c, bal, inc, cf, curr, prev)
            else:
                logs.append(f"ℹ️ {c}: <2 dönem — F/M atlandı/")
                            
        except FileNotFoundError:
            logs.append(f"ℹ️ {c}: Excel yok — F/M atlandı")
        except Exception as e:
            logs.append(f"⚠️ {c}: {e}")

        lynch, *_ = peter_lynch_score_card(row)
        graham     = graham_score(row)

        results.append({
            "Şirket"       : c,
            "F-Skor"       : f_skor,
            "M-Skor"       : m_skor,
            "L-Skor"       : lynch,
            "Graham Skoru" : graham,
        })


        if progress_cb:
            progress_cb.progress(i / total)

    df = pd.DataFrame(results)
    for col in ["F-Skor", "M-Skor", "L-Skor", "Graham Skoru"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df, logs


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
    l_min, l_max = st.slider("Lynch Aralığı", 0, 5, (0, 5), key="l")
    g_min, g_max = st.slider("Graham Aralığı", 0, 5, (0, 5), key="g")

    colA, colB = st.columns(2)
    with colA:
         apply = st.button("🔍 Filtrele", key="apply_filter")
    with colB:
        reset = st.button("🔄 Sıfırla", key="reset_filter")

if reset:
    st.session_state.pop("score_df", None)

# --- Build or retrieve score table ---------------------------------------

if "score_df" not in st.session_state:
    with st.spinner("Skorlar hesaplanıyor…"):
        prog = st.progress(0)
        score_df, logs = build_score_table(prog)
        st.session_state["score_df"] = score_df
        st.session_state["logs"] = logs
else:
    score_df = st.session_state["score_df"]
    logs = st.session_state["logs"]


# Skor tablosunu göster
score_df["Link"]     = "/stock_analysis?symbol=" + score_df["Şirket"]


# Skor kolonlarını numeriğe çevir, olmayanlar NaN olur
for col in ["F-Skor", "M-Skor", "L-Skor", "Graham Skoru"]:
    score_df[col] = pd.to_numeric(score_df[col], errors="coerce")

# --- Uygula / sıfırla filtre --------------------------------------------
if apply:
    filtered_df = score_df[
        (score_df["F-Skor"] >= f_min) & (score_df["F-Skor"] <= f_max) &
        (score_df["M-Skor"] >= m_min) & (score_df["M-Skor"] <= m_max) &
        (score_df["L-Skor"] >= l_min) & (score_df["L-Skor"] <= l_max) &
        (score_df["Graham Skoru"] >= g_min) & (score_df["Graham Skoru"] <= g_max)
    ]
    st.markdown(f"**🔎 Filtrelenmiş Şirket Sayısı:** {len(filtered_df)}")
    #st.dataframe(filtered_df.sort_values("F-Skor", ascending=False), use_container_width=True)
    st.dataframe(
        filtered_df.sort_values("F-Skor", ascending=False),
        column_config={
            "Link": cc.LinkColumn(
                label="Link",    # hangi kolon URL’yi tutuyor
                display_text="Analize Git",
                #target="_self",     # aynı sekmede aç
            )
        },
        hide_index=True,
        use_container_width=True,
    )
    

else:
    st.markdown(f"**📋 Tüm Şirketler:** {len(score_df)}")
    #st.dataframe(score_df.sort_values("F-Skor", ascending=False), use_container_width=True)
    st.dataframe(
        score_df.sort_values("F-Skor", ascending=False),
        column_config={
            "Link": cc.LinkColumn(
                label="Link",    # hangi kolon URL’yi tutuyor
                display_text="Analize Git",
                #target="_self",     # aynı sekmede aç
            )
        },
        hide_index=True,
        use_container_width=True,
    )



# Logları göster
with st.expander("🪵 Loglar"):
    for log in loglar:
        st.write(log)
