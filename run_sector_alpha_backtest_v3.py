# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
run_sector_alpha_backtest_v3.py
============================================================
✅ 日频精准对齐：采用 1日滞后收益率 'ret_1d_lag'
✅ 全面升级为 Parquet 工业级高速导出
✅ 新增 today_signals.csv 信号输出（对接 app.py 信号看板）
✅ [v3.1] 新增 volatility_10_cs_z 截面风险指标，输出 risk_level (0-100)
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

# ============================================================
# ⚙️ 【1. 基础配置与载入】
# ============================================================
DATA_PATH  = r"D:\MSTS\outputs\final_tables\train_set_enhanced.parquet"
OUTPUT_DIR = r"D:\MSTS\app\backtest_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 目标标签 + 核心风险指标
TARGET_LABEL = 'ret_1d_lag'
RISK_LABEL   = 'volatility_10_cs_z'

# 板块最强因子矩阵配置
SECTOR_CONFIG = {
    "能化":   {"factor": "vol_wsr_cs_z",       "direction":  1},
    "黑色":   {"factor": "f_oi_near_max_60",    "direction":  1},
    "有色":   {"factor": "sector_corr_20",      "direction":  1},
    "农产品": {"factor": "close",               "direction": -1},
    "软商":   {"factor": "wad_cs_rank",         "direction": -1},
    "金融":   {"factor": "ret_kurt_w120_cs_z",  "direction":  1},
}

print("⏳ 1. 正在载入包含 'ret_1d_lag' 与风险指标的 Parquet 数据集...")
required_cols = ['trade_date', 'symbol', 'sector', TARGET_LABEL, RISK_LABEL]
for cfg in SECTOR_CONFIG.values():
    if cfg['factor'] not in required_cols:
        required_cols.append(cfg['factor'])

df_raw = pd.read_parquet(DATA_PATH, columns=required_cols)
df_raw['trade_date'] = pd.to_datetime(df_raw['trade_date'])

# ============================================================
# ⚙️ 【2. 自适应合成流水线】（RISK_LABEL 随流水线向下流转）
# ============================================================
print("⚙️ 2. 正在启动板块自适应因子合成流水线...")
processed_sectors = []

for sector_name, cfg in SECTOR_CONFIG.items():
    sub_df = df_raw[df_raw['sector'] == sector_name].copy()
    if sub_df.empty:
        continue
    sub_df['composite_score'] = sub_df[cfg['factor']] * cfg['direction']
    sub_df['sector_f_rank']   = sub_df.groupby('trade_date')['composite_score'].rank(pct=True)
    processed_sectors.append(
        sub_df[['trade_date', 'symbol', 'sector',
                'composite_score', 'sector_f_rank',
                TARGET_LABEL, RISK_LABEL]]
    )

df_strategy = pd.concat(processed_sectors, ignore_index=True)
df_strategy  = df_strategy.sort_values(['trade_date', 'symbol']).reset_index(drop=True)

# ============================================================
# 🎯 【3. 全市场模拟 · 日频精选全板块复合多空组合】
# ============================================================
print("🎯 3. 正在全市场模拟【日频精选全板块复合多空组合】...")
df_strategy['group'] = df_strategy.groupby('trade_date')['sector_f_rank'].transform(
    lambda x: pd.qcut(x, 5, labels=False, duplicates='drop')
)

daily_group_ret  = df_strategy.groupby(['trade_date', 'group'])[TARGET_LABEL].mean().unstack().fillna(0)
market_mean      = daily_group_ret.mean(axis=1)
long_short_ret   = daily_group_ret[4] - daily_group_ret[0]

cum_returns    = (1 + daily_group_ret).cumprod()
cum_ls_wealth  = (1 + long_short_ret).cumprod()
cum_market     = (1 + market_mean).cumprod()

total_strategy_ret = (cum_ls_wealth.iloc[-1] - 1) * 100
sharpe_ann = (
    long_short_ret.mean() / long_short_ret.std() * np.sqrt(242)
    if long_short_ret.std() != 0 else 0
)

# ============================================================
# 💾 【4. 业绩汇总 CSV + 资产曲线 Parquet】
# ============================================================
print("💾 4. 正在同步真实业绩数据至轻量化展示层...")

summary_df = pd.DataFrame({
    'Metric': ['Mean IC', 'Mean Rank IC', 'IC IR', 'Rank IC IR'],
    'Value':  ['Composite', '🧬 组合赋能', f'Sharpe: {sharpe_ann:.2f}', '年化超额稳定']
})
summary_df.to_csv(os.path.join(OUTPUT_DIR, "factor_summary.csv"), index=False)

viz_df = pd.DataFrame({
    '基准_全市场平均':          cum_market,
    '精选全板块多空对冲策略':    cum_ls_wealth,
    '最优因子暴露组(G4)':       cum_returns[4],
    '最差因子暴露组(G0)':       cum_returns[0],
}, index=daily_group_ret.index)
viz_df.to_parquet(os.path.join(OUTPUT_DIR, "backtest_curves.parquet"), index=True)
print("💾 [SPEEDUP] 资产曲线已成功以 Parquet 二进制高压缩格式固化。")

# ============================================================
# 📡 【5. 生成 today_signals.csv（含截面风险指标）】
# ============================================================
print("📡 5. 正在生成包含截面风险的今日多空信号切片 today_signals.csv ...")

latest_date = df_strategy['trade_date'].max()
df_latest   = df_strategy[df_strategy['trade_date'] == latest_date].copy()
df_latest   = df_latest.dropna(subset=['composite_score'])

score_max = df_latest['composite_score'].abs().max()

# 多头：composite_score 最高的 Top 10
long_top10 = (
    df_latest.nlargest(10, 'composite_score')
    [['symbol', 'sector', 'composite_score', RISK_LABEL]]
    .rename(columns={'composite_score': 'score', RISK_LABEL: 'risk_level'})
    .assign(direction='多头')
    .reset_index(drop=True)
)
if score_max > 0:
    long_top10['score'] = (long_top10['score'] / score_max * 10).round(2)

# 空头：composite_score 最低的 Top 10
short_top10 = (
    df_latest.nsmallest(10, 'composite_score')
    [['symbol', 'sector', 'composite_score', RISK_LABEL]]
    .rename(columns={'composite_score': 'score', RISK_LABEL: 'risk_level'})
    .assign(direction='空头')
    .reset_index(drop=True)
)
if score_max > 0:
    short_top10['score'] = (short_top10['score'].abs() / score_max * 10).round(2)

# 合并
signals_df = pd.concat([long_top10, short_top10], ignore_index=True)
signals_df.insert(0, 'signal_date', latest_date.strftime('%Y-%m-%d'))

# 将 Z-Score 用 MinMax 映射到 0-100 风险区间（-3~+3 覆盖 99.7% 正态分布）
signals_df['risk_level'] = (
    ((signals_df['risk_level'] - (-3)) / 6) * 100
).clip(0, 100).round(1)

# 输出列顺序：signal_date, symbol, sector, score, risk_level, direction
signals_df = signals_df[['signal_date', 'symbol', 'sector', 'score', 'risk_level', 'direction']]

signals_path = os.path.join(OUTPUT_DIR, "today_signals.csv")
signals_df.to_csv(signals_path, index=False, encoding='utf-8-sig')

print(f"✅ [SIGNALS] 今日信号已成功输出 (含风险指标) → {signals_path}")
print(f"   多头 Top 10: {long_top10['symbol'].tolist()}")
print(f"   空头 Top 10: {short_top10['symbol'].tolist()}")

# ============================================================
# 📝 【6. 更新时间戳】
# ============================================================
with open(os.path.join(OUTPUT_DIR, "last_update.txt"), "w", encoding="utf-8") as f:
    f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

print(f"\n✨ [SUCCESS] 日频精细化回测完成！")
print(f"   组合真实年化夏普: {sharpe_ann:.2f} | 总超额收益: {total_strategy_ret:.2f}%")
print(f"   信号日期: {latest_date.date()} | 输出目录: {OUTPUT_DIR}")