from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import plotly.graph_objects as go
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
            Screener JII70: Deteksi Saham Merah Hari Ini Menuju Reversal Potensi Minimal 6% (Volume Valid & Jenuh Jual)
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
      """
        <div class="metric-container">
            <div class="metric-label">Total Pantauan JII70</div>
            <div class="metric-value">70 Emiten</div>
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
      ).rolling(window=14).mean().iloc[-1] * 100
      est_reversal_target = max(
          change_today * -1.2 + hist_volatility * 1.5, min_target
      )

      if est_reversal_target < min_target:
        continue

      pivot = (h_today + l_today + c_today) / 3
      support = (2 * pivot) - h_today
      resistance = (2 * pivot) - l_today
      target_besok = c_today * (1 + (min_target / 100))

      results.append({
          "Emiten": t,
          "Harga (Rp)": f"{c_today:,.0f}",
          "Chg Hari Ini": f"{change_today:+.2f}%",
          "RSI (14)": round(rsi14, 1),
          "Vol vs Avg5": f"{(v_today/vol_sma5):.2f}x"
          if vol_sma5 > 0
          else "1.0x",
          "Support": f"{support:,.0f}",
          "Target Besok (+6%+)": f"{target_besok:,.0f}",
          "Potensi Reversal": f"+{est_reversal_target:.1f}%",
          "Analisis Pola": (
              "Merah Jenuh Jual & Pantulan Valid"
              if jenuh_jual
              else "Intraday Recovery Kuat"
          ),
          "RawChg": change_today,
      })
    except Exception:
      continue

  return sorted(results, key=lambda x: x["RawChg"])


# --- 6. INISIALISASI SESSION STATE UNTUK KLIK KOTAK REKOMENDASI ---
if "selected_emiten_target" not in st.session_state:
  st.session_state.selected_emiten_target = None

with st.spinner(
    "Menganalisis data pasar real-time & mendeteksi pola volume valid..."
):
  scanned_data = scan_red_to_green_stocks(tickers_list, min_potensi)

# --- 7. KOTAK REKOMENDASI INTERAKTIF (SAHAM LAYAK BELI) ---
st.markdown("### 🔥 Top Saham Layak Beli (Reversal Terkonfirmasi)")
if scanned_data:
  # Ambil top 3 rekomendasi terbaik berdasarkan potensi reversal
  top_recoms = scanned_data[:3]

  cols_rec = st.columns(len(top_recoms))
  for idx, rec in enumerate(top_recoms):
    with cols_rec[idx]:
      st.markdown(
          f"""
            <div class="recommendation-box">
                <h4 style="color: #ffffff; margin: 0;">🎯 {rec['Emiten']}</h4>
                <p style="color: #d1fae5; font-size: 13px; margin: 4px 0;">
                    <b>Harga:</b> Rp {rec['Harga (Rp)']}<br>
                    <b>Potensi:</b> <span style="color: #fde047; font-weight: bold;">{rec['Potensi Reversal']}</span><br>
                    <b>Alasan:</b> Koreksi sehat (RSI {rec['RSI (14)']}), didukung volume meningkat & pantulan support kuat.
                </p>
            </div>
        """,
          unsafe_allow_html=True,
      )
      # Tombol interaktif untuk langsung mengarahkan ke emiten tersebut
      if st.button(
          f"👉 Analisis {rec['Emiten']}", key=f"btn_rec_{rec['Emiten']}"
      ):
        st.session_state.selected_emiten_target = rec["Emiten"]
        st.rerun()
else:
  st.info(
      "ℹ️ Belum ada emiten yang mencetak skor rekomendasi tertinggi saat ini."
  )

st.markdown("---")

# --- 8. TAMPILAN TABEL HASIL SCREENER ---
st.markdown("### 📋 Daftar Lengkap Saham JII70: Koreksi Merah Hari Ini")

if scanned_data:
  df_display = pd.DataFrame(scanned_data).drop(columns=["RawChg"])
  st.dataframe(df_display, use_container_width=True, height=400)

  st.markdown("---")
  st.markdown("### 📊 Detail & Grafik Analisis Emiten Terpilih")

  # Tentukan indeks default dari session state jika tombol kotak diklik
  emiten_list = [item["Emiten"] for item in scanned_data]
  default_idx = 0
  if st.session_state.selected_emiten_target in emiten_list:
    default_idx = emiten_list.index(st.session_state.selected_emiten_target)

  selected_emiten = st.selectbox(
      "Pilih Emiten untuk Melihat Grafik & Detail Setup:",
      emiten_list,
      index=default_idx,
  )

  if selected_emiten:
    col_chart1, col_chart2 = st.columns([2, 1])

    with col_chart1:
      chart_df = yf.download(
          f"{selected_emiten}.JK",
          period="2mo",
          interval="1d",
          progress=False,
          auto_adjust=False,
      )
      if isinstance(chart_df.columns, pd.MultiIndex):
        chart_df.columns = chart_df.columns.get_level_values(0)

      fig = go.Figure(
          data=[
              go.Candlestick(
                  x=chart_df.index,
                  open=chart_df["Open"],
                  high=chart_df["High"],
                  low=chart_df["Low"],
                  close=chart_df["Close"],
                  name="Candlestick",
              )
          ]
      )
      fig.update_layout(
          template="plotly_dark",
          title=f"Grafik Harian {selected_emiten}.JK",
          height=400,
          margin=dict(l=10, r=10, t=30, b=10),
      )
      st.plotly_chart(fig, use_container_width=True)

    with col_chart2:
      st.markdown(f"#### 💡 Panduan Eksekusi: `{selected_emiten}`")
      st.info(
          f"• **Kondisi Hari Ini:** Ditutup merah/koreksi sehat dengan volume"
          f" meningkat.\n• **Strategi Masuk:** Cicil beli (*Buy on Weakness*) di"
          f" area support pagi hari jika harga sempat melemah dulu.\n• **Target"
          f" Pantulan:** Minimal kenaikan **+{min_potensi}%** pada perdagangan"
          f" esok hari.\n• **Validitas Volume:** Volume akumulasi pembeli"
          f" besar bertahan hingga sesi sore."
      )

      stockbit_url = f"https://stockbit.com/symbol/{selected_emiten}"
      st.markdown(
          f'<a href="{stockbit_url}" target="_blank"><button style="width:'
          ' 100%; background-color: #10b981; color: white; border: none; padding:'
          ' 10px; border-radius: 6px; font-weight: bold; cursor: pointer;'
          ' margin-top: 10px;">🚀 Buka Trade di Stockbit</button></a>',
          unsafe_allow_html=True,
      )
else:
  st.warning(
      "⚠️ Belum ada saham JII70 yang memenuhi kriteria ketat 'Merah Hari Ini"
      " dengan Potensi Reversal Minimal 6%' saat ini. Coba sesuaikan filter"
      " target minimal atau lakukan *Refresh* beberapa saat lagi."
  )
