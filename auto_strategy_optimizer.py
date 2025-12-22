import pandas as pd
import akshare as ak
import json, os, warnings
from datetime import datetime
from trading_signal import TradingSignalGenerator
from llm_client import FreeLLMClient
from config import * # 这里会导入 WEIGHTS_PATH

warnings.filterwarnings('ignore')
os.makedirs("strategy_log", exist_ok=True)

class AutoStrategyOptimizer:
    def __init__(self):
        self.llm = FreeLLMClient()
        self.weights = self.load_weights()

    def load_weights(self):
        # 确保 WEIGHTS_PATH 已经从 config 导入
        if os.path.exists(WEIGHTS_PATH):
            try:
                with open(WEIGHTS_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return DEFAULT_FACTOR_WEIGHTS
        return DEFAULT_FACTOR_WEIGHTS

    def save_weights(self, new_weights):
        with open(WEIGHTS_PATH, 'w', encoding='utf-8') as f:
            json.dump(new_weights, f, indent=2, ensure_ascii=False)

    def run(self):
        print(f"🚀 [AI 智能选股] 启动... 策略权重: {self.weights}")
        
        try:
            # 1. 获取基础池
            df = ak.stock_zh_a_spot_em()
            df = df[~df['名称'].str.contains('ST|退', na=False)]
            df['市值'] = pd.to_numeric(df['总市值'], errors='coerce') / 1e8
            df = df[df['市值'] >= MIN_MARKET_CAP].head(50)
        except Exception as e:
            print(f"❌ 数据源连接失败: {e}"); return

        scored_list = []
        market_analysis_data = []

        # 2. 循环分析
        print("🔍 正在扫描优质标的...")
        for _, row in df.iterrows():
            tsg = TradingSignalGenerator(row['代码'])
            tsg.fetch_stock_data()
            inds = tsg.get_indicators()
            if not inds: continue
            
            # 计算加权分
            score = sum(inds[k] * (self.weights.get(k, 25)/100) for k in self.weights)
            
            item = row.to_dict()
            item['total_score'] = score
            scored_list.append(item)
            market_analysis_data.append(f"{row['名称']}: 涨幅{row['涨跌幅']}%, 指标{inds}")

        # 3. 排序并展示
        top_stocks = sorted(scored_list, key=lambda x: x['total_score'], reverse=True)[:TOP_N_STOCKS]

        print("\n" + "★"*40 + " 今日推荐操作 " + "★"*40)
        print(f"{'股票名称':<10} {'代码':<8} {'综合评分':<8} {'建议买入区间':<18} {'止损位':<8} {'仓位'}")
        print("-" * 92)
        
        for s in top_stocks:
            tsg = TradingSignalGenerator(s['代码'])
            tsg.fetch_stock_data()
            bounds = tsg.calculate_boundaries()
            price = s['最新价']
            print(f"{s['名称']:<10} {s['代码']:<8} {s['total_score']:<10.1f} {bounds['支撑']}-{price:<12} {round(bounds['支撑']*0.97, 2):<8} {SINGLE_STOCK_RATIO*100}%")

        # 4. LLM 进化
        print("\n🧠 DeepSeek 正在复盘今日风格并优化策略...")
        new_w = self.llm.evolve_strategy("\n".join(market_analysis_data[:10]), self.weights)
        if new_w and isinstance(new_w, dict):
            self.save_weights(new_w)
            print(f"✅ 策略进化完成，新权重已保存。")
        print("★"*92 + "\n")

if __name__ == "__main__":
    AutoStrategyOptimizer().run()