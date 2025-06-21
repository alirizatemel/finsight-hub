import streamlit as st  # type: ignore
import pandas as pd
import matplotlib.pyplot as plt
from modules.data_loader import load_financial_data
from modules.scores import (
    calculate_scores,
    show_company_scorecard,
    period_order,
    fcf_detailed_analysis,
    fcf_detailed_analysis_plot,
    fcf_yield_time_series,
)
from config import RADAR_XLSX


# --- yeni, önerilen yöntem -----------------------
params = st.query_params          # doğrudan Mapping[str, str]
default_symbol = params.get("symbol", "").upper()


@st.cache_data(show_spinner=False)
def get_scores_cached(symbol, radar_row, balance, income, cashflow, curr, prev):
    return calculate_scores(symbol, radar_row, balance, income, cashflow, curr, prev)


@st.cache_data(show_spinner=False)
def get_financials(symbol: str):
    """Load balance, income, and cash‑flow sheets for a single ticker."""
    return load_financial_data(symbol)


@st.cache_data(show_spinner=False)
def get_radar() -> pd.DataFrame:
    """Read the pre‑built fintables_radar Excel once and cache it."""
    df = pd.read_excel(RADAR_XLSX)
    df["Şirket"] = df["Şirket"].str.strip()
    return df


def main():
    st.title("📈 Tek Hisse Finans Skor Kartı")

    # Kullanıcı girişi
    symbol = st.text_input("Borsa Kodu", default_symbol).strip().upper()
    if not symbol:
        st.info("Lütfen geçerli bir borsa kodu girin.")
        st.stop()

    # Finansalları yükle
    try:
        balance, income, cashflow = get_financials(symbol)
    except FileNotFoundError:
        st.error(f"{symbol} verileri bulunamadı.")
        st.stop()

    # Dönem kontrolü
    periods = sorted(
        [c for c in balance.columns if "/" in c],
        key=period_order,
        reverse=True,
    )
    if len(periods) < 2:
        st.error("Yeterli dönem bilgisi yok (en az 2 dönem gerek).")
        st.stop()
    curr, prev = periods[:2]

    # Radar satırı
    radar_df = get_radar()
    radar_row = radar_df[radar_df["Şirket"] == symbol]
    if radar_row.empty:
        st.warning("Radar verisi bulunamadı; bazı skorlar eksik hesaplanabilir.")

    # Analiz başlatma kontrolü
    if "analyze" not in st.session_state:
        st.session_state.analyze = False

    if st.button("Analiz Et"):
        st.session_state.analyze = True

    if st.session_state.analyze:
        scores = get_scores_cached(symbol, radar_row, balance, income, cashflow, curr, prev)

        # Özet metrikler
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Piotroski F-Skor", f"{scores['f_score']} / 9")
            st.caption("🟢 Sağlam" if scores["f_score"] >= 7 else "🟡 Orta" if scores["f_score"] >= 4 else "🔴 Zayıf")

            mskor = scores["m_skor"]
            st.metric("Beneish M-Skor", f"{mskor:.2f}" if mskor is not None else "-")
            st.caption("🟢 Güvenilir" if mskor is not None and mskor < -2.22 else "🔴 Riskli")

        with col2:
            st.metric("Graham Skor", f"{scores['graham_skor']} / 5")
            st.caption("🟢 Güçlü" if scores["graham_skor"] >= 4 else "🟡 Sınırlı" if scores["graham_skor"] == 3 else "🔴 Zayıf")

            st.metric("Peter Lynch Skor", f"{scores['lynch_skor']} / 3")
            st.caption("🟢 Sağlam" if scores["lynch_skor"] == 3 else "🟡 Orta" if scores["lynch_skor"] == 2 else "🔴 Zayıf")


        # Sekmeler
        tab_score, tab_fcf, tab_raw = st.tabs(["📊 Skor Detayları", "🔍 FCF Analizi", "🗂 Ham Veriler"])

        with tab_score:
            show_company_scorecard(symbol, radar_row, curr, prev)

        with tab_fcf:
            st.subheader("FCF Detay Tablosu")
            df_fcf = fcf_detailed_analysis(symbol, radar_row)
            if df_fcf is not None:
                with st.expander("📊 FCF Detay Tablosu", expanded=False):
                    st.dataframe(df_fcf.style.format({"FCF Verimi (%)": "{:.2f}"}))

                st.subheader("FCF Verimi Grafiği")
                fcf_yield_time_series(symbol, radar_row)

                st.subheader("FCF + Satışlar + CAPEX Çoklu Grafik")
                fcf_detailed_analysis_plot(symbol, radar_row)
            else:
                st.info("FCF verileri hesaplanamadı veya eksik.")

        with tab_raw:
            st.expander("Bilanço").dataframe(balance)
            st.expander("Gelir Tablosu").dataframe(income)
            st.expander("Nakit Akış Tablosu").dataframe(cashflow)

if __name__ == "__main__":
    main()
