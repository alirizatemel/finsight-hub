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
- **Excel odaklı iş akışı** – Fintables şirket finans tablolarının çıktıklarını (`companies/<SEMBOL> (TRY).xlsx`) analiz eder.
- **Skor filtreleme paneli** – F, M, Lynch, Graham skorlarına göre yatırıma uygun hisseleri süz.
- **MOS (Margin of Safety)** – Skor kartlarında MOS yüzdesiyle hesaplanır ve filtrelemeye dahil edilir.
- **FCF analiz sekmesi** – Şirketin serbest nakit akışı zaman serisi grafiklerle sunulur.
- **Monte Carlo DCF** – FCF verilerine dayalı olarak içsel değeri senaryo bazlı hesaplar.
- **Log görüntüleme** – `scanner.log` içeriği arayüzden izlenebilir.
- **Bilanco indirici** – Eksik veya eski Excel dosyalarını Fintables'tan otomatik indirir.
- **Tamamen Python** – Genişletmesi kolay, yayına alması kolay (Streamlit Cloud, Hugging Face, Docker, Heroku... ne istersen).

---

(`companies/<SEMBOL> (TRY).xlsx`) klasörüne koyulmalı, ayrıca Fintables - Hisseler sayfasında

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
│   ├── 02_stock_analysis.py
│   └── 03_balance_download.py
│
├── data/
    └── companies/
        ├── ASELS (TRY).xlsx
        ├── THYAO (TRY).xlsx
        ...
    └── fintables_radar.xlsx
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
$ python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scriptsctivate

# 3. Bağımlılıkları yükle
$ pip install -r requirements.txt

# 4. Fintables'tan Excel çıktıklarını ./data/companies/ altına koy
$ tree data/companies -L 1
companies/
├── ASELS (TRY).xlsx
├── THYAO (TRY).xlsx
...

# 5. Uygulamayı çalıştır
$ streamlit run app.py
```

---

## 📥 Veri Hazırlığı

FinSight Hub uygulamasının çalışabilmesi için `data/companies/` klasörüne hisse bazlı Excel dosyaları eklenmelidir.

### 1. Şirket Bazlı Excel Dosyaları

Her şirket için Fintables platformundan indirilen mali tablo dosyaları şu formatta yerleştirilmelidir:
```text
    data/
    └── companies/
        ├── ASELS (TRY).xlsx
        ├── THYAO (TRY).xlsx
        ...
```

> 🔹 Bu dosyalar Fintables’ın **şirket detay sayfalarından** alınan bilanço, gelir tablosu ve nakit akış verilerini içermelidir.

### 2. Toplu Liste Excel Dosyası 

Fintables’ın **“Hisseler”** sekmesinden alınan ve tüm şirketlere ait özet verileri içeren bir dosya da aynı klasöre eklenmelidir.

Bu Excel dosyasında şu sütun başlıkları yer almalıdır:

`Şirket`, `Son Fiyat`, `Gün %`, `Hacim`, `Piyasa Değeri`, `Net Dönem Karı`, `İşletme Faaliyetlerinden Nakit Akışları`, `Finansman Faaliyetlerinden Nakit Akışları`, `Yıllıklandırılmış Serbest Nakit Akışı`, `Yatırım Faaliyetlerinden Nakit Akışları`, `Nakitlerdeki Değişim`, `Çeyreklik Serbest Nakit Akışı`, `Yıllık İşletme Faaliyetleri Nakit Akış Değişimi`, `Net Borç`, `Dönen Varlıklar`, `Kısa Vadeli Yükümlülükler`, `Brüt Kar`, `Satışlar`, `Toplam Varlıklar`, `Özkaynaklar`, `F/K`, `Cari Oran`, `PD/DD`, `FD/FAVÖK`, `FD/Satış`, `PEG`

> 📌 **Not:** Dosya adı `fintables_radar.xlsx` olabilir. Önemli olan yukarıdaki sütun adlarının birebir bulunmasıdır.


---

## ⚙️ Yapılandırma

| Ayar                          | Nerede                              | Varsayılan | Notlar |
|------------------------------|-------------------------------------|-------------|--------|
| **Excel klasörü**           | `load_company_xlsx(base_dir=...)`  | `companies/` | Dosyalar tek katmanda tutulur |
| **Cache süresi (TTL)**     | `@st.cache_data(ttl=3600)`         | `3600 s`    | Dosyalar nadiren değişiyorsa artırılabilir |
| **Sayfa sırası & etiket**  | Ön ek (`1_`, `2_`)        | Yok        | Sayfa adlarını dilediğin gibi değiştirebilirsin |

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