import os

# --- 规模配置：全市场深挖 ---
SCAN_POOL_SIZE = 1000      # 覆盖全市场前 1000 名活跃个股
TOP_CANDIDATES = 80        # 给 AI 更多选择，便于锁定特定题材
MAX_WORKERS = 20           

# --- 2025年12月 核心热点行业 (代码通过这些关键词对齐西部材料) ---
HOT_SECTORS = ["航空航天", "军工", "钛合金", "新材料", "卫星", "核电"]

# --- 因子权重：从“稳健”转向“暴力美学” ---
DEFAULT_WEIGHTS = {
    "行业热度评分": 35,     # 匹配当前最火的商业航天/军工新材料
    "筹码换手强度": 25,     # 西部材料近期的高换手是关键特征
    "突破爆发力": 30,       # 寻找斜率最高、振幅最大的个股
    "资金护盘": 10          # 基础支撑
}

LLM_CONFIG = {
    "api_url": "https://api.deepseek.com/chat/completions",
    "api_key": "", 
    "model_name": "deepseek-chat",
    "temperature": 0.7,     # 提高温度，让 AI 更有想象力和联想能力
}