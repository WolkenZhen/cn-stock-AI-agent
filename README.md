AI-Stock-Agent: A Self-Evolving Quantitative Stock Selection System Powered by DeepSeek

🚀 Project OverviewAI-Stock-Agent is an AI-driven short-term quantitative stock selection system for the Chinese A-share market, enhanced by DeepSeek Large Language Models (LLMs).Unlike traditional quantitative strategies with static parameters, this project is built around a core concept: AI-driven strategy evolution. The system allows an LLM to continuously analyze market behavior and dynamically adjust factor weights based on detected market regimes

.🧠 From Static Quant to Self-Evolving AIDynamic Factor Reweighting: Reallocates weights across factors such as price momentum, volume expansion, and RSI daily.Real-time Hotspot Sensing (V2.0): No more hard-coded sectors. DeepSeek analyzes real-time news to identify trending sectors (AI, Low-altitude economy, etc.) dynamically.Quant Closed-Loop Feedback: Automatically reviews yesterday's picks. If performance was suboptimal, DeepSeek adjusts the algorithm's risk-appetite and factor bias for today.Zero Manual Tuning: Strategy logic evolves daily without manual code changes.


📂 Module OverviewFileRoleCore Responsibilityconfig.pyControl CenterAPI keys, market cap thresholds (default: 5B), and persistence paths.llm_client.pyAI BrainEnhanced: Hotspot sensing, strategy evolution, and final decision logic.trading_signal.pyData EngineFetches data via akshare; computes RSI, Support/Resistance, and 100% Upside Potential.auto_strategy_optimizer.pyPipelineExecutes full-market scans, evolution loops, and TOP5 ranking.executor.pyFormatterConverts signals into human-readable execution tables.main.pyDiagnosisCLI tool for deep AI diagnosis of a specific stock code.🛠️ Detailed Environment 

Setup & Installation1. System RequirementsOS: macOS (13.x+), Windows, or Linux.Python: 3.9 or higher.2. Step-by-Step InstallationFollow these exact commands in your terminal:Bash# 1. Clone the project or enter the directory
cd cn-stock-AI-agent

# 2. Create a virtual environment (venv)
# On macOS/Linux:
python3 -m venv venv
# On Windows:
python -m venv venv

# 3. Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate

# 4. Upgrade pip
pip install --upgrade pip

# 5. Install all required dependencies
pip install -r requirements.txt
▶️ Usage GuideStep 1: Configure API KeyEdit config.py and replace YOUR_API_KEY:PythonLLM_CONFIG = {
    "api_url": "https://api.deepseek.com/chat/completions",
    "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxx", # Your DeepSeek Key
    "model_name": "deepseek-chat",
    "temperature": 0.3,
}
Step 2: Run Daily Evolution & SelectionThis performs: Performance Review -> Hotspot Analysis -> Market Scan -> Final TOP5.Bashpython3 auto_strategy_optimizer.py
Step 3: Single Stock AI DiagnosisAnalyze any specific stock (e.g., Kweichow Moutai):Bashpython3 main.py --code 600519


中文版本 (Chinese Version)AI-Stock-Agent: 基于 DeepSeek 驱动的 A 股自进化量化选股系统


🚀 项目简介本项目是一款融合了 DeepSeek 大语言模型 增强能力的 A 股短线交易智能化工具。核心在于**“AI 驱动的策略迭代”**：系统通过 DeepSeek 实时分析盘面特征，动态调整因子权重。它能像人类交易员一样，在“趋势市”中调高动能因子，在“震荡市”中调高技术支撑因子，从而实现选股逻辑的每日进化。


🧠 AI 选股核心意义：从“静态”到“自进化”动态权重分配：DeepSeek 根据每日强势股特征，重新分配“涨幅动能、成交量、空间弹性”等因子的权重。实时热点感知 (V2.0 新特性)：完全去除行业硬编码。 系统自主分析实时新闻，动态锁定如“商业航天、低空经济、新材料”等当前热点。量化闭环反馈：启动时自动复盘昨日推荐股表现，根据盈亏结果反向修正今日算法的风险偏好。零代码迭代：策略随盘面每日进化，无需手动修改任何参数。


📂 模块说明文件名职能描述核心逻辑config.py系统指挥部配置 API Key、市值门槛（默认 50 亿）、持久化路径。llm_client.pyAI 大脑增强：实现热点感知、算法进化引擎、AI 决赛圈决策。trading_signal.py数据引擎抓取行情并计算 RSI、支撑位，以及基于振幅倒推 100% 爆发空间。auto_strategy_optimizer.py主流程执行“复盘进化 -> 热点捕捉 -> 打分 -> 产生 TOP5”的闭环任务。main.py单股诊断器命令行交互，输入代码即可获取 DeepSeek 生成的深度诊断。


🛠️ 详尽环境准备与安装命令1. 基础环境操作系统: macOS / Windows / LinuxPython: 3.9 或更高版本2. 分步骤安装指令请在终端中依次执行以下命令：Bash# 1. 进入项目目录
cd cn-stock-AI-agent

# 2. 创建虚拟环境 (venv)
# macOS/Linux:
python3 -m venv venv
# Windows:
python -m venv venv

# 3. 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
.\venv\Scripts\activate

# 4. 升级 pip
pip install --upgrade pip

# 5. 安装依赖
pip install -r requirements.txt
▶️ 运行指南第一步：配置 API编辑 config.py，在 api_key 处填入你的 DeepSeek Key。第二步：运行每日选股与策略进化系统将自动执行：复盘昨日 -> 锁定今日热点 -> 全场打分 -> AI 决策。Bashpython3 auto_strategy_optimizer.py
第三步：获取单只股票 AI 深度诊断输入股票代码获取 DeepSeek 的专业意见：Bashpython3 main.py --code 002149
📊 示例输出Plaintext🚀 [AI 进化选股引擎] 启动...
🔄 正在执行量化闭环进化... 基于昨日反馈修正权重。
🧠 正在通过 DeepSeek 检索实时盘面热点... 锁定：AI应用、低空经济。

★ ★ ★ ★ ★ ★ ★ ★ ★ ★ AI 深度决策选股报告 (TOP 5) ★ ★ ★ ★ ★ ★ ★ ★ ★ ★
1. 002149 西部材料 | 核心分:95.1 | 现价:46.2 | 预期:+108.4%
   🚩 交易计划：目标价 96.28 | 止损价 42.5
   📊 空间分析：位阶 [#######-------------] 支撑:43.1 | 阻力:52.8
--------------------------------------------------------------------------
✅ 策略进化完成！新权重已自动存入 factor_weights.json。
⚠️ 免责声明本工具仅用于量化交易研究与辅助选股，不构成投资建议。股市有风险，入市需谨慎。📜 LicenseMIT License
