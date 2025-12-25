AI-Stock-Agent: A Self-Evolving Quantitative Stock Selection System Powered by DeepSeek


🚀 Project Overview
AI-Stock-Agent is an AI-driven short-term quantitative stock selection system for the Chinese A-share market, enhanced by DeepSeek Large Language Models (LLMs).
Unlike traditional quantitative strategies with static parameters, this project is built around a core concept: AI-driven strategy evolution.
The system allows an LLM to continuously analyze market behavior and dynamically adjust factor weights based on detected market regimes. Just like an experienced human trader, the model emphasizes momentum factors in trending markets and support/technical factors in range-bound markets — enabling the strategy logic to evolve daily.

🧠 From Static Quant to Self-Evolving AI
Traditional quant strategies often fail due to parameter decay — a configuration that works for months may suddenly stop performing. This project addresses that problem by embedding DeepSeek directly into the strategy core:
1.
Dynamic Factor Reweighting
2.
Based on daily strong-stock patterns, DeepSeek reallocates weights across factors such as price momentum, volume expansion, moving averages, and RSI.
3.
4.
Real-time Hotspot Sensing (New in V2.0)
5.
The system no longer relies on hard-coded industries. It autonomously scans global news and policy updates to identify the top 3-5 trending sectors (e.g., AI, Space-tech, New Materials) for the current market cycle.
6.
7.
Closed-Loop Feedback Loop
8.
The system automatically reviews the performance of yesterday's recommended stocks. If the "Momentum" factor underperformed, the AI dynamically increases the weight of "Support/Defensive" factors for today's scan.
9.
10.
Zero Manual Tuning
11.
No hard-coded parameter changes. DeepSeek automatically updates the factor_weights.json configuration.
12.

📂 Module Overview
File	Role	Core Responsibility
config.py	System Control Center	Defines DeepSeek API keys, market cap thresholds, volume filters, and persistence paths.
llm_client.py	AI Brain	Wraps DeepSeek APIs for Hotspot Analysis, Strategy Evolution, and Final Decision making.
trading_signal.py	Data Engine	Fetches market data via akshare and computes RSI, Support/Resistance, and Upside Potential (100%+).
auto_strategy_optimizer.py	Automation Pipeline	Executes evolution loops, hotspot sensing, full-market scans, and TOP5 selection.
executor.py	Execution Formatter	Converts raw signals into human-readable trading suggestion tables.
explainer.py	Report Generator	Produces AI-generated daily strategy reports (.md) explaining each stock selection.
main.py	Single-Stock Analyzer	CLI tool for deep AI diagnosis by stock code.

🛠️ Environment Setup
1. System Requirements

OS: macOS (13.x+), Windows, or Linux


Python: 3.9 or higher

2. Installation
Bash
# Clone the projectcd cn-stock-AI-agent
# Create virtual environment
python3 -m venv venvsource venv/bin/activate
# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

▶️ Usage Guide
Step 1: Configure API Key
Edit config.py:
Python
LLM_CONFIG = {
    "api_url": "https://api.deepseek.com/chat/completions",
    "api_key": "YOUR_DEEPSEEK_API_KEY",
    "model_name": "deepseek-chat",
    "temperature": 0.3,
}
Step 2: Run Daily Selection & Evolution (V2.0 Pipeline)
This process performs: Performance Review -> Hotspot Sensing -> Quant Scan -> AI Final Selection.
Bash
python3 auto_strategy_optimizer.py
Step 3: Single Stock AI Diagnosis
For in-depth analysis of a specific stock:
Bash
python3 main.py --code 600519

📊 Output Artifacts
After execution, files are generated under strategy_log/:
1.
selection_history.csv — Used for the feedback loop (Tomorrow's evolution basis).
2.
3.
trading_signals_log.csv — Daily signals with buy ranges and target prices.
4.
5.
daily_report_YYYY-MM-DD.md — AI-generated strategy report.
6.

中文版本 (Chinese Version)
AI-Stock-Agent: 基于 DeepSeek 驱动的 A 股自进化量化选股系统


🚀 项目简介
本项目是一款融合了 DeepSeek 大语言模型 增强能力的 A 股短线交易智能化工具。
不同于传统的静态量化策略，本项目核心在于**“AI 驱动的策略迭代”**：系统通过 DeepSeek 实时分析盘面特征，动态调整因子权重。它能像人类交易员一样，在“趋势市”中调高动能因子，在“震荡市”中调高技术支撑因子，从而实现选股逻辑的每日进化。

🧠 AI 选股的核心意义：从“静态”到“自进化”
1.
动态权重分配：根据每日强势股的共同特征，重新分配“涨幅动能、成交量、空间弹性”等因子的权重。
2.
3.
实时热点感知 (V2.0 新特性)：系统不再死推固定板块，而是自主分析实时时事新闻，定位当前最具“翻倍黑马”潜力的行业。
4.
5.
闭环反馈修正：每日运行前自动复盘昨日推荐股表现。若昨日策略回撤，DeepSeek 会反向修正算法，提高今日的防御分值。
6.
7.
零代码迭代：无需手动修改代码，DeepSeek 会自动更新 factor_weights.json。
8.

📂 模块说明
文件名	职能描述	核心逻辑
config.py	系统指挥部	定义 API Key、选股市值门槛、成交量要求及持久化路径。
llm_client.py	AI 大脑	新增：热点感知逻辑、算法进化引擎、AI 决赛圈决策。
trading_signal.py	数据引擎	计算核心指标，并基于振幅倒推 100% 级别的爆发空间。
auto_strategy_optimizer.py	自动化主流程	执行“复盘进化 -> 热点捕捉 -> 打分 -> 产生 TOP5”的闭环。
main.py	单股诊断器	命令行工具，输入代码即可获取 DeepSeek 深度报告。

▶️ 运行指南
第一步：配置 API
编辑 config.py 填入 API_KEY。
第二步：运行每日选股与策略进化
Bash
python3 auto_strategy_optimizer.py
第三步：单只股票 AI 深度诊断
Bash
python3 main.py --code 002149

📊 示例输出
Plaintext
🚀 [AI 进化选股引擎] 启动：2025-12-25
🔄 正在执行量化闭环进化... 基于昨日反馈修正因子权重。
🧠 正在检索实时盘面热点... 锁定：AI应用、低空经济、新材料。
📄 AI 今日热点风向标：...（略）

★ ★ ★ ★ ★ ★ ★ ★ ★ ★ AI 深度决策选股报告 (TOP 5) ★ ★ ★ ★ ★ ★ ★ ★ ★ ★
1. 002149 西部材料 | 核心分:95.0 | 现价:46.2 | 预期:+108.4%
   🚩 交易计划：目标价 96.28 | 止损价 42.5
   📊 空间分析：位阶 [#######-------------] 支撑:43.1 | 阻力:52.8
--------------------------------------------------------------------------
🧠 DeepSeek 正在复盘并优化策略...
✅ 策略进化完成！

⚠️ 免责声明
本工具仅用于研究与辅助选股，不构成投资建议。股市有风险，入市需谨慎。

📜 License
MIT License
