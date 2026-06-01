# -*- coding: utf-8 -*-
"""
factor_miner.py
============================================================
✅ 工业级特征库管理：全量解析 1768 个交互因子绩效表
✅ 多维淘金矩阵：支持绝对预测强度排序、正负 Alpha 自动分流
✅ 多环境自适应：智能识别 Streamlit Cloud 云端环境与本地 D 盘环境
✅ 双工架构：既可作为模块由 app.py 路由调用，亦可独立本地调试运行
✅ 🔐 安全增强：前端因子脱敏（支持 free / pro 权限隔离）
"""
import streamlit as st
import pandas as pd
import os
import hashlib

# ============================================================
# 🔐 因子脱敏模块（带盐值，防止反向破解）
# ============================================================
HASH_SALT = "lv_prof_alpha_secure_v1"

def anonymize_factor(name):
    raw = f"{name}{HASH_SALT}"
    return "Alpha_" + hashlib.md5(raw.encode('utf-8')).hexdigest()[:8]

def render_factor_mining_page():
    """
    渲染因子大淘金核心功能页
    """
    st.markdown("## 🧬 Alpha 因子大淘金 & 特征库监控")
    st.markdown("当前因子资产库总容量：`1768` 个智能交互特征")
    
    # ============================================================
    # 🌐 多环境路径解析
    # ============================================================
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    cloud_data_path = os.path.join(BASE_DIR, "data", "all_interaction_icir.csv")
    local_absolute_path = r"D:\MSTS\outputs\final_tables\all_interaction_icir.csv"
    
    if os.path.exists(cloud_data_path):
        csv_path = cloud_data_path
    elif os.path.exists(local_absolute_path):
        csv_path = local_absolute_path
    else:
        st.error("❌ 未找到因子绩效文件！")
        st.info(f"请检查路径:\n1. {cloud_data_path}\n2. {local_absolute_path}")
        return
        
    try:
        # ============================================================
        # 📊 载入数据
        # ============================================================
        df_factors = pd.read_csv(csv_path)
        df_factors['Abs_ICIR'] = df_factors['ICIR'].abs()
        
        # ============================================================
        # 👤 用户权限控制（核心：是否脱敏）
        # ============================================================
        user_plan = st.session_state.get("user_plan", "free")
        
        if user_plan == "free":
            df_factors['因子特征名'] = df_factors['factor'].apply(anonymize_factor)
        else:
            df_factors['因子特征名'] = df_factors['factor']
        
        # ============================================================
        # 🔍 侧边栏过滤器
        # ============================================================
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔍 因子挖掘过滤器")
        
        search_query = st.sidebar.text_input(
            "搜索因子关键词 (如: hurst, vol, skew)", ""
        ).strip()
        
        min_icir = st.sidebar.slider(
            "最低 ICIR 绝对值阈值",
            min_value=0.0,
            max_value=1.0,
            value=0.02,
            step=0.01
        )
        
        # ============================================================
        # 🧹 过滤逻辑
        # ============================================================
        df_filtered = df_factors[df_factors['Abs_ICIR'] >= min_icir]
        
        if search_query:
            df_filtered = df_filtered[
                df_filtered['factor'].str.contains(search_query, case=False, na=False)
            ]
        
        # ============================================================
        # 🔀 多空分流
        # ============================================================
        long_factors = df_filtered[df_filtered['ICIR'] > 0] \
            .sort_values(by='ICIR', ascending=False).reset_index(drop=True)
        
        short_factors = df_filtered[df_filtered['ICIR'] < 0] \
            .sort_values(by='ICIR', ascending=True).reset_index(drop=True)
        
        # ============================================================
        # 📊 指标看板
        # ============================================================
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        
        metric_col1.metric("当前激活特征总数", len(df_filtered))
        
        metric_col2.metric(
            "最强正向 Alpha",
            f"{long_factors['ICIR'].max():.4f}" if not long_factors.empty else "N/A"
        )
        
        metric_col3.metric(
            "最强反向 Alpha",
            f"{short_factors['ICIR'].min():.4f}" if not short_factors.empty else "N/A"
        )
        
        st.markdown("---")
        
        # ============================================================
        # 🖥️ 双栏展示（关键：使用脱敏列）
        # ============================================================
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🟢 顶级正向特征 (多头)")
            st.dataframe(
                long_factors.rename(columns={'ICIR': '稳定度 (ICIR)'})[
                    ['因子特征名', '稳定度 (ICIR)']
                ],
                use_container_width=True,
                height=450
            )
            
        with col2:
            st.markdown("#### 🔴 顶级反向特征 (空头)")
            st.dataframe(
                short_factors.rename(columns={'ICIR': '稳定度 (ICIR)'})[
                    ['因子特征名', '稳定度 (ICIR)']
                ],
                use_container_width=True,
                height=450
            )
            
    except Exception as e:
        st.error(f"⚠️ 因子解析异常: {str(e)}")

# ============================================================
# ⚙️ 本地调试入口
# ============================================================
if __name__ == "__main__":
    st.set_page_config(page_title="Alpha 因子淘金机", layout="wide")
    render_factor_mining_page()