# 📊 FinSight Hub

> **Fintables’tan dışa aktarılan Borsa İstanbul Excel tablolarını, hızlı ve paylaşılabilir finansal analizlere dönüştüren çok sayfalı bir Streamlit aracı.**

---

## 🙏 Teşekkür

**Fintables** ekibine, bu projede kullanılan örnek verilerin paylaşılmasına izin verdikleri için özellikle teşekkür ederiz.

---

## 🎯 Projenin Amacı

FinSight Hub, bireysel ya da kurumsal yatırımcıların Borsa İstanbul şirketlerine ait mali tabloları kolayca analiz edebilmesi için geliştirilmiş açık kaynaklı bir analiz platformudur. Excel’den başka hiçbir araca ihtiyaç duymadan, sadece Fintables verileriyle:

- Şirketin mali yapısı ve finansal sağlığı hızlıca anlaşılır.
- Yatırım yapılabilirlik açısından farklı metrikler (Piotroski, Graham, Lynch, Beneish) ile skorlamalar sunulur.
- Serbest nakit akışı (FCF) üzerinden şirketin değerleme uygunluğu yorumlanabilir.

Bu projeyle hedeflenen:
- 📉 Finansal okuryazarlığı artırmak
- 🔍 Şirket analizini standartlaştırmak
- 🚀 Excel ile Python arasında bir köprü kurarak yatırım analizini demokratikleştirmektir.

Veriye dayalı karar almak isteyen herkes için pratik ve esnek bir analiz platformu sunar.

---

## ✨ Temel Özellikler

- **Modüler yapı** – Ortak iş mantığı `modules/` klasöründedir; her `pages/` dosyası Streamlit arayüzünde bir sekme olur.
- **Hazır finansal oranlar** – Piotroski F-Skor, Beneish M-Skor, Graham & Peter Lynch skorları, özel radar grafikler ve daha fazlası.
- **Excel odaklı iş akışı** – Tek yapman gereken, Fintables çıktıklarını (`companies/<SEMBOL>/<SEMBOL> (TRY).xlsx`) klasörüne koymak ve analiz etmeye başlamak.
- **Akıcı Streamlit arayüzü** – Widget'lar, metrikler ve önbellek sistemi ile yüksek performans.
- **Tamamen Python** – Genişletmesi kolay, yayına alması kolay (Streamlit Cloud, Hugging Face, Docker, Heroku... ne istersen).

---

## 🗂️ Proje Yapısı

```text
finsight_hub/                     # ← depo kök dizini
│
├── app.py                        # Streamlit başlangıç dosyası
├── requirements.txt              # Bağımlılıklar
│
├── modules/                      # Yeniden kullanılabilir iş mantığı
│   ├── __init__.py
│   ├── data_loader.py            # → load_company_xlsx()
│   └── calculations.py           # → f_score(), graham_score(), ...
│
├── pages/                        # Her dosya = bir Streamlit sayfası
│   ├── 01_financial_radar.py
│   └── 02_stock_analysis.py
│
└── companies/                    # Fintables Excel tabloların
    └── ASELS/ASELS (TRY).xlsx
```

> **Neden bu yapı?**  
> `modules/` iş mantığını test edilebilir tutar; `pages/` ise Streamlit'in çok sayfa desteğinden yararlanır.

---

## 🚀 Hızlı Başlangıç

```bash
# 1. Repoyu klonla
$ git clone https://github.com/alirizatemel/finsight-hub.git
$ cd finsight-hub

# 2. Sanal ortam oluştur (Python ≥ 3.10 önerilir)
$ python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Bağımlılıkları yükle
$ pip install -r requirements.txt

# 4. Fintables'tan Excel çıktıklarını ./companies/ altına koy
$ tree companies -L 2
companies/
└── ASELS/
    └── ASELS (TRY).xlsx

# 5. Uygulamayı çalıştır
$ streamlit run app.py
```

### (Opsiyonel) Docker ile çalıştırma

```bash
# İmajı oluştur
$ docker build -t finsight-hub .
# http://localhost:8501 adresinden başlat
$ docker run -p 8501:8501 -v $PWD/companies:/app/companies finsight-hub
```

---

## ⚙️ Yapılandırma

| Ayar                          | Nerede                              | Varsayılan | Notlar |
|------------------------------|-------------------------------------|-------------|--------|
| **Excel klasörü**           | `load_company_xlsx(base_dir=...)`  | `companies/` | Her sembol için bir alt klasör |
| **Cache süresi (TTL)**     | `@st.cache_data(ttl=3600)`         | `3600 s`    | Dosyalar nadiren değişiyorsa artırılabilir |
| **Sayfa sırası & etiket**  | Ön ek (`1_`, `2_`) + emoji        | Yok        | Sayfa adlarını dilediğin gibi değiştirebilirsin |

---

## 🧑‍💻 Katkıda Bulunma

1. Forkla → yeni bir özellik dalı oluştur (`git checkout -b ozellik/super-fikir`)
2. Değişiklikleri yap ve commit et (isteğe bağlı: `pre-commit run --all-files`)
3. PR açarak katkı sağla!

Büyük katkılar en az bir onay gerektirir – birini etiketlemekten çekinme.

---

## 📜 Lisans

Bu proje **MIT Lisansı** ile sunulmaktadır – detaylar için [`LICENSE`](LICENSE) dosyasına bakabilirsiniz.

---

## 🙏 Teşekkürler

- **Fintables** ekibine, finansal tablo Excel çıktıklarını sağladıkları için sonsuz teşekkürler.
- Streamlit ekibine bu muhteşem framework için.
- `pandas`, `numpy`, `matplotlib` kütüphanelerine alt yapı gücü için.
- Orijinal Jupyter notebook geliştiricilerine (*bilanco_radar.ipynb* & *tek_hisse_analizi.ipynb*) ilhamları için.

Keyifli analizler! 🎉
