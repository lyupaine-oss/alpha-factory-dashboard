# -*- coding: utf-8 -*-
"""
data_center.py (亦可直接追加入 factor_miner.py 底部)
============================================================
✅ 工业级数据资产分发中心：完美支持本地环境与 Streamlit Cloud 云端环境
✅ 🔐 商业权限严格隔离：
    - Free 层：仅保留最基础行情与持仓（过滤掉宏观与特有因子），且限制滚动 30 天
    - Pro 层：一键打包完整 8 年对齐的高性能 Parquet（40+字段+72智能交互特征）
✅ 🚀 极致性能：云端智能对接 Hugging Face 永久免密直链，避免内存溢出与死锁
"""
import streamlit as st
import pandas as pd
import os

def render_data_download_component():
    st.markdown("---")
    st.markdown("### 💾 MSTS 金融数据资产下载中心")
    st.caption("对标 Quant Research Starter Kit，多资产要素全对齐，包含国际宏观变量与预计算核心特征。")
    
    # 1. 环境与路径智能解析（本地优先，云端自适应降级至 Hugging Face 直链）
    local_parquet_path = r"D:\MSTS\outputs\final_tables\train_set_blinded.parquet"
    hf_cloud_url = "https://huggingface.co/datasets/lyuguoguang2026/msts-alpha-blinded/resolve/main/train_set_blinded.parquet"
    
    target_parquet = None
    is_cloud_environment = False

    # 优先检测本地高性能数据源
    if os.path.exists(local_parquet_path):
        target_parquet = local_parquet_path
    else:
        # 本地找不到则判定为 Streamlit Cloud 环境，启用全局高速直链通道
        target_parquet = hf_cloud_url
        is_cloud_environment = True
    
    # 获取当前用户权限
    user_plan = st.session_state.get("user_plan", "free")
    
    col1, col2 = st.columns(2)
    
    # ============================================================
    # 📊 1. 免费引流层（Free Dataset）- 动态脱敏与切片
    # ============================================================
    with col1:
        st.info("📊 **免费版引流资产 (Free Dataset)**")
        st.markdown(
            "- **内容范围**：最近 30 个交易日滚动全截面时序\n"
            "- **字段脱敏**：仅保留基础价量与持仓（不含宏观与特有特征）\n"
            "- **文件格式**：标准通用 CSV 格式"
        )
        
        try:
            # 动态生成免费版脱敏资产，防止白嫖高级变量
            @st.cache_data(ttl=3600)  # 缓存 1 小时，避免高并发读盘/请求
            def generate_free_dataset(path):
                # 仅读取必要列以极大减少网络IO与内存占用
                base_cols = [
                    'ts_code', 'trade_date', 'open', 'high', 'low', 'close', 
                    'pre_close', 'pre_settle', 'settle', 'change1', 'change2', 
                    'amount', 'vol', 'oi', 'oi_chg', 'symbol'
                ]
                df = pd.read_parquet(path, columns=base_cols)
                
                # 排序并提取最近 30 天
                df = df.sort_values(['trade_date', 'ts_code']).reset_index(drop=True)
                unique_dates = sorted(df['trade_date'].unique())[-30:]
                
                df_slice = df[df['trade_date'].isin(unique_dates)]
                return df_slice.to_csv(index=False).encode('utf-8')
            
            with st.spinner("正在切片生成免费数据集..."):
                csv_free_bytes = generate_free_dataset(target_parquet)
            
            st.download_button(
                label="📥 免费下载最近30天基础数据 (CSV)",
                data=csv_free_bytes,
                file_name="msts_research_kit_free.csv",
                mime="text/csv",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"免费数据集生成失败: {str(e)}")
            
    # ============================================================
    # 👑 2. 专业变现层（Pro Dataset）- 完整核心商业燃料
    # ============================================================
    with col2:
        if user_plan == "pro":
            st.success("👑 **专业版核心数据资产 (Pro Dataset)**")
            st.markdown(
                "- **内容范围**：**完整 8 年历史时序**（2017 -> 至今）\n"
                "- **全量变量**：40+多资产对齐字段 + 72个顶级交互特征\n"
                "- **文件格式**：工业级高性能、超轻量 Parquet 格式"
            )
            
            try:
                # 惰性读取完整文件字节流，防止大文件频繁 I/O
                @st.cache_data(ttl=7200)  # 云端环境对大文件进行缓存，大幅降低二次下载延迟
                def get_pro_file_bytes(path, is_cloud):
                    if is_cloud:
                        # 云端环境利用 pandas 高效拉取整个 Parquet 字节流
                        df_all = pd.read_parquet(path)
                        return df_all.to_parquet()
                    else:
                        # 本地环境直接物理读取
                        with open(path, "rb") as f:
                            return f.read()
                
                with st.spinner("正在打包高速下发全量资产流..."):
                    pro_bytes = get_pro_file_bytes(target_parquet, is_cloud_environment)
                
                st.download_button(
                    label="🚀 一键打包下载 8 年全量数据资产 (Parquet)",
                    data=pro_bytes,
                    file_name="MSTS_Research_Dataset_v1.0.parquet",
                    mime="application/octet-stream",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"专业版资产打包失败: {str(e)}")
        else:
            st.warning("🔒 **专业版核心数据资产 (Pro Dataset)**")
            st.markdown(
                "- ⚠️ **权限不足**：全量 8 年时序及高级特征字段已安全锁定。\n"
                "- **核心壁垒**：完美省去用户 2-4 周的多资产清洗与宏观对齐时间。\n"
                "- **内含精粹**：VIX/DXY/WTI/黄金等多维联动及智能交互算子。"
            )
            
            # 使用标准的 streamlit 凭证输入框实现就地升级解锁
            license_key = st.text_input("🔑 输入 Pro 激活凭证解锁全量资产", type="password")
            if license_key:
                # 这里保持你专属的独立硬编码密钥
                if license_key == "PanEn_Alpha_2026":
                    st.session_state["user_plan"] = "pro"
                    st.success("🎉 凭证验证成功！Pro 权限已激活，请重新点击或刷新页面下载。")
                    st.rerun()
                else:
                    st.error("❌ 凭证错误，请联系系统管理员或 Lyu 教授获取授权。")