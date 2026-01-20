import os

# --- 机器学习：初始五因子权重 ---
DEFAULT_WEIGHTS = {
    "量价爆发": 30,     # 成交量、MACD
    "趋势强度": 20,     # 均线、乖离率
    "资金流向": 20,     # 模拟大单、筹码
    "基本面安全垫": 15,  # 排除雷股
    "专家因子": 15       # DeepSeek 深度量化因子
}

# --- 进化配置 ---
EVOLUTION_LOOKBACK = 30  # 回测最近30次选股
TARGET_HORIZON = 3       # 重点考核 T+3 的收益率 (实现波段进化)

LLM_CONFIG = {
    "api_url": "https://api.deepseek.com/chat/completions",
    "api_key": "", 
    "model_name": "deepseek-chat",
}

LOG_DIR = "strategy_log"
HIST_PATH = os.path.join(LOG_DIR, "selection_history.csv")
if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)
