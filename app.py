from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="SAHAM MERAH BESOK HIJAU", page_icon="📈", layout="wide"
)

# Custom CSS untuk Judul Kotak Hijau Tulisan Merah dan Komponen Lainnya
st.markdown(
    """
<style>
    .title-box {
        background-color: #d1fae5;
        border: 2px solid #10b981;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .title-text {
        font-size: 32px;
        font-weight: bold;
        color: #ef4444 !important; /* Warna Merah */
        letter-spacing: 1px;
    }
    .metric-container {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-label {
        font-size: 15px;
        color: #94a3b8;
        font-weight: 600;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 26px;
        font-weight: bold;
        color: #f8fafc;
    }
    .metric-delta-pos {
        font-size: 16px;
        font-weight: bold;
        color: #22c55e;
    }
    .metric-delta-neg {
        font-size: 16px;
        font-weight: bold;
        color: #ef4444;
    }
    .metric-yellow {
        font-size: 18px;
        font-weight: bold;
        color: #eab308;
    }
    .control-panel {
        background-color: #0f172a;
        border: 1px solid #1e293b;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 25px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# --- JUDUL UTAMA DI DALAM KOTAK HIJAU DENGAN TULISAN MERAH ---
st.markdown(
    """
    <div class="title-box">
        <div class="title-text">SAHAM MERAH BESOK HIJAU</div>
        <p style="color: #065f46 !important; font-size: 15px; margin-top: 5px; font-weight: 600;">
            Screener JII70: Deteksi Saham Koreksi Sehat (Jenuh Jual) Menuju Reversal Target Potensi Minimal 6%
        </p>
    </div>
""",
    unsafe_allow_html=True,
)


# --- 1. LOAD DATA TICKER JII70 DARI FILE EXCEL ---
@st.cache_data
def load_jii70_from_excel():
  file_path = "JII70 TICKER1.xlsx"
  try:
    xls = pd.ExcelFile(file_path)
    df_raw = pd.read_excel(file_path, sheet_name=xls.sheet_names[0])

    tickers = []
    for col in df_raw.columns:
      if isinstance(col, str) and len(col) <= 6 and col.upper() != "UNNAMED":
        tickers.append(col.strip().upper())
    for val in df_raw.iloc[:, 1].dropna():
      if isinstance(val, str) and len(val.strip()) <= 6:
        tickers.append(val.strip().upper())

    tickers = sorted(list(set(tickers)))
    if not tickers:
      tickers = [
          "ACES",
          "ADMR",
          "ADRO",
          "AKRA",
          "ANTM",
          "BRIS",
          "ICBP",
          "INDF",
          "KLBF",
          "MDKA",
          "PGAS",
          "PTBA",
          "UNVR",
      ]
    return tickers
  except Exception:
    return [
        "ACES",
        "ADMR",
        "ADRO",
        "AKRA",
        "ANTM",
        "BRIS",
        "ICBP",
        "INDF",
        "KLBF",
        "MDKA",
        "PGAS",
        "PTBA",
        "UNVR",
    ]


tickers_list = load_jii70_from_excel()


# --- 2. AMBIL DATA REAL-TIME IHSG (^JKSE) ---
@st.cache_data(ttl=60)
def get_ihsg_data():
  try:
    ihsg = yf.Ticker("^JKSE")
    hist = ihsg.history(period="5d")
    if len(hist) >= 2:
      current_price = float(hist["Close"].iloc[-1])
      prev_close = float(hist["Close"].iloc[-2])
      change_pct = ((current_price - prev_close) / prev_close) * 100
    else:
      current_price = (
          float(hist["Close"].iloc[-1]) if len(hist) > 0 else 7200.0
      )
      change_pct = 0.0
    return current_price, float(change
