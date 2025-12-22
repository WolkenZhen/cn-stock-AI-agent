import os

# --- 选股门槛配置 (放宽标准确保能选出股票) ---
MIN_MARKET_CAP = 50   # 最小市值（亿）
MIN_AVG_VOLUME = 0.3  # 最小日均成交额（亿）
EXCLUDE_ST = True     # 排除ST
TOP_N_STOCKS = 5      # 选股数量
SINGLE_STOCK_RATIO = 0.14  # 单只建议仓位

# --- DeepSeek 在线 API 配置 ---
LLM_CONFIG = {
    "api_url": "https://api.deepseek.com/chat/completions",
    "api_key": "sk-a84f7971d767458cafeb3e757612ea16", # <--- 记得改这里
    "model_name": "deepseek-chat",
    "temperature": 0.2,
}

# --- 因子权重持久化 (修复报错的关键) ---
WEIGHTS_PATH = "strategy_log/factor_weights.json"

# 初始因子权重
DEFAULT_FACTOR_WEIGHTS = {
    "涨幅动能": 30,
    "成交量放大": 25,
    "均线多头": 25,
    "RSI强弱": 20
}