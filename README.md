# F1 InsightX 

An interactive Formula 1 dashboard built with **Streamlit** and **FastF1**. Visualise lap times, tyre strategies, and fastest lap telemetry with ease.

---

## 🚀 Features
- **Lap Time Analysis** — Explore lap times for each driver in a session
- **Tyre Strategy** — See tyre compound usage distributions
- **Telemetry** — Visualize fastest lap telemetry (speed, track map)
- **Easy Session Selection** — Choose any season (2018 → latest), race, and session (FP1, FP2, FP3, Qualifying, Sprint, Race)

---

## Installation
Clone the repo and install dependencies:

```bash
git clone https://github.com/YOUR-USERNAME/F1-InsightX.git
cd F1-InsightX
pip install -r requirements.txt
```

---

## Usage
Run the dashboard locally with Streamlit:

```bash
streamlit run dashboard.py
```

The app will open in your browser at `http://localhost:8501`.

---

## Project Structure
```
F1-InsightX/
├── dashboard.py        # Main Streamlit app
├── requirements.txt    # Dependencies
├── .gitignore          # Ignore cache/venv
├── ff1cache/           # FastF1 cache (ignored in Git)
└── README.md           # This file
```

---

## ☁️ Deploy to Streamlit Cloud
1. Push this repo to GitHub
2. Go to [Streamlit Cloud](https://share.streamlit.io/)
3. Link your GitHub repo and select `dashboard.py`

The app will build using `requirements.txt` and run in the cloud.

---

## 🙌 Acknowledgements
- [FastF1](https://theoehrly.github.io/Fast-F1/) — F1 telemetry and timing API
- [Streamlit](https://streamlit.io/) — Interactive dashboards in Python

---

### 🔗 Repo
👉 https://github.com/YOUR-USERNAME/F1-InsightX
