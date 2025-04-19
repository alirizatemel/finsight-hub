# FinSight Hub

> **A multi‑page Streamlit toolkit that turns your Fintables‑exported Borsa İstanbul spreadsheets into instant, shareable insights.**

---

## ✨ Key Features

- **Modular architecture** – shared logic lives in `modules/`, while every page in `pages/` becomes a tab in the UI.
- **Built‑in financial ratios** – Piotroski F‑Skor, Beneish M‑Skor, Graham & Peter Lynch scores, custom radar charts, and more.
- **Excel‑first workflow** – just drop the **Fintables** XLSX exports (each at `companies/<SYMBOL>/<SYMBOL> (TRY).xlsx` with *Bilanço*, *Gelir Tablosu (Dönemsel)* and *Nakit Akış (Dönemsel)* sheets) and start exploring.
- **Snappy Streamlit UI** – widgets, metrics, and cached data loaders keep interaction times low.
- **100 % Python** – easy to extend, easy to deploy (Streamlit Cloud, Hugging Face, Docker, Heroku… you name it).

---

## 🗂️ Project Layout

```text
finsight_hub/                     # ← repo root
│
├── app.py                        # Streamlit entry point (router)
├── requirements.txt              # PyPI deps
│
├── modules/                      # Re‑usable business logic
│   ├── __init__.py
│   ├── data_loader.py            # → load_company_xlsx()
│   └── calculations.py           # → f_score(), graham_score(), ...
│
├── pages/                        # Every file = a Streamlit page
│   ├── 1_📊_Bilanco_Radar.py
│   └── 2_📈_Tek_Hisse_Analizi.py
│
└── companies/                    # Your Fintables Excel statements
    └── ASELS/ASELS (TRY).xlsx
```

> **Why this layout?**
> `modules/` keeps non‑UI code testable and DRY, while `pages/` leverages Streamlit’s automatic multipage navigation.

---

## 🚀 Quick Start

```bash
# 1.  Clone & enter the repo
$ git clone https://github.com/your‑org/finsight_hub.git
$ cd finsight_hub

# 2.  Create a virtual environment (Python ≥ 3.10 recommended)
$ python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3.  Install dependencies
$ pip install -r requirements.txt

# 4.  Export statements from Fintables and place them in ./companies/
$ tree companies -L 2
companies/
└── ASELS/
    └── ASELS (TRY).xlsx

# 5.  Run the app
$ streamlit run app.py
```

### Optional Docker run

```bash
# Build
$ docker build -t finsight_hub .
# Serve on http://localhost:8501
$ docker run -p 8501:8501 -v $PWD/companies:/app/companies finsight_hub
```

---

## ⚙️ Configuration

| Setting                         | Where                              | Default | Notes |
|---------------------------------|------------------------------------|---------|-------|
| **Excel directory**             | `load_company_xlsx(base_dir=...)`  | `companies/` | One sub‑folder per ticker. |
| **Cache TTL**                   | `@st.cache_data(ttl=3600)`         | `3600 s` | Increase if files rarely change. |
| **Page order & labels**         | Prefix (`1_`, `2_`) + emoji        | N/A     | Feel free to rename pages! |

---

## 🧑‍💻 Contributing

1. Fork → create feature branch (`git checkout -b feat/my‑amazing‑idea`)
2. Commit tests/docs (run `pre‑commit run --all-files` if you use it)
3. Push & open a PR.

All major contributions require one approving review—feel free to request one.

---

## 📜 License

This project is licensed under the **MIT License** – see [`LICENSE`](LICENSE) for details.

---

## 🙏 Acknowledgements

- **Fintables** for providing the financial statement Excel exports that power this analysis.
- Streamlit team for the awesome framework.
- `pandas`, `numpy`, and `matplotlib` for doing the heavy lifting.
- Thanks to the original Jupyter notebooks (*bilanco_radar.ipynb* & *tek_hisse_analizi.ipynb*) that inspired this consolidation.

Happy analyzing! 🎉
