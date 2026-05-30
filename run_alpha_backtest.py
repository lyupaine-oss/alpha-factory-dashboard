# -*- coding: utf-8 -*-
"""
run_alpha_backtest.py (极速纯分析版)
============================================================
✅ 零重复计算：直接提取 Parquet 中已有的自相关因子特征
✅ 极速对齐：对已有特征进行横截面分层与 IC 计算
✅ 成果输出：为 Streamlit 看板直接生成轻量化成果
"""

import os
import pandas as pd
import numpy as np
from scipy.stats import spearmanr

# 1. 路径与配置定义
DATA_PATH = r"D:\MSTS\outputs\final_tables\train_set_enhanced.parquet"
OUTPUT_DIR = r"D:\MSTS\app\backtest_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 直接指定数据集里已经存在的因子名和标签名
FACTOR_NAME = 'auto_corr_l1_cs_z'  # 使用你已经做过截面标准化的因子
TARGET_LABEL = 'label_5d'         # 预测目标（5日收益）

print("⏳ 1. 正在直接载入已包含特征的 Parquet 数据集...")
df = pd.read_parquet(DATA_PATH, columns=['trade_date', 'symbol', FACTOR_NAME, TARGET_LABEL])

# 转换时间并排序
df['trade_date'] = pd.to_datetime(df['trade_date'])
df = df.sort_values(['trade_date', 'symbol']).reset_index(drop=True)

print(f"📊 载入成功！共 {df.shape[0]} 行交易数据。")

# 2. 时序 IC / Rank IC 计算
print("📈 2. 正在基于现有特征计算 Rank IC...")
def calc_daily_ic(sub_df):
    sub_df = sub_df.dropna(subset=[FACTOR_NAME, TARGET_LABEL])
    if len(sub_df) < 5: 
        return pd.Series({'ic': np.nan, 'rank_ic': np.nan})
    ic = np.corrcoef(sub_df[FACTOR_NAME], sub_df[TARGET_LABEL])[0, 1]
    rank_ic, _ = spearmanr(sub_df[FACTOR_NAME], sub_df[TARGET_LABEL])
    return pd.Series({'ic': ic, 'rank_ic': rank_ic})

daily_ic = df.groupby('trade_date').apply(calc_daily_ic).dropna()

mean_ic = daily_ic['ic'].mean()
mean_rank_ic = daily_ic['rank_ic'].mean()
ir = daily_ic['ic'].mean() / daily_ic['ic'].std() if daily_ic['ic'].std() != 0 else 0
rank_ir = daily_ic['rank_ic'].mean() / daily_ic['rank_ic'].std() if daily_ic['rank_ic'].std() != 0 else 0

print(f"   => Mean Rank IC: {mean_rank_ic:.4f} | Rank IC IR: {rank_ir:.4f}")

# 3. 截面 5 分层模拟 (Quintile Backtest)
print("🎯 3. 正在进行截面分层与多空组合资产回溯...")
# 按照已有的因子得分在每日截面上分 5 组
df['group'] = df.groupby('trade_date')[FACTOR_NAME].transform(
    lambda x: pd.qcut(x, 5, labels=False, duplicates='drop')
)

daily_group_ret = df.groupby(['trade_date', 'group'])[TARGET_LABEL].mean().unstack().fillna(0)
market_mean = daily_group_ret.mean(axis=1)

# 根据 Rank IC 正负号自动决定多空方向
if mean_rank_ic < 0:
    long_short_ret = daily_group_ret[0] - daily_group_ret[4]  # 负相关：买因子值最低的，卖最高的
else:
    long_short_ret = daily_group_ret[4] - daily_group_ret[0]  # 正相关：买因子值最高的，卖最低的

# 计算累计净值
cum_returns = (1 + daily_group_ret).cumprod()
cum_ls_wealth = (1 + long_short_ret).cumprod()
cum_market = (1 + market_mean).cumprod()

# 4. 导出成果
print("💾 4. 正在导出轻量化结果至 app 目录...")
summary_df = pd.DataFrame({
    'Metric': ['Mean IC', 'Mean Rank IC', 'IC IR', 'Rank IC IR'],
    'Value': [f"{mean_ic:.4f}", f"{mean_rank_ic:.4f}", f"{ir:.4f}", f"{rank_ir:.4f}"]
})
summary_df.to_csv(os.path.join(OUTPUT_DIR, "factor_summary.csv"), index=False)

viz_df = pd.DataFrame({
    'Market_Benchmark': cum_market,
    'Long_Short_Strategy': cum_ls_wealth,
    'Top_Quintile(G4)': cum_returns[4],
    'Bottom_Quintile(G0)': cum_returns[0]
}, index=daily_group_ret.index)
viz_df.to_csv(os.path.join(OUTPUT_DIR, "backtest_curves.csv"))

print("✨ [SUCCESS] 极速回测完成！已生成轻量化图表数据。")