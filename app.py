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
    .recommendation-box {
        background: linear-gradient(135deg, #065f46 0%, #047857 100%);
        border: 2px solid #34d399;
        padding: 18px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2);
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
            Screener ISSI: Deteksi Saham Merah Hari Ini Menuju Reversal Potensi Minimal 6% (Volume Valid & Jenuh Jual)
        </p>
    </div>
""",
    unsafe_allow_html=True,
)


# --- 1. LOAD DATA TICKER ISSI DARI FILE EXCEL ---
@st.cache_data
def load_issi_from_excel():
  file_path = "SAHAM ISSI.xlsx"
  try:
    xls = pd.ExcelFile(file_path)
    df_raw = pd.read_excel(file_path, sheet_name=xls.sheet_names[0])

    tickers = []
    for val in df_raw.iloc[2:, 1].dropna():
      if isinstance(val, str) and len(val.strip()) <= 6:
        tickers.append(val.strip().upper())

    tickers = sorted(list(set(tickers)))
    if not tickers:
      tickers = ["ADRO", "ANTM", "PTBA", "INDF", "KLBF"]
    return tickers
  except Exception:
    return ["ADRO", "ANTM", "PTBA", "INDF", "KLBF"]


tickers_list = load_issi_from_excel()


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
    return current_price, change_pct
  except Exception:
    return 7200.0, 0.0


ihsg_price, ihsg_change = get_ihsg_data()


# --- 3. PANEL KONTROL DI HALAMAN UTAMA ---
st.markdown("### 🎛️ Panel Kontrol & Pengaturan Screener")
col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)

with col_ctrl1:
  screener_filter = st.selectbox(
      "🔍 Filter Fokus Screener:",
      [
          "🔥 Semua Saham Merah Potensi Reversal 6%+",
          "📊 Hanya Sinyal Akumulasi Volume Tinggi",
          "📉 Jenuh Jual Ekstrim (Oversold Bounce)",
      ],
  )

with col_ctrl2:
  min_potensi = st.slider(
      "🎯 Minimal Target Potensi Reversal (%):", 4.0, 15.0, 6.0, 0.5
  )

with col_ctrl3:
  st.markdown("<br>", unsafe_allow_html=True)
  refresh_clicked = st.button(
      "🔄 Refresh & Scan Market Real-Time", use_container_width=True
  )
  if refresh_clicked:
    st.cache_data.clear()
    st.rerun()

st.markdown("---")

# --- 4. RINGKASAN METRIK PASAR ---
m1, m2, m3, m4 = st.columns(4)
with m1:
  delta_class = (
      "metric-delta-pos" if ihsg_change >= 0 else "metric-delta-neg"
  )
  st.markdown(
      f"""
        <div class="metric-container">
            <div class="metric-label">IHSG Real-Time</div>
            <div class="metric-value">{ihsg_price:,.2f}</div>
            <div class="{delta_class}">{ihsg_change:+.2f}%</div>
        </div>
    """,
      unsafe_allow_html=True,
  )

with m2:
  st.markdown(
      f"""
        <div class="metric-container">
            <div class="metric-label">Total Pantauan ISSI</div>
            <div class="metric-value">{len(tickers_list)} Emiten</div>
            <div class="metric-yellow">Sistem Aktif</div>
        </div>
    """,
      unsafe_allow_html=True,
  )

with m3:
  st.markdown(
      """
        <div class="metric-container">
            <div class="metric-label">Kriteria Utama</div>
            <div class="metric-value">Merah ➔ Hijau</div>
            <div class="metric-yellow">Reversal Valid</div>
        </div>
    """,
      unsafe_allow_html=True,
  )

with m4:
  st.markdown(
      f"""
        <div class="metric-container">
            <div class="metric-label">Target Minimum</div>
            <div class="metric-value">+{min_potensi}%</div>
            <div class="metric-yellow">Potensi Pantulan</div>
        </div>
    """,
      unsafe_allow_html=True,
  )

st.markdown("<br>", unsafe_allow_html=True)


# --- 5. FUNGSI ANALISIS & SCREENING SAHAM ---
@st.cache_data(ttl=300)
def scan_red_to_green_stocks(tickers, min_target):
  results = []
  for t in tickers:
    symbol = f"{t}.JK"
    try:
      df = yf.download(
          symbol, period="3mo", interval="1d", progress=False, auto_adjust=False
      )
      if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

      if df.empty or len(df) < 30:
        continue

      close_s = df["Close"]
      open_s = df["Open"]
      high_s = df["High"]
      low_s = df["Low"]
      vol_s = df["Volume"]

      c_today = float(close_s.iloc[-1])
      o_today = float(open_s.iloc[-1])
      h_today = float(high_s.iloc[-1])
      l_today = float(low_s.iloc[-1])
      v_today = float(vol_s.iloc[-1])

      c_prev = float(close_s.iloc[-2])

      change_today = ((c_today - c_prev) / c_prev) * 100
      if change_today >= 0:
        intraday_recovery = (c_today > o_today) and (
            (c_today - l_today) / l_today > 0.015
        )
        if not intraday_recovery:
          continue
      else:
        intraday_recovery = (c_today > o_today) or (c_today >= l_today * 1.01)

      vol_sma5 = float(vol_s.rolling(window=5).mean().iloc[-1])

      delta = close_s.diff()
      gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
      loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
      rs = gain / loss
      rsi14 = float((100 - (100 / (1 + rs))).iloc[-1])
      jenuh_jual = rsi14 <= 48

      hist_volatility = (
          (high_s - low_s) / close_s
      ).rolling(window=14).mean().iloc[-1] * 10
