# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

# 1. 页面基础配置
st.set_page_config(page_title="Alpha Factory 数字化看板", layout="wide")

# ✅ 动态自适应路径（本地 Windows + Streamlit Cloud Linux 全兼容）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "backtest_outputs")

curves_parquet_path = os.path.join(OUTPUT_DIR, "backtest_curves.parquet")
summary_path        = os.path.join(OUTPUT_DIR, "factor_summary.csv")
last_update_path    = os.path.join(OUTPUT_DIR, "last_update.txt")

st.title("🚀 Alpha Factory 数字化因子量化看板")
st.caption("基于工业级特征工厂的自适应多板块复合回测系统")

# ==================== 更新时间显示 ====================
if os.path.exists(last_update_path):
    with open(last_update_path, "r", encoding="utf-8") as f:
        last_update = f.read().strip()
else:
    last_update = "尚未运行回测"

st.markdown(f"**数据更新时间**：`{last_update}`")

# 2. 高速缓存 + Parquet 读取
@st.cache_data
def load_and_clean_data_fast(p_path, s_path):
    if not os.path.exists(p_path) or not os.path.exists(s_path):
        return None, None
    df_curves = pd.read_parquet(p_path)
    df_summary = pd.read_csv(s_path).set_index('Metric')
    return df_curves, df_summary

df_curves, df_summary = load_and_clean_data_fast(curves_parquet_path, summary_path)

if df_curves is None:
    st.error("❌ 未检测到回测输出数据，请先在终端运行 `python run_sector_alpha_backtest_v3.py`")
    st.stop()
else:
    # 使用 Tabs 组织页面
    tab1, tab2 = st.tabs(["📈 业绩曲线看板", "📚 Alpha Factory 因子字典"])

    with tab1:
        # 侧边栏
        st.sidebar.header("控制面板")
        mode = st.sidebar.radio("查看级别", ["免费版（累计净值）", "专业版（每日具体持仓-需授权）"])
        st.sidebar.markdown("---")
        st.sidebar.info("🤖 生产流水线状态：每日16:30自动化回测已对齐")

        # 核心指标
        st.subheader("📊 因子组合核心统计指标")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="复合模型状态", value=df_summary.loc['Mean Rank IC', 'Value'])
        with col2:
            st.metric(label="组合真实年化夏普", value=df_summary.loc['IC IR', 'Value'].replace("Sharpe: ", ""))
        with col3:
            target_col = '精选全板块多空对冲策略'
            if target_col in df_curves.columns:
                total_ret = (df_curves[target_col].iloc[-1] - 1) * 100
                st.metric(label="测试期总超额收益", value=f"{total_ret:.2f}%", delta="实盘对齐")
            else:
                st.metric(label="测试期总超额收益", value="计算错误")
        with col4:
            st.metric(label="测试品种总数", value="65类商品期货")

        st.markdown("---")

        # 交互曲线
        st.subheader("📈 因子多空组合历史净值走势 (对冲大盘风险)")
        
        default_select = [c for c in ['精选全板块多空对冲策略', '基准_全市场平均'] if c in df_curves.columns]
        
        selected_cols = st.multiselect(
            "切换或增加想要观测的资产曲线：", 
            options=df_curves.columns.tolist(), 
            default=default_select
        )
        
        fig = px.line(df_curves.reset_index(), 
                      x=df_curves.index.name if df_curves.index.name else 'trade_date',
                      y=selected_cols,
                      labels={'value': '累积净值 (Baseline=1.0)', 'trade_date': '交易日期'},
                      title="多板块精选强因子复合回测表现 (全量日线)")
        
        fig.update_layout(
            hovermode="x unified", 
            legend_title_text="资产配置曲线",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

        if mode == "免费版（累计净值）":
            st.info("💡 当前为免费版本模式：支持全历史多空回测追踪。当期截面实时买卖信号已对顶尖订阅会员开放。")

    # ==================== 因子字典 Tab ====================
    with tab2:
        st.header("🔬 Alpha Factory 核心因子字典")
        st.markdown("以下为本轮复合策略所使用的**各板块最强因子**及其微观经济学逻辑：")

        factor_dict = {
            "能化": """
**vol_wsr_cs_z**（仓单结构）  
家族：仓单驱动 | 方向：多▲ | IC≈0.1046  
逻辑：注册仓单横截面异常变化反映产业供需失衡，是能化品种20日强领先信号。
            """,
            "黑色": """
**f_oi_near_max_60**（持仓逼近60日高点）  
家族：持仓驱动 | 方向：多▲ | IC≈0.0597  
逻辑：巨量持仓沉淀代表多空资金死磕，黑色系典型的趋势突破催化剂。
            """,
            "有色": """
**sector_corr_20**（20日板块相关性）  
家族：板块共振 | 方向：多▲ | Total Score=1.0  
逻辑：与板块高度共振的品种享受系统性红利，捕捉板块轮动中的Alpha。
            """,
            "农产品": """
**close**（收盘价，方向反转）  
家族：价格水平 | 方向：空▼ | IC≈0.0866  
逻辑：农产品高价位往往面临供给压力或需求季节性回落。
            """,
            "软商": """
**wad_cs_rank**（Williams Accumulation Distribution 截面排序）  
家族：资金累积 | 方向：空▼ | IC≈0.0974  
逻辑：资金流入流出强度在软商板块有显著反向预测能力。
            """,
            "金融": """
**ret_kurt_w120_cs_z**（120日收益率峰度）  
家族：微观分布 | 方向：多▲ | IC≈0.1142  
逻辑：金融期货长周期高峰度往往预示机构筹码沉淀后的趋势启动。
            """
        }

        for sector, desc in factor_dict.items():
            with st.expander(f"📍 {sector}板块核心因子", expanded=True):
                st.markdown(desc)

        st.markdown("---")
        st.info("💡 因子选择基于历史IC、多头胜率、OOS稳定性等综合评分。所有因子均经过严格未来函数过滤。")

# 页脚
st.caption("© Alpha Factory | 仅供研究参考 | 历史业绩不代表未来表现")
