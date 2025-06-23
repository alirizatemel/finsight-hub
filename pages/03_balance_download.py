#  pages/04_balance_download.py
import streamlit as st #type: ignore
from modules.downloader import update_companies_if_needed

st.title("📥 Fintables Bilanço İndirici")

st.markdown(
    """
    Bu sayfa, **data/son_bilancolar.json** dosyasındaki şirket kodlarını tarar,  
    _companies_ klasöründe güncel bilanço dosyası (**2025/3** dönemi) bulunmayan
    veya eski sürümü bulunan şirketlerin Excel dosyalarını Fintables’tan otomatik indirir
    ve ilgili klasöre kaydeder.
    """
)


# Mesajları tutacak liste
if "logs" not in st.session_state:
    st.session_state["logs"] = []

def streamlit_logger(msg: str):
    st.session_state.logs.append(msg)
    log_placeholder.markdown("  \n".join(st.session_state.logs))

if st.button("🔽 Bilançoları İndir"):
    st.session_state.logs = []          # eski logları temizle
    with st.spinner("İndiriliyor…"):
        with st.expander("⬇️ İşlem Günlüğü", expanded=True):
            log_placeholder = st.empty()
            update_companies_if_needed(log=streamlit_logger)  # ↓ retry’li fonksiyon
    st.success("İndirme tamamlandı.")


st.markdown("""
<style>
.big-title {
    font-size: 22px;
    font-weight: bold;
    margin-bottom: 10px;
}
.section-title {
    font-size: 18px;
    font-weight: bold;
    margin-top: 1.5em;
    color: #f0f0f0;
}
.info-box {
    background-color: #2b2b2b;
    padding: 12px;
    border-radius: 8px;
    margin-top: 10px;
    font-size: 15px;
    color: #f5f5f5;
}
ul {
    padding-left: 20px;
    font-size: 15px;
    color: #f5f5f5;
}
code {
    background-color: #1e1e1e;
    padding: 2px 5px;
    border-radius: 4px;
}
</style>

<div class='big-title'>📥 Balance Download – Sayfa Açıklaması</div>

<div class='info-box'>
Bu sayfa, <strong>Fintables</strong>'tan alınan finansal verilerin otomatik olarak indirilmesini sağlar. Her şirket için <em>bilanço</em>, <em>gelir tablosu</em> ve <em>nakit akış</em> sayfalarını içeren <code>.xlsx</code> dosyaları düzenli olarak toplanır ve yerel klasör yapısına kaydedilir.
</div>

<div class='section-title'>🎯 Amaç</div>
<ul>
<li>Şirketlerin finansal verilerini düzenli ve güvenilir şekilde indirmek</li>
<li>Manuel indirme sürecini otomatikleştirerek zamandan kazanmak</li>
<li>Verileri <code>companies/{Şirket Kodu} (TRY).xlsx</code> yapısında tutmak</li>
</ul>

<div class='section-title'>🧩 Teknik Yaklaşım</div>
<div class='info-box'>
Bazı veri kaynakları doğrudan HTTP isteklerine yanıt vermez. Bu nedenle özel bir <strong>Chrome profili</strong> ile tarayıcı otomasyonu kullanılır:
<ul>
  <li>Yeni bir kullanıcı profili açılır (<code>--user-data-dir</code>).</li>
  <li>Geliştirici ilk kez manuel giriş yapar.</li>
  <li>Selenium ile indirme sayfası açılır, Excel dosyası otomatik olarak indirilir.</li>
  <li>İndirilen dosya ilgili şirket klasörüne taşınır.</li>
</ul>
</div>

<div class='section-title'>🛠️ Geliştirici Notları</div>
<ul>
  <li>Chrome profili ve indirme dizini <code>Selenium</code> ile yapılandırılmıştır.</li>
  <li>Dosya <strong>yoksa</strong> veya <strong>3 günden eskiyse</strong> yeniden indirilir.</li>
  <li>İlk kullanımda Fintables’a giriş yapılmalıdır.</li>
  <li>Streamlit üzerinden güncellemeler tetiklenebilir.</li>
</ul>

<div class='section-title'>💡 Ekstra Özellikler</div>
<ul>
  <li><code>st.progress</code> ve <code>st.success</code> ile kullanıcıya durum bilgisi verilir</li>
  <li>Gelecekte zamanlanmış görevler veya çoklu şirket seçimi desteklenebilir</li>
</ul>
""", unsafe_allow_html=True)

