
import streamlit as st
from modules.data_loader import load_company_xlsx
from modules.calculations import f_score, beneish_m_score

st.title("📈 Tek Hisse Analizi")

symbol = st.text_input("Borsa Kodu", "ACSEL")

if st.button("Hesapla"):
    bilanco, gelir, cashflow = load_company_xlsx(symbol)

    st.metric("Piotroski F‑Skor", f_score(bilanco, gelir, cashflow))
    st.metric("Beneish M‑Skor", beneish_m_score(bilanco, gelir, cashflow))

    st.write("📝 Ayrıntılı metrikleri ve grafiklerinizi ekleyin.")
