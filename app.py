from collections import Counter
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Xóc Đĩa Pro - Mobile Optimized", layout="centered"
)

# --- CSS TÙY CHỈNH GIAO DIỆN DI ĐỘNG & THU NHỎ THÔNG BÁO ---
st.markdown("""
    <style>
    div.stButton > button {
        height: 55px;
        font-size: 18px !important;
        font-weight: bold;
        border-radius: 10px;
        background-color: #f8f9fa;
        border: 2px solid #cbd5e1;
        color: #1e293b;
    }
    div.stButton > button:hover {
        background-color: #ef4444;
        color: white;
        border-color: #ef4444;
    }
    .block-container {
        padding-top: 0.8rem;
        padding-bottom: 2rem;
        padding-left: 0.8rem;
        padding-right: 0.8rem;
    }
    .stAlert {
        padding: 6px 12px !important;
        font-size: 14px !important;
        margin-bottom: 0.5rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# Khởi tạo session state lưu lịch sử
if "history" not in st.session_state:
  st.session_state.history = []

st.title("🎲 Xóc Đĩa Pro (Mobile)")


# --- PHẦN 1: CÀI ĐẶT THÔNG SỐ VỐN & CHIẾN THUẬT ---
st.sidebar.header("⚙️ Cài Đặt Vốn & Cược")
total_capital = st.sidebar.number_input(
    "Tổng Vốn (VNĐ):", min_value=100000, value=5000000, step=100000
)
base_bet = st.sidebar.number_input(
    "Mức Cược Gốc (VNĐ):", min_value=10000, value=100000, step=10000
)

betting_strategy = st.sidebar.selectbox(
    "Chiến thuật vào tiền:",
    [
        "Đều tay (Flat Betting)",
        "Gấp thếp (Martingale: x2)",
        "Fibonacci (1, 1, 2, 3, 5...)",
    ],
)

stop_loss_pct = st.sidebar.slider("Cắt Lỗ (%):", 5, 50, 25)
take_profit_pct = st.sidebar.slider("Chốt Lãi (%):", 5, 100, 40)

stop_loss_amount = total_capital * (stop_loss_pct / 100)
take_profit_amount = total_capital * (take_profit_pct / 100)

st.sidebar.markdown("---")
st.sidebar.markdown(f"🛑 **Cắt Lỗ:** -{stop_loss_amount:,.0f}")
st.sidebar.markdown(f"🎯 **Chốt Lãi:** +{take_profit_amount:,.0f}")


# --- PHẦN 2: BÀN PHÍM NHẬP LIỆU TO (0, 1, 2, 3, 4) ---
st.markdown("### ⌨️ Nhập Kết Quả")
cols_btn = st.columns(6)

label_map = {0: "0 Đỏ", 1: "1 Đỏ", 2: "2 Đỏ", 3: "3 Đỏ", 4: "4 Đỏ"}
odds_map = {0: 16.0, 1: 4.8, 2: 3.6, 3: 4.8, 4: 16.0}

for val in range(5):
  with cols_btn[val]:
    if st.button(str(val), key=f"btn_{val}", use_container_width=True):
      st.session_state.history.append(val)
      st.rerun()

with cols_btn[5]:
  if st.button("⬅ Xóa", key="btn_back", use_container_width=True):
    if st.session_state.history:
      st.session_state.history.pop()
      st.rerun()

if st.sidebar.button("🗑 Reset Lịch Sử"):
  st.session_state.history = []
  st.rerun()

history = st.session_state.history


# --- PHẦN 3: PHÂN TÍCH MARKOV + THUẬT TOÁN PHÁT HIỆN CẦU BỆT ---
st.markdown("---")
st.subheader("🤖 Phân Tích & Vào Tiền")

if len(history) >= 6:
  # 1. Thuật toán phát hiện cầu bệt (Streak Momentum)
  is_streak_detected = False
  streak_bonus_pred = None
  streak_count = 0

  if len(history) >= 3:
    last_val = history[-1]
    for v in reversed(history):
      if v == last_val:
        streak_count += 1
      else:
        break
    if streak_count >= 3:
      is_streak_detected = True
      streak_bonus_pred = last_val

  # Hiển thị cảnh báo nếu bắt gặp cầu bệt
  if is_streak_detected:
    st.warning(
        f"🔥 **PHÁT HIỆN CẦU BỆT:** Đang bệt số **{streak_bonus_pred}**"
        f" ({streak_count} tay liên tiếp) -> Ưu tiên bám đuôi!"
    )

  # 2. Thuật toán Markov Bậc 2 kết hợp trọng số ván gần nhất
  transitions = {}
  for i in range(len(history) - 2):
    curr_pair = (history[i], history[i + 1])
    nxt = history[i + 2]
    if curr_pair not in transitions:
      transitions[curr_pair] = []
    weight = 2 if i >= len(history) - 10 else 1
    for _ in range(weight):
      transitions[curr_pair].append(nxt)

  last_pair = (history[-2], history[-1])
  if last_pair in transitions and transitions[last_pair]:
    possible_nexts = transitions[last_pair]
  else:
    possible_nexts = history

  counts = Counter(possible_nexts)
  top_items = counts.most_common(2)

  main_pred = top_items[0][0] if len(top_items) > 0 else history[-1]
  sub_pred = top_items[1][0] if len(top_items) > 1 else (main_pred + 1) % 5

  # Nếu phát hiện cầu bệt rõ ràng, ưu tiên đưa cửa bệt lên làm cửa chính
  if is_streak_detected and streak_bonus_pred is not None:
    if streak_bonus_pred != main_pred:
      sub_pred = main_pred
      main_pred = streak_bonus_pred

  # Tính chuỗi xịt liên tiếp để quản lý vốn
  recent_checks = []
  for i in range(4, len(history)):
    sub_hist = history[:i]
    sub_pair = (sub_hist[-2], sub_hist[-1])
    sub_trans = {}
    for j in range(len(sub_hist) - 2):
      spair = (sub_hist[j], sub_hist[j + 1])
      snxt = sub_hist[j + 2]
      if spair not in sub_trans:
        sub_trans[spair] = []
      sub_trans[spair].append(snxt)

    if sub_pair in sub_trans and sub_trans[sub_pair]:
      sub_counts = Counter(sub_trans[sub_pair])
      sub_top = sub_counts.most_common(2)
      s_main = sub_top[0][0] if len(sub_top) > 0 else sub_hist[-1]
      s_sub = sub_top[1][0] if len(sub_top) > 1 else (s_main + 1) % 5
      recent_checks.append(history[i] == s_main or history[i] == s_sub)

  current_loss_streak = 0
  if recent_checks:
    for res in reversed(recent_checks):
      if not res:
        current_loss_streak += 1
      else:
        break

  fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
  multiplier = 1
  if "Martingale" in betting_strategy:
    multiplier = 2**current_loss_streak
  elif "Fibonacci" in betting_strategy:
    idx = min(current_loss_streak, len(fib) - 1)
    multiplier = fib[idx]
  else:
    multiplier = 1

  total_current_bet = base_bet * multiplier
  K1 = odds_map[main_pred]
  K2 = odds_map[sub_pred]

  raw_money_main = total_current_bet * (K2 / (K1 + K2))
  money_main = round(raw_money_main / 10000) * 10000
  if money_main < 10000:
    money_main = 10000

  money_sub = total_current_bet - money_main
  money_sub = round(money_sub / 10000) * 10000
  if money_sub < 10000:
    money_sub = 10000

  total_current_bet = money_main + money_sub

  # Hiển thị Dự đoán
  col_m1, col_m2 = st.columns(2)
  with col_m1:
    st.metric(
        label="🎯 Cửa Chính",
        value=f"⭐ {label_map[main_pred]}",
        delta=f"{money_main:,.0f} VNĐ",
    )
  with col_m2:
    st.metric(
        label="🔹 Cửa Phụ",
        value=f"🔹 {label_map[sub_pred]}",
        delta=f"{money_sub:,.0f} VNĐ",
    )

  st.info(
      f"💰 **Tổng Cược:** `{total_current_bet:,.0f} VNĐ` (x{multiplier}"
      f" | Xịt liên tiếp: {current_loss_streak})"
  )

  # --- TÍNH TOÁN LỊCH SỬ DÒNG TIỀN ĐỂ ĐẨY LÊN TRÊN ---
  simulation_data = []
  running_capital = total_capital
  sim_loss_streak = 0

  for i in range(4, len(history)):
    sub_hist = history[:i]
    sub_pair = (sub_hist[-2], sub_hist[-1])
    sub_trans = {}
    for j in range(len(sub_hist) - 2):
      spair = (sub_hist[j], sub_hist[j + 1])
      snxt = sub_hist[j + 2]
      if spair not in sub_trans:
        sub_trans[spair] = []
      sub_trans[spair].append(snxt)

    if sub_pair in sub_trans and sub_trans[sub_pair]:
      sub_counts = Counter(sub_trans[sub_pair])
      sub_top = sub_counts.most_common(2)

      s_main = sub_top[0][0] if len(sub_top) > 0 else sub_hist[-1]
      s_sub = sub_top[1][0] if len(sub_top) > 1 else (s_main + 1) % 5

      if "Martingale" in betting_strategy:
        sim_mult = 2**sim_loss_streak
      elif "Fibonacci" in betting_strategy:
        s_idx = min(sim_loss_streak, len(fib) - 1)
        sim_mult = fib[s_idx]
      else:
        sim_mult = 1

      g_bet = base_bet * sim_mult
      k_m = odds_map[s_main]
      k_s = odds_map[s_sub]

      m_m = round((g_bet * (k_s / (k_m + k_s))) / 10000) * 10000
      if m_m < 10000:
        m_m = 10000
      m_s = g_bet - m_m
      m_s = round(m_s / 10000) * 10000
      if m_s < 10000:
        m_s = 10000
      actual_bet = m_m + m_s

      actual_next = history[i]
      is_win = False
      win_amount = 0
      if actual_next == s_main:
        is_win = True
        win_amount = m_m * k_m
      elif actual_next == s_sub:
        is_win = True
        win_amount = m_s * k_s

      if is_win:
        profit = win_amount - actual_bet
        running_capital += profit
        sim_loss_streak = 0
        result_str = "🟢 Thắng"
      else:
        profit = -actual_bet
        running_capital -= actual_bet
        sim_loss_streak += 1
        result_str = "🔴 Thua"

      simulation_data.append({
          "Ván": i + 1,
          "Cược": f"{actual_bet:,.0f}",
          "KQ": str(actual_next),
          "TT": result_str,
          "Lãi/Lỗ": f"{profit:+,.0f}",
          "Ví": f"{running_capital:,.0f}",
      })

  # --- HIỂN THỊ SỐ DƯ VÍ & LỊCH SỬ DÒNG TIỀN Ở KHUNG TRÊN ---
  if simulation_data:
    st.markdown("---")
    col_w1, col_w2 = st.columns(2)
    with col_w1:
      st.metric(label="💵 Số Dư Ví", value=f"{running_capital:,.0f} VNĐ")
    with col_w2:
      if running_capital <= total_capital - stop_loss_amount:
        st.error("🚨 CHẠM CẮT LỖ!")
      elif running_capital >= total_capital + take_profit_amount:
        st.success("🎯 ĐẠT CHỐT LÃI!")
      else:
        st.info("⚖️ Trạng thái: An toàn")

    st.markdown("### 📊 Lịch Sử Dòng Tiền")
    df_sim = pd.DataFrame(simulation_data)
    df_sim = df_sim.iloc[::-1].reset_index(drop=True)
    st.dataframe(df_sim, use_container_width=True, hide_index=True)
else:
  st.warning("⚠️ Nhập tối thiểu 6 ván để kích hoạt dự đoán.")


# --- PHẦN 4: BẢNG CẦU CHI TIẾT (ĐỂ PHÍA DƯỚI) ---
def get_chan_le(val):
  return "C" if val in [0, 2, 4] else "L"


def get_tai_xiu(val):
  if val > 2:
    return "T"
  elif val < 2:
    return "X"
  else:
    return "2"


def create_compact_casino_grid(data_list, max_rows=5, max_cols=8):
  if not data_list:
    return pd.DataFrame()

  columns_list = []
  current_col = []

  for i, val in enumerate(data_list):
    if i == 0:
      current_col.append(val)
    else:
      if val == data_list[i - 1]:
        if len(current_col) < max_rows:
          current_col.append(val)
        else:
          columns_list.append(current_col)
          current_col = [val]
      else:
        columns_list.append(current_col)
        current_col = [val]
  if current_col:
    columns_list.append(current_col)

  num_cols_total = len(columns_list)
  matrix = [["" for _ in range(num_cols_total)] for _ in range(max_rows)]

  for col_idx, col_data in enumerate(columns_list):
    for row_idx, val in enumerate(col_data):
      matrix[row_idx][col_idx] = val

  df_full = pd.DataFrame(matrix)
  if num_cols_total > max_cols:
    df_clipped = df_full.iloc[:, -max_cols:]
  else:
    df_clipped = df_full

  df_clipped.columns = [f"C{i+1}" for i in range(df_clipped.shape[1])]
  return df_clipped


st.markdown("---")
st.markdown("### 📈 Lịch Sử Cầu Bàn Chơi")
col_b1, col_b2, col_b3 = st.columns(3)

with col_b1:
  st.markdown("**C/L**")
  cl_data = [get_chan_le(v) for v in history]
  df_cl = create_compact_casino_grid(cl_data)
  if not df_cl.empty:
    st.dataframe(df_cl, use_container_width=True, hide_index=True)
  else:
    st.info("Trống")

with col_b2:
  st.markdown("**T/X/2**")
  tx_data = [get_tai_xiu(v) for v in history]
  df_tx = create_compact_casino_grid(tx_data)
  if not df_tx.empty:
    st.dataframe(df_tx, use_container_width=True, hide_index=True)
  else:
    st.info("Trống")

with col_b3:
  st.markdown("**Số Đỏ**")
  chitiet_data = [str(v) for v in history]
  df_ct = create_compact_casino_grid(chitiet_data)
  if not df_ct.empty:
    st.dataframe(df_ct, use_container_width=True, hide_index=True)
  else:
    st.info("Trống")