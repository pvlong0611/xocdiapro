from collections import Counter
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Xóc Đĩa Pro - App Làm Tròn 10k", layout="wide")

# Khởi tạo session state lưu lịch sử
if "history" not in st.session_state:
  st.session_state.history = []

st.title("🎲 Tool Xóc Đĩa - Làm Tròn Tiền Cược Bội Số 10.000 VNĐ")


# --- PHẦN 1: CÀI ĐẶT THÔNG SỐ VỐN & CHIẾN THUẬT ---
st.sidebar.header("⚙️ Cài Đặt Vốn & Cược")
total_capital = st.sidebar.number_input(
    "Tổng Vốn Khởi Điểm (VNĐ):",
    min_value=100000,
    value=5000000,
    step=100000,
)
base_bet = st.sidebar.number_input(
    "Mức Cược Gốc Ban Đầu (VNĐ):", min_value=10000, value=100000, step=10000
)

betting_strategy = st.sidebar.selectbox(
    "Chiến thuật vào tiền khi thua:",
    [
        "Đều tay (Flat Betting)",
        "Gấp thếp cổ điển (Martingale: x2 khi thua)",
        "Dãy Fibonacci (1, 1, 2, 3, 5, 8... khi thua)",
    ],
)

stop_loss_pct = st.sidebar.slider(
    "Cắt Lỗ (% Vốn):", min_value=5, max_value=50, value=25
)
take_profit_pct = st.sidebar.slider(
    "Chốt Lãi (% Vốn):", min_value=5, max_value=100, value=40
)

stop_loss_amount = total_capital * (stop_loss_pct / 100)
take_profit_amount = total_capital * (take_profit_pct / 100)

st.sidebar.markdown("---")
st.sidebar.markdown(f"🛑 **Cắt Lỗ:** -{stop_loss_amount:,.0f} VNĐ")
st.sidebar.markdown(f"🎯 **Chốt Lãi:** +{take_profit_amount:,.0f} VNĐ")


# --- PHẦN 2: BÀN PHÍM NHẬP LIỆU NHANH ---
st.markdown("### ⌨️ Nhập Kết Quả Nhanh")
cols_btn = st.columns(6)

label_map = {
    0: "0 Đỏ (4 Trắng)",
    1: "1 Đỏ (3 Trắng)",
    2: "2 Đỏ (2 Trắng)",
    3: "3 Đỏ (1 Trắng)",
    4: "4 Đỏ (0 Trắng)",
}
odds_map = {0: 16.0, 1: 4.8, 2: 3.6, 3: 4.8, 4: 16.0}

for val in range(5):
  with cols_btn[val]:
    if st.button(
        label_map[val], key=f"btn_{val}", use_container_width=True
    ):
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


# Các hàm quy đổi trạng thái
def get_chan_le(val):
  return "C" if val in [0, 2, 4] else "L"


def get_tai_xiu(val):
  if val > 2:
    return "T"
  elif val < 2:
    return "X"
  else:
    return "2"


history = st.session_state.history


# --- PHẦN 3: XÂY DỰNG BẢNG CẦU THU GỌN ---
def create_compact_casino_grid(data_list, max_rows=5, max_cols=12):
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
col_b1, col_b2, col_b3 = st.columns(3)

with col_b1:
  st.markdown("**📊 Chẵn / Lẻ**")
  cl_data = [get_chan_le(v) for v in history]
  df_cl = create_compact_casino_grid(cl_data)
  if not df_cl.empty:
    st.dataframe(df_cl, use_container_width=True, hide_index=True)
  else:
    st.info("Trống")

with col_b2:
  st.markdown("**📊 Tài / Xỉu / Số 2**")
  tx_data = [get_tai_xiu(v) for v in history]
  df_tx = create_compact_casino_grid(tx_data)
  if not df_tx.empty:
    st.dataframe(df_tx, use_container_width=True, hide_index=True)
  else:
    st.info("Trống")

with col_b3:
  st.markdown("**📊 Chi Tiết 0-4 Đỏ**")
  chitiet_data = [label_map[v] for v in history]
  df_ct = create_compact_casino_grid(chitiet_data)
  if not df_ct.empty:
    st.dataframe(df_ct, use_container_width=True, hide_index=True)
  else:
    st.info("Trống")


# --- PHẦN 4: DỰ ĐOÁN & LÀM TRÒN TIỀN CƯỢC BỘI SỐ 10.000 VNĐ ---
st.markdown("---")
st.subheader("🤖 Dự Đoán Ván Tới & Phân Bổ Tiền Bội Số 10k")

if len(history) >= 4:
  transitions = {}
  for i in range(len(history) - 1):
    curr = history[i]
    nxt = history[i + 1]
    if curr not in transitions:
      transitions[curr] = []
    transitions[curr].append(nxt)

  last_val = history[-1]
  possible_nexts = transitions.get(last_val, history)
  counts = Counter(possible_nexts)

  top_items = counts.most_common(2)
  main_pred = top_items[0][0] if len(top_items) > 0 else history[-1]
  sub_pred = top_items[1][0] if len(top_items) > 1 else (main_pred + 1) % 5

  recent_checks = []
  for i in range(3, len(history)):
    sub_hist = history[:i]
    sub_last = sub_hist[-1]
    sub_trans = {}
    for j in range(len(sub_hist) - 1):
      scurr = sub_hist[j]
      snxt = sub_hist[j + 1]
      if scurr not in sub_trans:
        sub_trans[scurr] = []
      sub_trans[scurr].append(snxt)
    if sub_last in sub_trans and sub_trans[sub_last]:
      sub_counts = Counter(sub_trans[sub_last])
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
  
  # LÀM TRÒN SỐ TIỀN THÀNH BỘI SỐ CỦA 10.000 VNĐ
  raw_money_main = total_current_bet * (K2 / (K1 + K2))
  money_main = round(raw_money_main / 10000) * 10000
  if money_main < 10000: 
    money_main = 10000
    
  money_sub = total_current_bet - money_main
  money_sub = round(money_sub / 10000) * 10000
  if money_sub < 10000:
    money_sub = 10000
    
  total_current_bet = money_main + money_sub

  col_m1, col_m2, col_m3 = st.columns(3)
  with col_m1:
    st.metric(label="🎯 Dự Đoán", value=f"⭐ {label_map[main_pred]}", delta=f"🔹 {label_map[sub_pred]}")
  with col_m2:
    st.metric(label="⚡ Chuỗi Xịt", value=f"{current_loss_streak} tay", delta=f"Hệ số: x{multiplier}")
  with col_m3:
    st.metric(label="💰 Tổng Cược (Tròn 10k)", value=f"{total_current_bet:,.0f} VNĐ")

  st.markdown("---")
  st.markdown("### 📋 Tiền Cược Từng Cửa (Bội Số 10.000 VNĐ)")
  col_t1, col_t2 = st.columns(2)
  with col_t1:
    st.markdown(f"* ⭐ **Cửa Chính (`{label_map[main_pred]}`):** **`{money_main:,.0f} VNĐ`**")
  with col_t2:
    st.markdown(f"* 🔹 **Cửa Phụ (`{label_map[sub_pred]}`):** **`{money_sub:,.0f} VNĐ`**")

  # --- PHẦN 5: SAO KÊ DÒNG TIỀN ---
  st.markdown("---")
  st.subheader("📊 Bảng Sao Kê Dòng Tiền Lịch Sử")

  simulation_data = []
  running_capital = total_capital
  sim_loss_streak = 0

  for i in range(3, len(history)):
    sub_hist = history[:i]
    sub_last = sub_hist[-1]
    sub_trans = {}
    for j in range(len(sub_hist) - 1):
      scurr = sub_hist[j]
      snxt = sub_hist[j + 1]
      if scurr not in sub_trans:
        sub_trans[scurr] = []
      sub_trans[scurr].append(snxt)

    if sub_last in sub_trans and sub_trans[sub_last]:
      sub_counts = Counter(sub_trans[sub_last])
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
      
      # Làm tròn mô phỏng lịch sử chuẩn bội số 10k
      m_m = round((g_bet * (k_s / (k_m + k_s))) / 10000) * 10000
      if m_m < 10000: m_m = 10000
      m_s = g_bet - m_m
      m_s = round(m_s / 10000) * 10000
      if m_s < 10000: m_s = 10000
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
          "Kết quả": label_map[actual_next],
          "Trạng thái": result_str,
          "Lãi/Lỗ": f"{profit:+,.0f}",
          "Số dư ví": f"{running_capital:,.0f}",
      })

  if simulation_data:
    df_sim = pd.DataFrame(simulation_data)
    st.dataframe(df_sim, use_container_width=True, hide_index=True)

    net_profit = running_capital - total_capital
    col_s1, col_s2 = st.columns(2)
    with col_s1:
      st.metric(label="💵 Số Dư Ví", value=f"{running_capital:,.0f} VNĐ", delta=f"{net_profit:+,.0f} VNĐ")
    with col_s2:
      if running_capital <= total_capital - stop_loss_amount:
        st.error("🚨 CHẠM CẮT LỖ! Dừng ngay.")
      elif running_capital >= total_capital + take_profit_amount:
        st.success("🎯 ĐẠT CHỐT LÃI! Nghỉ ngơi.")
      else:
        st.info("⚖️ Ví an toàn.")
else:
  st.warning("⚠️ Nhập từ 4 ván trở lên để tool phân tích.")
