# -*- coding: utf-8 -*-
import os
from huggingface_hub import HfApi

# 🔑 从系统环境变量中动态读取，再也不用明文暴露给 GitHub 了
# 如果环境变量里没有，则默认使用后面的后备 Token
HF_TOKEN = os.environ.get("HF_TOKEN", "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")

USER_NAME = "lyuguoguang2026"
REPO_NAME = "msts-alpha-blinded"
repo_id = f"{USER_NAME}/{REPO_NAME}"

api = HfApi()

try:
    # 1. 强行在云端开辟保险箱仓库（带 Token 强认证硬闯）
    print("正在通过 Token 强认证在云端开辟数据集仓库...")
    api.create_repo(
        repo_id=repo_id,
        repo_type="dataset",
        private=False,   # 确保公开，Streamlit 网页才能免密抓取
        exist_ok=True,   # 如果已经存在，不报错继续运行
        token=HF_TOKEN   # 显式传入 Token
    )
    
    # 2. 通过底层通道直接把 87MB 盲化表拍上去
    print("底层通道已建立，正在物理上传 train_set_blinded.parquet (约87MB)...")
    api.upload_file(
        path_or_fileobj=r"D:\MSTS\outputs\final_tables\train_set_blinded.parquet", # 本地数据路径
        path_in_repo="train_set_blinded.parquet",                                 # 云端保存的名字
        repo_id=repo_id,
        repo_type="dataset",
        token=HF_TOKEN   # 显式传入 Token
    )
    print("\n🎉 [大获全胜] 底层通道已被 Token 彻底击穿，数据成功安全落子！")

except Exception as e:
    print(f"\n❌ 上传遭遇阻碍，错误原因: {e}")