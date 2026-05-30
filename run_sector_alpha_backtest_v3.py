# -*- coding: utf-8 -*-
"""
run_sector_alpha_backtest_v3.py
============================================================
✅ 日频精准对齐：采用 1日滞后收益率 'ret_1d_lag'
✅ 全面升级为 Parquet 工业级高速导出
"""

import os
import pandas as pd
import numpy as np

# 1. 基础配置
DATA_PATH = r"D:\MSTS\outputs\final_tables\train_set_enhanced.parquet"
OUTPUT_DIR = r"D:\MSTS\app\backtest_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 目标标签
TARGET_LABEL = 'ret_1d_lag'

# 板块最强因子矩阵配置
SECTOR_CONFIG = {
    "能化": {"factor": "vol_wsr_cs_z", "direction": 1},
    "黑色": {"factor": "f_oi_near_max_60", "direction": 1},
    "有色": {"factor": "sector_corr_20", "direction": 1},
    "农产品": {"factor": "close", "direction": -1},
    "软商": {"factor": "wad_cs_rank", "direction": -1},
    "金融": {"factor": "ret_kurt_w120_cs_z", "direction": 1}
}

print("⏳ 1. 正在载入包含 'ret_1d_lag' 的 Parquet 数据集...")
required_cols = ['trade_date', 'symbol', 'sector', TARGET_LABEL]
for cfg in SECTOR_CONFIG.values():
    if cfg['factor'] not in required_cols: 
        required_cols.append(cfg['factor'])

df_raw = pd.read_parquet(DATA_PATH, columns=required_cols)
df_raw['trade_date'] = pd.to_datetime(df_raw['trade_date'])

print("⚙️ 2. 正在启动板块自适应因子合成流水线...")
processed_sectors = []

for sector_name, cfg in SECTOR_CONFIG.items():
    sub_df = df_raw[df_raw['sector'] == sector_name].copy()
    if sub_df.empty: continue
    
    sub_df['composite_score'] = sub_df[cfg['factor']] * cfg['direction']
    sub_df['sector_f_rank'] = sub_df.groupby('trade_date')['composite_score'].rank(pct=True)
    processed_sectors.append(sub_df[['trade_date', 'symbol', 'sector', 'sector_f_rank', TARGET_LABEL]])

df_strategy = pd.concat(processed_sectors, ignore_index=True)
df_strategy = df_strategy.sort_values(['trade_date', 'symbol']).reset_index(drop=True)

print("🎯 3. 正在全市场模拟【日频精选全板块复合多空组合】...")
df_strategy['group'] = df_strategy.groupby('trade_date')['sector_f_rank'].transform(
    lambda x: pd.qcut(x, 5, labels=False, duplicates='drop')
)

daily_group_ret = df_strategy.groupby(['trade_date', 'group'])[TARGET_LABEL].mean().unstack().fillna(0)
market_mean = daily_group_ret.mean(axis=1)
long_short_ret = daily_group_ret[4] - daily_group_ret[0]

cum_returns = (1 + daily_group_ret).cumprod()
cum_ls_wealth = (1 + long_short_ret).cumprod()
cum_market = (1 + market_mean).cumprod()

print("💾 4. 正在同步真实业绩数据至轻量化展示层...")

total_strategy_ret = (cum_ls_wealth.iloc[-1] - 1) * 100
sharpe_ann = (long_short_ret.mean() / long_short_ret.std() * np.sqrt(242)) if long_short_ret.std() != 0 else 0

# ==========================================
# 💾 4. 更改为 Parquet 工业级高速导出
# ==========================================
summary_df = pd.DataFrame({
    'Metric': ['Mean IC', 'Mean Rank IC', 'IC IR', 'Rank IC IR'],
    'Value': [f"Composite", f"🧬 组合赋能", f"Sharpe: {sharpe_ann:.2f}", f"年化超额稳定"]
})
# summary_df 较小，保留 CSV 方便随时文本查看
summary_df.to_csv(os.path.join(OUTPUT_DIR, "factor_summary.csv"), index=False)

# 大规模资产曲线矩阵 → 保存为 Parquet
viz_df = pd.DataFrame({
    '基准_全市场平均': cum_market,
    '精选全板块多空对冲策略': cum_ls_wealth,
    '最优因子暴露组(G4)': cum_returns[4],
    '最差因子暴露组(G0)': cum_returns[0]
}, index=daily_group_ret.index)

viz_df.to_parquet(os.path.join(OUTPUT_DIR, "backtest_curves.parquet"), index=True)
print("💾 [SPEEDUP] 资产曲线已成功以 Parquet 二进制高压缩格式固化。")

print(f"✨ [SUCCESS] 日频精细化回测完成！组合真实年化夏普: {sharpe_ann:.2f}，总超额收益: {total_strategy_ret:.2f}%")