import pandas as pd
import akshare as ak
import json, os, warnings
from datetime import datetime
from trading_signal import TradingSignalGenerator
from llm_client import FreeLLMClient
from config import *

warnings.filterwarnings('ignore')
os.makedirs("strategy_log", exist_ok=True)

class AutoStrategyOptimizer:
    def __init__(self):
        self.llm = FreeLLMClient()
        self.weights = self.load_weights()

    def load_weights(self):
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
        print(f"🚀 [AI 智能进化系统] 当前权重布局: {self.weights}")
        print("🔍 正在扫描市场并计算最优标的...")
        
        try:
            df = ak.stock_zh_a_spot_em()
            df = df[~df['名称'].str.contains('ST|退', na=False)]
            df['市值'] = pd.to_numeric(df['总市值'], errors='coerce') / 1e8
            df = df[df['市值'] >= MIN_MARKET_CAP].head(80) 
        except:
            print("❌ 无法连接数据源"); return

        scored_list = []
        market_analysis = []

        for _, row in df.iterrows():
            tsg = TradingSignalGenerator(row['代码'])
            tsg.fetch_stock_data()
            inds = tsg.get_indicators()
            if not inds: continue
            
            # AI 评分逻辑
            score = sum(inds[k] * (self.weights.get(k, 25)/100) for k in self.weights)
            
            res = tsg.calculate_logic()
            if res:
                res['name'] = row['名称']
                res['code'] = row['代码']
                res['total_score'] = score
                scored_list.append(res)
                market_analysis.append(f"{res['name']}: {row['涨跌幅']}%, 指标{inds}")

        # 按评分排序取前 N 名
        top_stocks = sorted(scored_list, key=lambda x: x['total_score'], reverse=True)[:TOP_N_STOCKS]

        print("\n" + "—"*30 + " AI 选股诊断报告 " + "—"*30)
        
        for i, s in enumerate(top_stocks):
            print(f"{i+1}. {s['code']} {s['name']}")
            print(f"   基础信息：最新价{s['price']}元 | 支撑位{s['support']}元 | 阻力位{s['resistance']}元")
            print(f"   均线状态：5日({s['ma']['ma5']}) | 20日({s['ma']['ma20']})")
            print(f"   交易信号：{s['signal']}")
            print(f"   操作建议：{s['advice']} | 止损价{s['stop_loss']}元 | 目标价{s['target']}元")
            print("-" * 65)

        # 触发 AI 进化
        print("\n🧠 DeepSeek 正在复盘今日风格并优化明日策略...")
        new_w = self.llm.evolve_strategy("\n".join(market_analysis[:10]), self.weights)
        if new_w and isinstance(new_w, dict):
            self.save_weights(new_w)
            print(f"✅ 策略进化完成！权重已自动更新。")
        print("—"*76 + "\n")

if __name__ == "__main__":
    AutoStrategyOptimizer().run()