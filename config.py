import os

# --- 选股规模与并发配置 ---
SCAN_POOL_SIZE = 400       # 扫描全市场活跃度前400的个股
TOP_CANDIDATES = 25        # 量化初筛保留25只，供AI做深度博弈
MAX_WORKERS = 12           # 线程池并发数

# --- 存储路径 ---
LOG_DIR = "strategy_log"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

WEIGHTS_PATH = os.path.join(LOG_DIR, "factor_weights.json")
HISTORY_PATH = os.path.join(LOG_DIR, "selection_history.csv")

# --- 初始因子权重 (需与 TradingSignalGenerator 指标对应) ---
DEFAULT_WEIGHTS = {
    "涨幅动能": 30,
    "成交量放大": 20,
    "均线多头": 20,
    "价格弹性": 30
}

# --- DeepSeek 配置 ---
LLM_CONFIG = {
    "api_url": "https://api.deepseek.com/chat/completions",
    "api_key": "sk-a84f7971d767458cafeb3e757612ea16", 
    "model_name": "deepseek-chat",
    "temperature": 0.3,
}