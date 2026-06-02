# -*- coding: utf-8 -*-
"""
pnl_tracker.py
============================================================
AlphaOS 持仓盈亏滚动复盘流水线（逻辑修正版）
============================================================
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

# ============================================================
# 0. 路径配置（兼容本地 + Streamlit Cloud）
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 优先使用相对路径，兼容 Streamlit Cloud
DATA_PATH = os.path.join(BASE_DIR, "..", "outputs", "final_tables", "train_set_enhanced.parquet")

# 如果相对路径不存在，回退到本地开发路径
if not os.path.exists(DATA_PATH):
    DATA_PATH = r"D:\MSTS\outputs\final_tables\train_set_enhanced.parquet"

OUTPUT_DIR = os.path.join(BASE_DIR, "backtest_outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

PNL_CURRENT_PATH = os.path.join(OUTPUT_DIR, "pnl_current.csv")
PNL_HISTORY_PATH = os.path.join(OUTPUT_DIR, "pnl_history.csv")
PNL_REPORT_PATH = os.path.join(OUTPUT_DIR, "pnl_report.txt")

# ============================================================
# 1. 持仓配置区（每次换仓只改这里）
# ============================================================
SYSTEM_START_DATE = "2026-05-22"

CURRENT_POSITIONS = {
    "EC": {"name": "集运欧线", "direction": 1, "entry_date": "2026-05-22"},
    "LC": {"name": "碳酸锂", "direction": 1, "entry_date": "2026-05-22"},
    "SI": {"name": "工业硅", "direction": 1, "entry_date": "2026-05-22"},
}

HOLDING_DAYS = 5

# ============================================================
# 2. 数据加载
# ============================================================
print("⏳ 正在读取数据集...")
df = pd.read_parquet(DATA_PATH, columns=["trade_date", "symbol", "close"])
df["trade_date"] = pd.to_datetime(df["trade_date"])

all_dates = sorted(df["trade_date"].unique())
latest_date = all_dates[-1]
today_str = datetime.now().strftime("%Y-%m-%d")
print(f"✅ 数据最新日期：{latest_date.date()}")

# ============================================================
# 3. 计算系统运行第 N 天
# ============================================================
start_dt = pd.Timestamp(SYSTEM_START_DATE)
day_count = (pd.Timestamp(today_str) - start_dt).days + 1


# ============================================================
# 4. 工具函数
# ============================================================
def get_close(symbol: str, date: pd.Timestamp) -> float:
    sub = df[(df["symbol"] == symbol) & (df["trade_date"] <= date)]
    if sub.empty:
        return np.nan
    return float(sub.sort_values("trade_date").iloc[-1]["close"])


def calc_holding_days(entry_date_str: str, end_date: pd.Timestamp) -> int:
    entry = pd.Timestamp(entry_date_str)
    return sum(1 for d in all_dates if entry < d <= end_date)


def get_exit_date(entry_date_str: str, holding: int) -> pd.Timestamp:
    entry = pd.Timestamp(entry_date_str)
    # 找到建仓日之后所有的有效交易日
    future_dates = [d for d in all_dates if d > entry]
    if len(future_dates) >= holding:
        return future_dates[holding - 1]
    return future_dates[-1] if future_dates else entry


# ============================================================
# 5. 逐笔计算
# ============================================================
records = []
for symbol, cfg in CURRENT_POSITIONS.items():
    try:
        entry_date = pd.Timestamp(cfg["entry_date"])
        direction = cfg["direction"]
        name = cfg["name"]

        price_entry = get_close(symbol, entry_date)
        price_now = get_close(symbol, latest_date)

        if np.isnan(price_entry) or np.isnan(price_now):
            print(f"⚠️ [{symbol}] 价格数据缺失，跳过")
            continue

        raw_ret = (price_now - price_entry) / price_entry
        ret = raw_ret * direction

        # 精准计算时间逻辑
        days_held = calc_holding_days(cfg["entry_date"], latest_date)
        exit_date = get_exit_date(cfg["entry_date"], HOLDING_DAYS)

        # 处理超期逻辑，防止出现负数或剩余0天却在持仓的尴尬
        if latest_date > exit_date:
            days_remain = 0
            over_days = sum(1 for d in all_dates if exit_date < d <= latest_date)
            status_text = f"⏱ 本轮5日换仓期满（已超期 {over_days} 个交易日），等待信号迭代"
        elif latest_date == exit_date:
            days_remain = 0
            status_text = f"⏱ 今日达到目标平仓日（已持有 {days_held} 个交易日），16:30 将自动执行换仓"
        else:
            days_remain = sum(1 for d in all_dates if latest_date < d <= exit_date)
            status_text = f"⏱ 已持有 {days_held} 个交易日，剩余 {days_remain} 个交易日"

        records.append({
            "symbol": symbol,
            "name": name,
            "direction": "多▲" if direction == 1 else "空▼",
            "entry_date": cfg["entry_date"],
            "entry_price": round(price_entry, 2),
            "latest_price": round(price_now, 2),
            "ret_pct": round(ret * 100, 2),
            "days_held": days_held,
            "days_remaining": days_remain,
            "status_text": status_text,
            "exit_date": str(exit_date.date()),
            "pnl_emoji": "✅" if ret > 0 else ("❌" if ret < 0 else "➖"),
            "as_of_date": str(latest_date.date()),
        })
    except Exception as e:
        print(f"⚠️ 处理 {symbol} 时发生错误: {e}")

df_current = pd.DataFrame(records)

# ============================================================
# 6. 保存当前持仓
# ============================================================
if not df_current.empty:
    df_current.to_csv(PNL_CURRENT_PATH, index=False, encoding="utf-8-sig")
    print(f"💾 pnl_current.csv 已保存 → {len(df_current)} 条持仓")
else:
    print("⚠️ 当前没有有效持仓记录")

# ============================================================
# 7. 平仓日归档
# ============================================================
is_exit_day = any(latest_date >= get_exit_date(r["entry_date"], HOLDING_DAYS) for r in records) if records else False
if is_exit_day and not df_current.empty:
    print("📦 检测到达到或超出平仓目标日，正在检查是否归档...")
    df_to_save = df_current.copy()
    df_to_save["close_date"] = str(latest_date.date())
    df_to_save["round_ret_pct"] = df_to_save["ret_pct"]

    if os.path.exists(PNL_HISTORY_PATH):
        df_hist = pd.read_csv(PNL_HISTORY_PATH)
        # 简单防重复归档逻辑：如果当前日期的当前品种已归档，则不再叠加
        mask = (df_hist["close_date"] == str(latest_date.date())) & (df_hist["symbol"].isin(df_to_save["symbol"]))
        if not mask.any():
            df_hist = pd.concat([df_hist, df_to_save], ignore_index=True)
            df_hist.to_csv(PNL_HISTORY_PATH, index=False, encoding="utf-8-sig")
            print(f"📚 pnl_history.csv 已更新归档")
        else:
            print("i 今日信号数据已存在于历史归档中，跳过追加。")
    else:
        df_hist = df_to_save.copy()
        df_hist.to_csv(PNL_HISTORY_PATH, index=False, encoding="utf-8-sig")
        print(f"📚 pnl_history.csv 已建立并完成首次归档")

# ============================================================
# 8. 生成播报文案（增加空保护与美化）
# ============================================================
total_ret = df_current["ret_pct"].mean() if not df_current.empty else 0.0
win_count = int((df_current["ret_pct"] > 0).sum()) if not df_current.empty else 0
total_count = len(df_current)

total_emoji = "✅" if total_ret > 0 else ("❌" if total_ret < 0 else "➖")

# 历史统计
hist_win_rate_str = "积累中…"
hist_total_ret_str = "—"
if os.path.exists(PNL_HISTORY_PATH):
    try:
        df_hist_check = pd.read_csv(PNL_HISTORY_PATH)
        if len(df_hist_check) > 0:
            hist_win_rate = (df_hist_check["ret_pct"] > 0).mean() * 100
            hist_total_ret = df_hist_check["ret_pct"].sum()
            hist_win_rate_str = f"{hist_win_rate:.0f}%（共 {len(df_hist_check)} 笔）"
            hist_total_ret_str = f"{hist_total_ret:+.2f}%"
    except:
        pass

# ============================================================
# 9. 拼装知乎播报文本
# ============================================================
lines = []
lines.append(f"AlphaOS 第 {day_count} 天公开记录 | {today_str}")
lines.append("—" * 32)
lines.append("")

if records:
    lines.append(f"📅 建仓日期：{records[0]['entry_date']}")
    lines.append(f"📅 数据截至：{latest_date.date()}")
    lines.append(f"📅 预计平仓：{records[0]['exit_date']}")
    lines.append(f"{records[0]['status_text']}")  # 动态状态提示
else:
    lines.append("暂无持仓记录")

lines.append("")
lines.append("今日持仓浮动盈亏：")
lines.append("")

for r in records:
    change_str = f"+{r['ret_pct']:.2f}%" if r['ret_pct'] > 0 else f"{r['ret_pct']:.2f}%"
    lines.append(
        f"{r['pnl_emoji']} {r['symbol']} {r['name']}（{r['direction']}） "
        f"建仓 {r['entry_price']} → 现价 {r['latest_price']}  {change_str}"
    )

lines.append("")
lines.append(
    f"{total_emoji} 组合等权均收：{total_ret:+.2f}% "
    f"本轮胜率 {win_count}/{total_count}"
)

if hist_total_ret_str != "—":
    lines.append(f"📊 历史累计收益：{hist_total_ret_str} | 胜率：{hist_win_rate_str}")

lines.append("")
lines.append("———")
lines.append("系统采用 5 日换仓机制，每日 16:30 自动更新。")
lines.append("信号由多因子复合模型生成，非人工主观判断。")
lines.append("出问题就说出问题，这也是公开记录的一部分。")
lines.append("")
lines.append("© Alpha Factory | 仅供研究参考 | 历史业绩不代表未来表现")

report_text = "\n".join(lines)

with open(PNL_REPORT_PATH, "w", encoding="utf-8") as f:
    f.write(report_text)

print("\n" + "=" * 60)
print(report_text)
print("=" * 60)
print(f"\n📝 播报文案已保存 → {PNL_REPORT_PATH}")

# ============================================================
# 10. 终端摘要
# ============================================================
print(f"\n{'─' * 50}")
print(f"✨ [DONE] 第 {day_count} 天复盘完成")
print(f"   数据截至：{latest_date.date()}")
print(f"   组合等权收益：{total_ret:+.2f}%")
print(f"   本轮盈利笔数：{win_count}/{total_count}")
print(f"{'─' * 50}")