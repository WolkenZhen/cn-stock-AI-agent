# AI-Stock-Agent: A Self-Evolving Quantitative Stock Selection System Powered by DeepSeek

## 🚀 Project Overview

AI-Stock-Agent is an **AI-driven short-term quantitative stock selection system** for the Chinese A-share market, enhanced by **DeepSeek Large Language Models (LLMs)**.

Unlike traditional quantitative strategies with static parameters, this project is built around a core concept:

> **AI-driven strategy evolution**.

The system allows an LLM to continuously analyze market behavior and **dynamically adjust factor weights** based on detected market regimes. Just like an experienced human trader, the model emphasizes momentum factors in trending markets and support/technical factors in range-bound markets — enabling the strategy logic to evolve *daily*.

---

## 🧠 From Static Quant to Self-Evolving AI

Traditional quant strategies often fail due to **parameter decay** — a configuration that works for months may suddenly stop performing.

This project addresses that problem by embedding DeepSeek directly into the strategy core:

1. **Dynamic Factor Reweighting**
   Based on daily strong-stock patterns, DeepSeek reallocates weights across factors such as price momentum, volume expansion, moving averages, and RSI.

2. **Market Regime Reasoning**
   The LLM analyzes whether the current market favors breakout trends or pullback-based opportunities.

3. **Zero Manual Tuning**
   No hard-coded parameter changes. DeepSeek automatically updates the `factor_weights.json` configuration.

---

## 📂 Module Overview

| File                         | Role                      | Core Responsibility                                                                                        |
| ---------------------------- | ------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `config.py`                  | **System Control Center** | Defines DeepSeek API keys, market cap thresholds (default: 5B RMB), volume filters, and persistence paths. |
| `llm_client.py`              | **AI Brain**              | Wraps DeepSeek APIs, transforming market data into logically reasoned JSON-based factor weights.           |
| `trading_signal.py`          | **Data Engine**           | Fetches market data via `akshare` and computes MA, RSI, support/resistance levels.                         |
| `auto_strategy_optimizer.py` | **Automation Pipeline**   | Executes full-market scans, factor scoring, TOP5 selection, and AI-driven evolution loops.                 |
| `executor.py`                | **Execution Formatter**   | Converts raw signals into human-readable trading suggestion tables.                                        |
| `explainer.py`               | **Report Generator**      | Produces AI-generated daily strategy reports (`.md`) explaining each stock selection.                      |
| `main.py`                    | **Single-Stock Analyzer** | CLI tool for deep AI diagnosis by stock code.                                                              |

---

## 🛠️ Environment Setup

### 1. System Requirements

* **OS**: macOS (13.x+), Windows, or Linux
* **Python**: 3.9 or higher

### 2. DeepSeek API Key

Register on the DeepSeek platform and obtain an API key.

### 3. Installation

```bash
# Clone the project
cd cn-stock-AI-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ▶️ Usage Guide

### Step 1: Configure API Key

Edit `config.py`:

```python
LLM_CONFIG = {
    "api_url": "https://api.deepseek.com/chat/completions",
    "api_key": "YOUR_DEEPSEEK_API_KEY",
    "model_name": "deepseek-chat",
    "temperature": 0.2,
}
```

---

### Step 2: Run Daily Stock Selection & Strategy Evolution

This process scans the entire market, selects the TOP 5 candidates, and lets DeepSeek adjust strategy weights for the next trading day.

```bash
python3 auto_strategy_optimizer.py
```

---

### Step 3: Single Stock AI Diagnosis

For in-depth analysis of a specific stock:

```bash
python3 main.py --code 600519
```

---

## 📊 Output Artifacts

After execution, the following files will be generated under `strategy_log/`:

1. **`factor_weights.json`** — Latest AI-adjusted factor weights.
2. **`trading_signals_log.csv`** — Daily trading signals with buy ranges, stop-loss, and target prices.
3. **`daily_report_YYYY-MM-DD.md`** — AI-generated daily market and strategy report.
4. **Terminal Output** — Formatted execution-ready tables.

### Example Output

```text
★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ TODAY'S RECOMMENDED ACTIONS ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★
Stock        Code      Score     Buy Range            Stop Loss   Position Size
--------------------------------------------------------------------------------------------
Kweichow Moutai 600519 88.5      1580.5–1620.0        1533.0      14%
CATL         300750    85.2      185.0–192.5          179.45     14%
...
🧠 DeepSeek is reviewing today’s market regime...
✅ Strategy evolution completed. Tomorrow’s weights favor volume expansion.
```

---

## 🌟 Key Highlights

* **True AI Closed Loop** — LLMs directly participate in quantitative factor optimization.
* **Adaptive Multi-Factor Scoring** — Strategy dynamically shifts between trending and ranging markets.
* **Explainable Trading Logic** — Every recommendation is grounded in transparent technical indicators.
* **Low Barrier Deployment** — No local model training required; powered by online LLM APIs.

---

## ⚠️ Disclaimer

This project is for **research and educational purposes only** and does not constitute investment advice. Trading involves risk. Use at your own discretion.

---

## 📜 License

MIT License

---

## 🤝 About the Author

Designed and implemented as an exploration of **LLM-powered decision intelligence systems**, focusing on adaptability, explainability, and real-world engineering constraints.








# AI-Stock-Agent: 基于 DeepSeek 驱动的 A 股自进化量化选股系统

## 🚀 项目简介

本项目是一款融合了 **DeepSeek 大语言模型** 增强能力的 A 股短线交易智能化工具。
不同于传统的静态量化策略，本项目核心在于**“AI 驱动的策略迭代”**：系统通过 DeepSeek 实时分析盘面特征，动态调整因子权重。它能像人类交易员一样，在“趋势市”中调高动能因子，在“震荡市”中调高技术支撑因子，从而实现选股逻辑的每日进化。

---

## 🧠 AI 选股的核心意义：从“静态”到“自进化”

传统量化程序往往面临“参数失效”的问题（即一套参数跑几个月就亏钱）。本项目通过 DeepSeek 解决了这一痛点：

1. **动态权重分配**：DeepSeek 会根据每日强势股的共同特征，重新分配“涨幅、成交量、均线、RSI”等因子的权重。
2. **盘面复盘逻辑**：DeepSeek 不仅是选股，更是在复盘。它能识别当前市场是偏向“放量突破”还是“缩量回调”。
3. **零代码迭代**：你无需手动修改代码参数，DeepSeek 会自动更新 `factor_weights.json` 配置文件。

---

## 📂 模块说明

| 文件名 | 职能描述 | 核心逻辑 |
| --- | --- | --- |
| `config.py` | **系统指挥部** | 定义 DeepSeek API Key、选股市值门槛（默认 50 亿）、成交量要求及持久化路径。 |
| `llm_client.py` | **AI 大脑** | 封装 DeepSeek 标准接口，负责接收市场数据并输出经过逻辑推理的 JSON 权重配置。 |
| `trading_signal.py` | **数据引擎** | 基于 `akshare` 抓取行情，计算 MA、RSI、支撑位/阻力位等核心技术指标。 |
| `auto_strategy_optimizer.py` | **自动化主流程** | 执行“全场扫描 -> 因子打分 -> 产生 TOP5 建议 -> 触发 AI 进化”的闭环任务。 |
| `executor.py` | **执行工具** | 将复杂的信号日志转化为人类可读的“实盘操作建议”表格。 |
| `explainer.py` | **报告生成器** | 调用 LLM 生成详细的策略日报（.md 格式），解释为何选中这些股票。 |
| `main.py` | **单股诊断器** | 提供命令行交互，输入股票代码即可获取 DeepSeek 生成的深度诊断报告。 |

---

## 🛠️ 环境准备与安装

### 1. 基础环境

* **操作系统**: macOS (已适配 13.x+) / Windows / Linux
* **Python**: 3.9 或更高版本

### 2. 获取 DeepSeek API

访问 [DeepSeek 开放平台](https://platform.deepseek.com/) 注册并获取 `API_KEY`。

### 3. 安装依赖

```bash
# 克隆项目 (假设你已上传)
cd cn-stock-AI-agent

# 安装核心依赖
pip install --upgrade pip
pip install -r requirements.txt

```
python3 -m venv venv
source venv/bin/activate
---

## 运行指南

### 第一步：配置 API

编辑 `config.py` 文件，填入你的 DeepSeek Key：

```python
LLM_CONFIG = {
    "api_url": "https://api.deepseek.com/chat/completions",
    "api_key": "你的_DEEPSEEK_API_KEY", # <--- 填入此处
    "model_name": "deepseek-chat",
    "temperature": 0.2,
}

```

### 第二步：运行每日选股与策略进化

系统将自动扫描全市场，筛选 TOP 5 潜力股，并让 DeepSeek 根据今日盘面调整明天的因子权重。

```bash
python3 auto_strategy_optimizer.py

```

### 第三步：获取单只股票 AI 深度诊断

如果你有心仪的股票，想看看 AI 的专业意见：

```bash
python3 main.py --code 600519

```

---

## 📊 运行结果输出说明

项目运行后，会在 `strategy_log/` 目录下生成以下资产：

1. **`factor_weights.json`**: 被 DeepSeek 动态修改后的最新因子权重。
2. **`trading_signals_log.csv`**: 每日产生的交易信号，包含买入区间、止损价、目标价。
3. **`daily_report_YYYY-MM-DD.md`**: AI 生成的策略日报，包含市场风格判断与风险提示。
4. **终端输出**: 直接展示格式化的实操表格（如下所示）。

**示例输出表格：**

```text
★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ 今日推荐操作 ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★
股票名称     代码      综合评分   建议买入区间        止损位     建议仓位
--------------------------------------------------------------------------------------------
贵州茅台     600519    88.5      1580.5-1620.0      1533.0     14%
宁德时代     300750    85.2      185.0-192.5        179.45     14%
...
🧠 DeepSeek 正在复盘今日风格并优化策略...
✅ 策略进化完成，明日权重将向“成交量放大”倾斜。

```

---



# AI-Stock-Agent: 基于 DeepSeek 驱动的 A 股自进化量化选股系统

[![DeepSeek Powered](https://img.shields.io/badge/LLM-DeepSeek-blue.svg)](https://platform.deepseek.com/)
[![License-MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 项目亮点
本项目并非简单的量化脚本，而是一个具备**自进化能力**的选股机器人。

1. **DeepSeek 智能大脑**：每日盘后自动复盘，根据强势股特征（如：是缩量上涨还是放量突破）动态调整因子权重。
2. **多因子动态评分**：摆脱静态策略失效的困扰，AI 自动根据市场风格（震荡 vs 趋势）切换配置。
3. **结构化操盘建议**：输出极简、专业的买卖点指导，包含支撑位、阻力位、止损位及均线偏离度。

## 🌟 亮点功能总结

* **真正的 AI 闭环**：不仅仅是用 LLM 读新闻，而是让 LLM 参与量化核心因子的权重分配。
* **低门槛实操**：不需要复杂的本地模型部署，直接通过在线 API 实现最强 LLM 的量化赋能。
* **抗风险设计**：所有 AI 建议均基于严格的技术指标（支撑位/止损位）计算，确保交易逻辑在可控范围内。

---

## 📂 项目结构
- `config.py`: 配置 API Key、市值门槛及持久化路径。
- `llm_client.py`: 封装 DeepSeek 接口，处理策略进化逻辑。
- `trading_signal.py`: 计算 MA5/MA20、RSI、支撑阻力位及交易逻辑。
- `auto_strategy_optimizer.py`: 主程序，执行全场扫描、AI 评分与结果展示。

---

## 🚀 运行效果展示
程序运行后，您将获得如下形式的专业分析报告：

```text
1. 601899 紫金矿业
   基础信息：最新价16.53元 | 支撑位15.12元 | 阻力位16.78元
   均线状态：5日(16.16) | 20日(15.42)
   交易信号：买入/持有
   操作建议：趋势走强，建议继续持有 | 止损价14.67元 | 目标价17.62元
-----------------------------------------------------------------
🧠 DeepSeek 正在复盘今日风格并优化明日策略...
✅ 策略进化完成！新权重已自动更新：{'涨幅动能': 20, '成交量放大': 40, ...}
---

## ⚠️ 免责声明

本工具仅用于量化交易研究与辅助选股，不构成任何投资建议。股市有风险，入市需谨慎。

---
