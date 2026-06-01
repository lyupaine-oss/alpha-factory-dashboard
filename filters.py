# -*- coding: utf-8 -*-
# filters.py
import streamlit as st


def render_risk_slider():
    """
    在侧边栏渲染工业级风控滑块。
    risk_level 已由回测脚本将 Z-Score MinMax 映射至 0-100，
    此处直接以 0-100 区间控制信号过滤阈值。
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🛡️ 自动化风控阈值")

    max_risk_allowed = st.sidebar.slider(
        label="最大允许风险水位 (0-100)",
        min_value=0.0,
        max_value=100.0,
        value=100.0,
        step=5.0,
        help="向左拖动滑块将过滤掉全市场中相对波动率极高、处于风险风口浪尖的极端标的。"
    )

    if max_risk_allowed < 100.0:
        st.sidebar.warning(
            f"⚠️ 防御拦截已激活：隐藏风险评分 > {max_risk_allowed:.0f} 的信号"
        )
    else:
        st.sidebar.success("✅ 全风险资产库满额暴露中")

    return max_risk_allowed
