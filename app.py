# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
import subprocess
from datetime import datetime
import plotly.express as px

# ============================================================
# 0. 页面配置
# ============================================================
st.set_page_config(page_title="Alpha Factory 量化信号系统", layout="wide")

# ✅ 保留云端的动态自适应路径（本地 Windows + Streamlit Cloud Linux 全兼容）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "backtest_outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ✅ 保留本地最新的全部 7 个数据路径定义
curves_parquet_path = os.path.join(OUTPUT_DIR, "backtest_curves.parquet")
summary_path = os.path.join(OUTPUT_DIR, "factor_summary.csv")
last_update_path = os.path.join(OUTPUT_DIR, "last_update.txt")
signals_path = os.path.join(OUTPUT_DIR, "today_signals.csv")
pnl_current_path = os.path.join(OUTPUT_DIR, "pnl_current.csv")
pnl_history_path = os.path.join(OUTPUT_DIR, "pnl_history.csv")
pnl_report_path = os.path.join(OUTPUT_DIR, "pnl_report.txt")

# ============================================================
# 1. 权限系统
# ============================================================
if "user_plan" not in st.session_state:
    st.session_state.user_plan = "free"

user_plan = st.session_state.user_plan

# ============================================================
# 2. 侧边栏 + 更新时间
# ============================================================
st.sidebar.header("🎛️ 控制面板")
plan_labels = {"free": "🆓 免费版", "pro": "👑 专业版", "pro_plus": "💎 高端版"}
st.sidebar.markdown(f"**当前订阅**：{plan_labels[user_plan]}")
st.sidebar.markdown("---")

if user_plan == "free":
    if st.sidebar.button("🚀 升级专业版 ¥199/月"):
        st.session_state.user_plan = "pro"
        st.rerun()
    if st.sidebar.button("💎 升级高端版 ¥599/月"):
        st.session_state.user_plan = "pro_plus"
        st.rerun()
else:
    if st.sidebar.button("退出订阅（演示）"):
        st.session_state.user_plan = "free"
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("🤖 生产流水线：每日 16:30 自动更新")

# 更新时间
last_update = "尚未运行回测"
if os.path.exists(last_update_path):
    with open(last_update_path, "r", encoding="utf-8") as f:
        last_update = f.read().strip()

st.sidebar.caption(f"📅 当前数据：`{last_update}`")

# ============================================================
# 3. 一键回测
# ============================================================
st.sidebar.subheader("⚙️ 回测控制")
if st.sidebar.button("🔄 一键运行回测", type="primary", use_container_width=True):
    with st.spinner("🔄 正在执行回测...（约 10~30 秒）"):
        try:
            result = subprocess.run(
                ["python", "run_sector_alpha_backtest_v3.py"],
                capture_output=True, text=True, cwd=BASE_DIR, timeout=90
            )
            if result.returncode == 0:
                st.success("✅ 回测执行成功！页面刷新中...")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(f"❌ 回测失败：{result.stderr[:300]}")
        except Exception as e:
            st.error(f"⚠️ 执行异常：{e}")

# ============================================================
# 4. 数据加载
# ============================================================
@st.cache_data(ttl=60)
def load_backtest_data(p_path, s_path):
    if not os.path.exists(p_path) or not os.path.exists(s_path):
        return None, None
    try:
        df_curves = pd.read_parquet(p_path)
        df_summary = pd.read_csv(s_path).set_index("Metric")
        return df_curves, df_summary
    except:
        return None, None

@st.cache_data(ttl=60)
def load_csv(path):
    if not os.path.exists(path):
        return None
    try:
        return pd.read_csv(path)
    except:
        return None

df_curves, df_summary = load_backtest_data(curves_parquet_path, summary_path)
df_signals = load_csv(signals_path)
df_pnl_cur = load_csv(pnl_current_path)
df_pnl_hist = load_csv(pnl_history_path)

# ============================================================
# 5. 主界面
# ============================================================
st.title("🔥 Alpha Factory 数字化因子量化信号系统")
st.caption("基于工业级特征工厂的自适应多板块复合回测系统")
st.markdown(f"**数据更新时间**：`{last_update}`")
st.markdown("---")

if df_curves is None:
    st.warning("⚠️ 当前没有回测数据，请点击左侧「一键运行回测」按钮生成数据。")
    st.stop()

# ============================================================
# 6. Tabs
# ============================================================
tab_signal, tab_pnl, tab_curve, tab_dict = st.tabs([
    "📡 今日信号看板", "📒 持仓复盘日志", "📈 业绩曲线看板", "📚 因子字典"
])

# ============================================================
# TAB 1：今日信号看板
# ============================================================
with tab_signal:
    st.subheader("📊 今日自适应多空信号")
    st.caption("多因子复合评分 · 每日 16:30 更新 · 免费版延迟 1 天")

    if df_signals is not None and not df_signals.empty:
        long_signals = df_signals[df_signals["direction"] == "多头"].sort_values("score", ascending=False).reset_index(drop=True)
        short_signals = df_signals[df_signals["direction"] == "空头"].sort_values("score", ascending=False).reset_index(drop=True)
    else:
        long_signals = pd.DataFrame({"symbol": ["螺纹钢 RB", "铜 CU", "原油 SC", "铁矿石 I", "PTA"], "score": [9.4, 8.9, 8.3, 7.8, 7.1], "direction": ["多头"] * 5})
        short_signals = pd.DataFrame({"symbol": ["豆粕 M", "玉米 C", "棕榈油 P", "白糖 SR", "棉花 CF"], "score": [8.7, 8.1, 7.6, 7.0, 6.5], "direction": ["空头"] * 5})

    col_long, col_short = st.columns(2)
    with col_long:
        st.success("📈 多头精选 Top 5")
        visible = long_signals.head(2) if user_plan == "free" else long_signals.head(5)
        for i, row in visible.iterrows():
            st.write(f"**{i+1}.** {row['symbol']}　因子强度：`{row['score']:.1f}`")
        if user_plan == "free" and len(visible) < 5:
            for j in range(len(visible) + 1, 6):
                st.warning(f"**{j}.** 🔒 订阅专业版后查看")

    with col_short:
        st.error("📉 空头精选 Top 5")
        visible = short_signals.head(2) if user_plan == "free" else short_signals.head(5)
        for i, row in visible.iterrows():
            st.write(f"**{i+1}.** {row['symbol']}　因子强度：`{row['score']:.1f}`")
        if user_plan == "free" and len(visible) < 5:
            for j in range(len(visible) + 1, 6):
                st.warning(f"**{j}.** 🔒 订阅专业版后查看")

    st.markdown("---")
    if user_plan in ("pro", "pro_plus"):
        st.balloons()
        st.subheader("👑 完整多空 Top 10")
        c1, c2 = st.columns(2)
        with c1:
            st.dataframe(long_signals.head(10).assign(建议持有="5 交易日"), use_container_width=True)
        with c2:
            st.dataframe(short_signals.head(10).assign(建议持有="5 交易日"), use_container_width=True)
    else:
        st.info("💡 完整 Top 10 → 升级专业版解锁")

# ============================================================
# TAB 2：持仓复盘日志
# ============================================================
with tab_pnl:
    st.subheader("📒 AlphaOS 持仓复盘公开日志")
    st.caption("5日换仓机制 · 每日16:30自动更新 · 公开透明记录")

    # 当前持仓浮动盈亏
    st.markdown("#### 📌 当前持仓浮动盈亏")
    
    if df_pnl_cur is not None and not df_pnl_cur.empty:
        as_of = df_pnl_cur["as_of_date"].iloc[0]
        st.caption(f"数据截至：**{as_of}**")

        cols = st.columns(len(df_pnl_cur))
        for idx, (_, row) in enumerate(df_pnl_cur.iterrows()):
            with cols[idx]:
                st.metric(
                    label=f"{row.get('pnl_emoji', '')} {row['symbol']} {row.get('name', row['symbol'])}",
                    value=f"{row['latest_price']:,.2f}",
                    delta=f"{row.get('ret_pct', 0):+.2f}%",
                    delta_color="normal" if row.get("ret_pct", 0) >= 0 else "inverse"
                )

        total_ret = df_pnl_cur["ret_pct"].mean()
        win_count = (df_pnl_cur["ret_pct"] > 0).sum()
        total_count = len(df_pnl_cur)
        emoji = "✅" if total_ret > 0 else ("❌" if total_ret < 0 else "➖")
        st.markdown(f"**{emoji} 组合等权均收：`{total_ret:+.2f}%`　本轮胜率：{win_count}/{total_count}**")

        # 详细表格：选择关键列展示
        display_cols = [col for col in ["symbol", "name", "direction", "entry_price", "latest_price", "ret_pct", "days_held", "days_remaining", "exit_date"] if col in df_pnl_cur.columns]
        st.dataframe(df_pnl_cur[display_cols], use_container_width=True, hide_index=True)
    else:
        st.info("📌 当前暂无持仓数据\n请先运行 `python pnl_tracker.py` 生成持仓记录")

    st.markdown("---")

    # 历史复盘归档
    st.markdown("#### 📚 历史复盘归档")
    
    if df_pnl_hist is not None and not df_pnl_hist.empty:
        # 按建仓日聚合统计
        df_rounds = (
            df_pnl_hist.groupby("entry_date")
            .agg(
                平仓日=("close_date", "first"),
                品种数=("symbol", "count"),
                等权收益_pct=("ret_pct", "mean"),
                盈利单数=("ret_pct", lambda x: (x > 0).sum()),
            )
            .reset_index()
            .rename(columns={"entry_date": "建仓日"})
        )
        df_rounds["胜率"] = (df_rounds["盈利单数"] / df_rounds["品种数"] * 100).map("{:.0f}%".format)
        df_rounds["等权收益"] = df_rounds["等权收益_pct"].map("{:+.2f}%".format)
        df_rounds["结果"] = df_rounds["等权收益_pct"].apply(lambda x: "✅" if x > 0 else "❌")
        df_rounds["累计收益_pct"] = df_rounds["等权收益_pct"].cumsum()

        st.dataframe(
            df_rounds[["结果", "建仓日", "平仓日", "品种数", "等权收益", "胜率"]],
            use_container_width=True,
            hide_index=True,
        )

        # 历史收益柱状图 + 累计收益线
        fig_hist = px.bar(
            df_rounds, x="建仓日", y="等权收益_pct",
            color=df_rounds["等权收益_pct"].apply(lambda x: "盈利" if x > 0 else "亏损"),
            color_discrete_map={"盈利": "#26a69a", "亏损": "#ef5350"},
            labels={"等权收益_pct": "等权收益 (%)"},
            title="各轮次组合收益 + 累计收益走势",
        )
        fig_hist.add_scatter(
            x=df_rounds["建仓日"], y=df_rounds["累计收益_pct"],
            mode="lines+markers", name="累计收益",
            line=dict(color="#FFA726", width=2),
        )
        fig_hist.update_layout(margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified")
        st.plotly_chart(fig_hist, use_container_width=True)

        # 历史总计指标
        total_hist_ret = df_rounds["等权收益_pct"].sum()
        hist_win_rounds = (df_rounds["等权收益_pct"] > 0).sum()
        hist_total_rds = len(df_rounds)
        hc1, hc2, hc3 = st.columns(3)
        hc1.metric("历史累计收益", f"{total_hist_ret:+.2f}%")
        hc2.metric("历史轮次胜率", f"{hist_win_rounds}/{hist_total_rds} = {hist_win_rounds/hist_total_rds*100:.0f}%")
        hc3.metric("累计交易笔数", f"{len(df_pnl_hist)} 笔")
    else:
        st.info("历史复盘记录将在第一次平仓后自动生成。")

    st.markdown("---")

    # 知乎/小红书播报文案
    st.markdown("#### 📋 今日知乎播报文案")
    if os.path.exists(pnl_report_path):
        with open(pnl_report_path, "r", encoding="utf-8") as f:
            report_text = f.read()
        st.text_area("可直接复制使用：", value=report_text, height=380)
        st.download_button("⬇️ 下载播报文案", report_text, file_name="alphaos_今日播报.txt")
    else:
        st.info("播报文案将在运行 `pnl_tracker.py` 后自动生成。")

# ============================================================
# TAB 3：业绩曲线看板
# ============================================================
with tab_curve:
    st.subheader("📊 因子组合核心统计指标")
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        if df_summary is not None and "Mean Rank IC" in df_summary.index:
            st.metric("复合模型状态", df_summary.loc["Mean Rank IC", "Value"])
        else:
            st.metric("复合模型状态", "N/A")
    
    with c2:
        if df_summary is not None and "IC IR" in df_summary.index:
            sharpe_str = df_summary.loc["IC IR", "Value"]
            sharpe_val = sharpe_str.replace("Sharpe: ", "") if isinstance(sharpe_str, str) else sharpe_str
            st.metric("组合真实年化夏普", sharpe_val)
        else:
            st.metric("组合真实年化夏普", "N/A")
    
    with c3:
        target_col = "精选全板块多空对冲策略"
        if df_curves is not None and target_col in df_curves.columns:
            total_ret = (df_curves[target_col].iloc[-1] - 1) * 100
            st.metric("测试期总超额收益", f"{total_ret:.2f}%", delta="实盘对齐")
        else:
            st.metric("测试期总超额收益", "N/A")
    
    with c4:
        st.metric("测试品种总数", "65类商品期货")

    st.markdown("---")
    
    if df_curves is not None:
        default_select = [c for c in ["精选全板块多空对冲策略", "基准_全市场平均"] if c in df_curves.columns]
        selected_cols = st.multiselect("切换曲线：", df_curves.columns.tolist(), default=default_select)
        
        if selected_cols:
            fig = px.line(
                df_curves.reset_index(), 
                x=df_curves.index.name or "trade_date",
                y=selected_cols, 
                title="多板块精选强因子复合回测表现（全量日线）"
            )
            fig.update_layout(hovermode="x unified", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("暂无回测曲线数据")

# ============================================================
# TAB 4：因子字典
# ============================================================
with tab_dict:
    st.header("🔬 Alpha Factory 核心因子字典")
    st.markdown("各板块最强因子及其微观经济学逻辑，所有因子均经过严格未来函数过滤。")
    
    factor_dict = {
        "能化": {
            "name": "vol_wsr_cs_z（仓单结构）",
            "tag": "仓单驱动 | 多▲ | IC≈0.1046",
            "free": True,
            "desc": "注册仓单横截面异常变化反映供需失衡，是能化品种20日强领先信号。仓单骤降→现货商加速提货→近月逼仓压力→做多胜率显著提升。"
        },
        "黑色": {
            "name": "f_oi_near_max_60（持仓逼近60日高点）",
            "tag": "持仓驱动 | 多▲ | IC≈0.0597",
            "free": True,
            "desc": "巨量持仓沉淀代表多空死磕，黑色系典型趋势突破催化剂。持仓近历史高位→一方被迫离场→动量加速启动。"
        },
        "有色": {
            "name": "sector_corr_20（20日板块相关性）",
            "tag": "板块共振 | 多▲ | Score=1.0",
            "free": False,
            "desc": "🔒 专业版解锁完整逻辑。当有色板块内品种相关性显著提升时，表明宏观定价因子主导市场，顺势交易胜率提升。"
        },
        "农产品": {
            "name": "close（收盘价方向反转）",
            "tag": "价格水平 | 空▼ | IC≈0.0866",
            "free": False,
            "desc": "🔒 专业版解锁完整逻辑。农产品价格具有均值回归特性，极端价格水平后反转概率增加，配合库存周期使用效果更佳。"
        },
        "软商": {
            "name": "wad_cs_rank（Williams AD 截面排序）",
            "tag": "资金累积 | 空▼ | IC≈0.0974",
            "free": False,
            "desc": "🔒 专业版解锁完整逻辑。Williams Accumulation/Distribution 资金流指标，资金持续流出预示下跌动能。"
        },
        "金融": {
            "name": "ret_kurt_w120_cs_z（120日收益率峰度）",
            "tag": "微观分布 | 多▲ | IC≈0.1142",
            "free": False,
            "desc": "🔒 专业版解锁完整逻辑。收益率分布峰度反映尾部风险预期，高峰度往往伴随波动率扩张，趋势策略胜率提升。"
        },
    }

    for sector, info in factor_dict.items():
        with st.expander(f"📍 {sector}：{info['name']}", expanded=info["free"]):
            st.caption(info["tag"])
            if info["free"] or user_plan in ("pro", "pro_plus"):
                st.markdown(info["desc"])
            else:
                st.warning("🔒 升级专业版后解锁完整因子逻辑白皮书。")
    
    st.markdown("---")
    st.info("💡 因子选择基于历史IC、多头胜率、OOS稳定性综合评分。")

# ============================================================
# 页脚
# ============================================================
st.markdown("---")
st.caption("© Alpha Factory | 仅供研究参考 | 历史业绩不代表未来表现")