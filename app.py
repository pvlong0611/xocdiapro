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

label_map = {0: "4 Trắng", 1: "1 Đỏ 3 Trắng", 2: "2 Đỏ 2 Trắng", 3: "3 Đỏ 1 Trắng", 4: "4 Đỏ"}

# Tỷ lệ ăn chuẩn nhà cái online thực tế
odds_map = {0: 15.0, 1: 3.8, 2: 2.6, 3: 3.8, 4: 15.0}

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


# --- HÀM THUẬT TOÁN DỰ ĐOÁN 2 CỬA (CHÍNH & PHỤ) ---
def get_prediction_for_slice(hist_slice):
  if len(hist_slice) < 6:
    return None, None, False, None, 0

  is_streak_detected = False
  streak_bonus_pred = None
  streak_count = 0

  if len(hist_slice) >= 3:
    last_val = hist_slice[-1]
    for v in reversed(hist_slice):
      if v == last_val:
        streak_count += 1
      else:
        break
    if streak_count >= 3:
      is_streak_detected = True
      streak_bonus_pred = last_val

  transitions = {}
  for i in range(len(hist_slice) - 2):
    curr_pair = (hist_slice[i], hist_slice[i + 1])
    nxt = hist_slice[i + 2]
    if curr_pair not in transitions:
      transitions[curr_pair] = []
    weight = 2 if i >= len(hist_slice) - 10 else 1
    for _ in range(weight):
      transitions[curr_pair].append(nxt)

  last_pair = (hist_slice[-2], hist_slice[-1])
  if last_pair in transitions and transitions[last_pair]:
    possible_nexts = transitions[last_pair]
  else:
    possible_nexts = hist_slice

  counts = Counter(possible_nexts)
  top_items = counts.most_common(2)

  main_pred = top_items[0][0] if len(top_items) > 0 else hist_slice[-1]
  sub_pred = top_items[1][0] if len(top_items) > 1 else (main_pred + 1) % 5

  if is_streak_detected and streak_bonus_pred is not None:
    if streak_bonus_pred != main_pred:
      sub_pred = main_pred
      main_pred = streak_bonus_pred

  return main_pred, sub_pred, is_streak_detected, streak_bonus_pred, streak_count


# --- HÀM TÍNH TOÁN PHÂN BỔ TIỀN 2 CỬA CÂN BẰNG ---
def calculate_money_split(total_bet, main_pred, sub_pred):
  k_m = odds_map[main_pred]
  k_s = odds_map[sub_pred]

  raw_money_main = total_bet * (k_s / (k_m + k_s))
  money_main = round(raw_money_main / 10000) * 10000
  if money_main < 10000:
    money_main = 10000

  money_sub = total_bet - money_main
  money_sub = round(money_sub / 10000) * 10000
  if money_sub < 10000:
    money_sub = 10000

  actual_total = money_main + money_sub
  return money_main, money_sub, actual_total


# --- PHẦN 3: PHÂN TÍCH & DỰ ĐOÁN (TỪ VÁN THỨ 7 TRỞ ĐI) ---
st.markdown("---")
st.subheader("🤖 Phân Tích & Vào Tiền 2 Cửa (Từ Ván 7)")

if len(history) >= 6:
  main_pred, sub_pred, is_streak_detected, streak_bonus_pred, streak_count = (
      get_prediction_for_slice(history)
  )

  if is_streak_detected:
    st.warning(
        f"🔥 **PHÁT HIỆN CẦU BỆT:** Đang bệt số **{label_map[streak_bonus_pred]}**"
        f" ({streak_count} tay liên tiếp) -> Ưu tiên bám đuôi!"
    )

  # --- TÍNH TOÁN CHUỖI XỊT VÀ DÒNG TIỀN MÔ PHỎNG ---
  current_loss_streak = 0
  fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]

  sim_loss_streak = 0
  simulation_data = []
  running_capital = total_capital

  for i in range(6, len(history)):
    sub_hist = history[:i]
    s_main, s_sub, _, _, _ = get_prediction_for_slice(sub_hist)

    if "Martingale" in betting_strategy:
      sim_mult = 2**sim_loss_streak
    elif "Fibonacci" in betting_strategy:
      s_idx = min(sim_loss_streak, len(fib) - 1)
      sim_mult = fib[s_idx]
    else:
      sim_mult = 1

    g_bet = base_bet * sim_mult
    m_m, m_s, actual_bet = calculate_money_split(g_bet, s_main, s_sub)

    actual_next = history[i]
    is_win = False
    win_amount = 0

    if actual_next == s_main:
      is_win = True
      win_amount = m_m * odds_map[s_main]
    elif actual_next == s_sub:
      is_win = True
      win_amount = m_s * odds_map[s_sub]

    if is_win:
      profit = win_amount - actual_bet
      running_capital += profit
      sim_loss_streak = 0  # THẮNG: Reset chuỗi xịt về 0 để quay về mức cược gốc
      result_str = "🟢 Thắng"
    else:
      profit = -actual_bet
      running_capital -= actual_bet
      sim_loss_streak += 1  # THUA: Tăng chuỗi xịt để ván sau tự động nhân tiền gấp thếp
      result_str = "🔴 Thua"

    simulation_data.append({
        "Ván": i + 1,
        "Chính": f"{label_map[s_main]} ({m_m:,.0f})",
        "Phụ": f"{label_map[s_sub]} ({m_s:,.0f})",
        "Hệ số": f"x{sim_mult}",
        "Tổng Cược": f"{actual_bet:,.0f}",
        "KQ": label_map[actual_next],
        "TT": result_str,
        "Lãi/Lỗ": f"{profit:+,.0f}",
        "Ví": f"{running_capital:,.0f}",
    })

  current_loss_streak = sim_loss_streak

  multiplier = 1
  if "Martingale" in betting_strategy:
    multiplier = 2**current_loss_streak
  elif "Fibonacci" in betting_strategy:
    idx = min(current_loss_streak, len(fib) - 1)
    multiplier = fib[idx]
  else:
    multiplier = 1

  total_current_bet_raw = base_bet * multiplier
  money_main, money_sub, total_current_bet = calculate_money_split(
      total_current_bet_raw, main_pred, sub_pred
  )

  # Hiển thị trực quan 2 cửa
  col_m1, col_m2 = st.columns(2)
  with col_m1:
    st.metric(
        label="🎯 Cửa Chính",
        value=f"⭐ {label_map[main_pred]}",
        delta=f"Cược: {money_main:,.0f} VNĐ (1:{odds_map[main_pred]})",
    )
  with col_m2:
    st.metric(
        label="🔹 Cửa Phụ",
        value=f"🔹 {label_map[sub_pred]}",
        delta=f"Cược: {money_sub:,.0f} VNĐ (1:{odds_map[sub_pred]})",
    )

  st.info(
      f"💰 **Tổng Cược Ván Kế Tiếp:** `{total_current_bet:,.0f} VNĐ` (Chiến"
      f" thuật: {betting_strategy} | Hệ số: **x{multiplier}** | Xịt liên"
      f" tiếp: {current_loss_streak} tay)"
  )

  # --- HIỂN THỊ SỐ DƯ VÍ & BẢNG LỊCH SỬ DÒNG TIỀN ---
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

    st.markdown(
        "### 📊 Lịch Sử Dòng Tiền (Đánh 2 Cửa - Cân Đối Lãi Vốn)"
    )
    df_sim = pd.DataFrame(simulation_data)
    df_sim = df_sim.iloc[::-1].reset_index(drop=True)
    st.dataframe(df_sim, use_container_width=True, hide_index=True)
else:
  st.warning(
      f"⚠️ Đã nhập {len(history)}/6 ván. Hãy nhập đủ tối thiểu 6 ván đầu để"
      " hệ thống bắt đầu dự đoán và vào tiền từ ván thứ 7!"
  )


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