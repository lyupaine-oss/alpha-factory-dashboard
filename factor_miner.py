# -*- coding: utf-8 -*-
"""
factor_miner.py
============================================================
✅ 工业级特征库管理：全量解析 1768 个交互因子绩效表
✅ 多维淘金矩阵：支持绝对预测强度排序、正负 Alpha 自动分流
✅ 双工架构：既可作为模块由 app.py 路由调用，亦可独立本地调试运行
"""

import streamlit as st
import pandas as pd
import os

def render_factor_mining_page():
    """
    渲染因子大淘金核心功能页
    """
    st.markdown("## 🧬 Alpha 因子大淘金 & 特征库监控")
    st.markdown("当前因子资产库总容量：`1768` 个智能交互特征")
    
    csv_path = r"D:\MSTS\outputs\final_tables\all_interaction_icir.csv"
    
    if not os.path.exists(csv_path):
        st.error(f"❌ 未找到因子绩效文件，请检查路径是否正确：{csv_path}")
        return
        
    try:
        # 1. 载入全量因子
        df_factors = pd.read_csv(csv_path)
        
        # 计算绝对预测强度用于全局风控和排序
        df_factors['Abs_ICIR'] = df_factors['ICIR'].abs()
        
        # 2. 侧边栏联动风控组件挂载
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔍 因子挖掘过滤器")
        
        # 搜索框：支持不区分大小写的关键词模糊检索
        search_query = st.sidebar.text_input("搜索特定因子关键词 (如: hurst, vol, skew)", "").strip()
        
        # 滑块：动态截断低预测强度的噪音特征
        min_icir = st.sidebar.slider(
            label="最低有效 ICIR 绝对值阈值", 
            min_value=0.0, 
            max_value=1.0, 
            value=0.02, 
            step=0.01,
            help="滑块向右拖动会过滤掉预测能力不稳定的僵尸因子。"
        )
        
        # 3. 核心清洗与过滤逻辑
        df_filtered = df_factors[df_factors['Abs_ICIR'] >= min_icir]
        
        if search_query:
            df_filtered = df_filtered[df_filtered['factor'].str.contains(search_query, case=False, na=False)]
            
        # 4. 动态分流多空阵营
        long_factors = df_filtered[df_filtered['ICIR'] > 0].sort_values(by='ICIR', ascending=False).reset_index(drop=True)
        short_factors = df_filtered[df_filtered['ICIR'] < 0].sort_values(by='ICIR', ascending=True).reset_index(drop=True)
        
        # 5. 轻量化展示层看板渲染
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        metric_col1.metric("当前激活特征总数", len(df_filtered))
        metric_col2.metric("最强正向 Alpha 因子 (ICIR)", f"{long_factors['ICIR'].max():.4f}" if not long_factors.empty else "N/A")
        metric_col3.metric("最强反向 Alpha 因子 (ICIR)", f"{short_factors['ICIR'].min():.4f}" if not short_factors.empty else "N/A")
        
        st.markdown("---")
        
        # 双栏并排输出
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🟢 顶级正向特征 (多头暴露权重)")
            st.caption("适合作为多头组合的因子强化或加权仓位依据")
            st.dataframe(
                long_factors.rename(columns={'factor': '因子特征名', 'ICIR': '稳定度 (ICIR)'})[['因子特征名', '稳定度 (ICIR)']], 
                use_container_width=True,
                height=450
            )
            
        with col2:
            st.markdown("#### 🔴 顶级反向特征 (空头对冲依据)")
            st.caption("适合做反转或回归策略，负得越多代表做空越稳定")
            st.dataframe(
                short_factors.rename(columns={'factor': '因子特征名', 'ICIR': '稳定度 (ICIR)'})[['因子特征名', '稳定度 (ICIR)']], 
                use_container_width=True,
                height=450
            )
            
    except Exception as e:
        st.error(f"⚠️ 因子特征库解析异常: {str(e)}")

# ============================================================
# ⚙️ 本地独立运行调试入口
# ============================================================
if __name__ == "__main__":
    # 如果单独运行本脚本，自动启动本地调试大屏
    st.set_page_config(page_title="Alpha 因子淘金机", layout="wide")
    render_factor_mining_page()