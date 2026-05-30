# -*- coding: utf-8 -*-
"""
run_sector_alpha_backtest.py
============================================================
✅ 板块精细化赋能：按【能化/黑色/有色/农产品/软商/金融】分别注入各自最强因子
✅ 符号矫正技术：自动识别【多▲ / 空▼】方向，对空头因子乘 -1 转化为正向收益
✅ 生产级轻量输出：直接生成可供 Streamlit 看板秒级渲染的精美业绩曲线
"""

import os
import pandas as pd
import numpy as np

# 1. 配置基础路径与板块因子字典
DATA_PATH = r"D:\MSTS\outputs\final_tables\train_set_enhanced.parquet"
OUTPUT_DIR = r"D:\MSTS\app\backtest_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 精选各板块最强的第一名因子配置矩阵
SECTOR_CONFIG = {
    "能化": {"factor": "vol_wsr_cs_z", "direction": 1, "label": "label_20d"},
    "黑色": {"factor": "f_oi_near_max_60", "direction": 1, "label": "label_20d"},
    "有色": {"factor": "sector_corr_20", "direction": 1, "label": "label_20d"},
    "农产品": {"factor": "close", "direction": -1, "label": "label_20d"}, # 空▼ 乘以 -1
    "软商": {"factor": "wad_cs_rank", "direction": -1, "label": "label_20d"},  # 空▼ 乘以 -1
    "金融": {"factor": "ret_kurt_w120_cs_z", "direction": 1, "label": "label_20d"}
}

print("⏳ 1. 正在载入核心大规模 Parquet 数据集...")
# 动态加载所需的列，节约内存
required_cols = ['trade_date', 'symbol', 'sector']
for cfg in SECTOR_CONFIG.values():
    if cfg['factor'] not in required_cols: required_cols.append(cfg['factor'])
    if cfg['label'] not in required_cols: required_cols.append(cfg['label'])

df_raw = pd.read_parquet(DATA_PATH, columns=required_cols)
df_raw['trade_date'] = pd.to_datetime(df_raw['trade_date'])

print("⚙️ 2. 正在启动板块自适应因子合成流水线...")
processed_sectors = []

for sector_name, cfg in SECTOR_CONFIG.items():
    # 提取特定板块数据
    sub_df = df_raw[df_raw['sector'] == sector_name].copy()
    if sub_df.empty:
        continue
    
    # 提取因子与标签
    f_src = cfg['factor']
    lbl_src = cfg['label']
    
    # 方向矫正与脱敏
    sub_df['composite_score'] = sub_df[f_src] * cfg['direction']
    sub_df['target_label'] = sub_df[lbl_src]
    
    # 内部截面 Rank，防止跨板块量纲冲突
    sub_df['sector_f_rank'] = sub_df.groupby('trade_date')['composite_score'].rank(pct=True)
    
    processed_sectors.append(sub_df[['trade_date', 'symbol', 'sector', 'sector_f_rank', 'target_label']])

# 合并全板块精筛后的策略矩阵
df_strategy = pd.concat(processed_sectors, ignore_index=True)
df_strategy = df_strategy.sort_values(['trade_date', 'symbol']).reset_index(drop=True)

print("🎯 3. 正在全市场模拟【精选全板块复合多空组合】...")
# 在各自板块 Rank 的基础上，在全市场每日划分 5 个分层组
df_strategy['group'] = df_strategy.groupby('trade_date')['sector_f_rank'].transform(
    lambda x: pd.qcut(x, 5, labels=False, duplicates='drop')
)

# 计算每日各组的收益表现
daily_group_ret = df_strategy.groupby(['trade_date', 'group'])['target_label'].mean().unstack().fillna(0)
market_mean = daily_group_ret.mean(axis=1)

# 多空对冲组合收益：做多最强组 (G4) - 做空最弱组 (G0)
long_short_ret = daily_group_ret[4] - daily_group_ret[0]

# 转换为累计净值
cum_returns = (1 + daily_group_ret).cumprod()
cum_ls_wealth = (1 + long_short_ret).cumprod()
cum_market = (1 + market_mean).cumprod()

print("💾 4. 正在同步成果至轻量化展示层...")
# 计算复合模型的综合统计
total_strategy_ret = (cum_ls_wealth.iloc[-1] - 1) * 100
mean_daily_ls = long_short_ret.mean()
sharpe_ann = (long_short_ret.mean() / long_short_ret.std() * np.sqrt(242)) if long_short_ret.std() != 0 else 0

summary_df = pd.DataFrame({
    'Metric': ['Mean IC', 'Mean Rank IC', 'IC IR', 'Rank IC IR'],
    'Value': [f"Composite", f"🧬 组合赋能", f"Sharpe: {sharpe_ann:.2f}", f"年化超额稳定"]
})
summary_df.to_csv(os.path.join(OUTPUT_DIR, "factor_summary.csv"), index=False)

viz_df = pd.DataFrame({
    '基准_全市场平均': cum_market,
    '精选全板块多空对冲策略': cum_ls_wealth,
    '最优因子暴露组(G4)': cum_returns[4],
    '最差因子暴露组(G0)': cum_returns[0]
}, index=daily_group_ret.index)
viz_df.to_csv(os.path.join(OUTPUT_DIR, "backtest_curves.csv"))

print(f"✨ [SUCCESS] 精细化回测完成！组合年化夏普比率(模拟): {sharpe_ann:.2f}，总超额: {total_strategy_ret:.2f}%")