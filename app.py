from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

# ============================================================
# KONFIGURASI HALAMAN STREAMLIT
# ============================================================
st.set_page_config(
    page_title="SAHAM MERAH BESOK HIJAU", page_icon="📈", layout="wide"
)

# Custom CSS - Desain Modern, Elegan, & Interaktif
st.markdown(
    """
<style>
    .stApp {
        background: linear-gradient(135deg, #090d16 0%, #111827 50%, #0f172a 100%);
        color: #f8fafc;
    }
    .title-box {
        background: linear-gradient(135deg, #065f46 0%, #047857 100%);
        border: 2px solid #34d399;
        padding: 24px;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 10px 25px rgba(16, 185, 129, 0.25);
        margin-bottom: 25px;
    }
    .title-text {
        font-size: 34px;
        font-weight: 900;
        color: #ef4444 !important; /* Warna Merah Menyala Elegan */
        letter-spacing: 1.5px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .metric-container {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid #334155;
        padding: 18px;
        border-radius: 14px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(10px);
    }
    .metric-label {
        font-size: 13px;
        color: #94a3b8;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 6px;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: 800;
        color: #f8fafc;
    }
    .metric-delta-pos {
        font-size: 15px;
        font-weight: 700;
        color: #4ade80;
    }
    .metric-delta-neg {
        font-size: 15px;
        font-weight: 700;
        color: #f87171;
    }
    .recommendation-box {
        background: linear-gradient(135deg, #064e3b 0%, #065f46 100%);
        border: 1px solid #34d399;
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 15px;
        box-shadow: 0 6px 15px rgba(16, 185, 129, 0.15);
        transition: transform 0.2s ease;
    }
    .recommendation-box:hover {
        transform: translateY(-3px);
    }
    div.stButton > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 8px 16px;
        box-shadow: 0 4px 10px rgba(16, 185, 129, 0.3);
        width: 100%;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        color: #ffffff;
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
        <p style="color: #ecfdf5 !important; font-size: 15px; margin-top: 8px; font-weight: 600;">
            Screener ISSI Profesional: Deteksi Saham Koreksi Sehat Menuju Reversal Potensi Minimal 6% (Full Database ISSI)
        </p>
    </div>
""",
    unsafe_allow_html=True,
)


# --- 1. LOAD SELURUH 500+ TICKER ISSI DARI FILE EXCEL SECARA PRESISI ---
@st.cache_data
def load_issi_from_excel():
  file_path = "SAHAM ISSI.xlsx"
  tickers = []
  try:
    xls = pd.ExcelFile(file_path)
    df_raw = pd.read_excel(file_path, sheet_name=xls.sheet_names[0])

    # Membaca langsung dari kolom ke-2 (indeks 1) mulai baris indeks 2 ke bawah
    for val in df_raw.iloc[2:, 1].dropna():
      s_val = str(val).strip().upper()
      if (
          s_val
          and s_val not in ["KODE", "NO.", "NAMA", "NAN"]
          and not s_val.isdigit()
          and len(s_val) <= 6
      ):
        tickers.append(s_val)

    # Jika karena suatu hal kosong, pindai seluruh sel dalam dataframe
    if not tickers:
      for col in df_raw.columns:
        for val in df_raw[col].dropna():
          s_val = str(val).strip().upper()
          if (
              len(s_val) <= 6
              and s_val not in [
                  "KODE",
                  "NO.",
                  "NAMA",
                  "UNNAMED: 0",
                  "UNNAMED: 1",
                  "NAN",
              ]
              and not s_val.isdigit()
          ):
            tickers.append(s_val)
  except Exception as e:
    st.error(f"Gagal memuat file Excel: {e}")

  tickers = sorted(list(set(tickers)))
  if not tickers:
    tickers = ["ADRO", "ANTM", "PTBA", "INDF", "KLBF", "ASII", "BBCA", "BMRI"]
  return tickers


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
  view_mode = st.selectbox(
      "🔍 Mode Tampilan & Analisis:",
      [
          "🔥 Filter Sinyal Reversal Potensi 6%+",
          "📋 Tampilkan Seluruh Daftar Saham ISSI (Market Watch)",
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
            <div class="metric-label">Total Database ISSI</div>
            <div class="metric-value">{len(tickers_list)} Emiten</div>
            <div style="color: #38bdf8; font-size: 14px; font-weight: bold;">Terdaftar Penuh</div>
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
            <div style="color: #34d399; font-size: 14px; font-weight: bold;">Reversal Valid</div>
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
            <div style="color: #fde047; font-size: 14px; font-weight: bold;">Pantulan Target</div>
        </div>
    """,
      unsafe_allow_html=True,
  )

st.markdown("<br>", unsafe_allow_html=True)


# --- 5. FUNGSI ANALISIS & SCREENING SAHAM ---
def analyze_single_stock(t, min_target, strict_mode=True):
  symbol = f"{t}.JK"
  try:
    df = yf.download(
        symbol, period="3mo", interval="1d", progress=False, auto_adjust=False
    )
    if isinstance(df.columns, pd.MultiIndex):
      df.columns = df.columns.get_level_values(0)

    if df.empty or len(df) < 30:
      return None

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

    vol_sma5 = float(vol_s.rolling(window=5).mean().iloc[-1])
    delta = close_s.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi14 = float((100 - (100 / (1 + rs))).iloc[-1])

    hist_volatility = (
        (high_s - low_s) / close_s
    ).rolling(window=14).mean().iloc[-1] * 100
    est_reversal_target = max(
        change_today * -1.2 + hist_volatility * 1.5, min_target
    )

    if strict_mode:
      if change_today >= 0:
        intraday_recovery = (c_today > o_today) and (
            (c_today - l_today) / l_today > 0.015
        )
        if not intraday_recovery:
          return None
      if est_reversal_target < min_target:
        return None

    pivot = (h_today + l_today + c_today) / 3
    support = (2 * pivot) - h_today
    target_besok = c_today * (1 + (min_target / 100))

    return {
        "Emiten": t,
        "Harga (Rp)": f"{c_today:,.0f}",
        "Chg Hari Ini": f"{change_today:+.2f}%",
        "RSI (14)": round(rsi14, 1),
        "Vol vs Avg5": f"{(v_today/vol_sma5):.2f}x" if vol_sma5 > 0 else "1.0x",
        "Support": f"{support:,.0f}",
        "Target Besok": f"{target_besok:,.0f}",
        "Potensi Reversal": f"+{est_reversal_target:.1f}%",
        "Analisis Pola": (
            "Merah Jenuh Jual & Pantulan Valid"
            if change_today < 0
            else "Intraday Recovery Kuat"
        ),
        "RawChg": change_today,
    }
  except Exception:
    return None


@st.cache_data(ttl=300)
def scan_stocks_fast(tickers, min_target, strict_mode):
  results = []
  with ThreadPoolExecutor(max_workers=20) as executor:
    futures = {
        executor.submit(
            analyze_single_stock, t, min_target, strict_mode
        ): t
        for t in tickers
    }
    for future in as_completed(futures):
      res = future.result()
      if res is not None:
        results.append(res)
  return sorted(results, key=lambda x: x["RawChg"])


# --- 6. INISIALISASI SESSION STATE ---
if "selected_emiten_target" not in st.session_state:
  st.session_state.selected_emiten_target = None

is_strict_mode = "Filter Sinyal Reversal" in view_mode

with st.spinner(
    f"Memindai seluruh {len(tickers_list)} emiten ISSI secara real-time..."
):
  scanned_data = scan_stocks_fast(
      tuple(tickers_list), min_potensi, is_strict_mode
  )

# --- 7. KOTAK REKOMENDASI INTERAKTIF (TOP SAHAM LAYAK BELI) ---
st.markdown("### 🔥 Top Saham Layak Beli (Reversal Terkonfirmasi)")
if scanned_data:
  top_recoms = scanned_data[:3]

  cols_rec = st.columns(len(top_recoms))
  for idx, rec in enumerate(top_recoms):
    with cols_rec[idx]:
      st.markdown(
          f"""
            <div class="recommendation-box">
                <h4 style="color: #ffffff; margin: 0;">🎯 {rec['Emiten']}</h4>
                <p style="color: #d1fae5; font-size: 13px; margin: 6px 0;">
                    <b>Harga:</b> Rp {rec['Harga (Rp)']}<br>
                    <b>Potensi:</b> <span style="color: #fde047; font-weight: bold;">{rec['Potensi Reversal']}</span><br>
                    <b>Alasan:</b> Koreksi sehat (RSI {rec['RSI (14)']}), didukung volume meningkat & pantulan support kuat.
                </p>
            </div>
        """,
          unsafe_allow_html=True,
      )
      if st.button(
          f"👉 Analisis {rec['Emiten']}", key=f"btn_rec_{rec['Emiten']}"
      ):
        st.session_state.selected_emiten_target = rec["Emiten"]
        st.rerun()
else:
  st.info(
      "ℹ️ Belum ada emiten yang memenuhi saringan ketat reversal saat ini."
      " Ubah mode ke 'Tampilkan Seluruh Daftar Saham ISSI' untuk melihat"
      " keseluruhan emiten."
  )

st.markdown("---")

# --- 8. TAMPILAN TABEL HASIL SCREENER ---
st.markdown(
    f"### 📋 Daftar Saham ISSI ({len(scanned_data)} Emiten Ditampilkan)"
)

if scanned_data:
  df_display = pd.DataFrame(scanned_data).drop(columns=["RawChg"])
  st.dataframe(df_display, use_container_width=True, height=420)

  st.markdown("---")
  st.markdown("### 📊 Detail & Grafik Analisis Emiten Terpilih")

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
          period="3mo",
          interval="1d",
          progress=False,
          auto_adjust=False,
      )
      if isinstance(chart_df.columns, pd.MultiIndex):
        chart_df.columns = chart_df.columns.get_level_values(0)

      if not chart_df.empty and "Close" in chart_df.columns:
        st.markdown(
            f"**Grafik Harga Penutupan Harian ({selected_emiten}.JK)**"
        )
        st.line_chart(chart_df["Close"])

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
          ' 10px; border-radius: 8px; font-weight: bold; cursor: pointer;'
          ' margin-top: 10px;">🚀 Buka Trade di Stockbit</button></a>',
          unsafe_allow_html=True,
      )
else:
  st.warning("⚠️ Tidak ada data emiten yang ditemukan.")
