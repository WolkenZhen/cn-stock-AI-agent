import pandas as pd
import akshare as ak
import os, warnings, time
from datetime import datetime
from trading_signal import TradingSignalGenerator
from llm_client import FreeLLMClient
from config import *

warnings.filterwarnings('ignore')

class AutoStrategyOptimizer:
    def __init__(self):
        self.llm = FreeLLMClient()
        self.weights = {"涨幅动能": 35, "成交量放大": 25, "空间弹性": 40}
        self.hist_path = "strategy_log/selection_history.csv"

    def evolve_logic(self):
        if os.path.exists(self.hist_path):
            print("🔄 正在执行量化闭环进化...")
            hist = pd.read_csv(self.hist_path).tail(5).to_string()
            self.weights = self.llm.evolve_strategy(hist, self.weights)
            print(f"📈 算法进化完成，今日权重: {self.weights}")

    def run(self):
        print(f"\n🚀 [AI 进化选股引擎] 启动：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.evolve_logic() # 量化闭环

        print("🧠 正在通过 DeepSeek 检索全网实时热点...")
        hotspots = self.llm.analyze_market_hotspots() # 去 Hard-coding

        df = ak.stock_zh_a_spot_em()
        df = df[~df['名称'].str.contains('ST|退', na=False)]
        df['成交额'] = pd.to_numeric(df['成交额'], errors='coerce')
        df = df.sort_values(by='成交额', ascending=False).head(300)

        results = []
        for _, row in df.iterrows():
            tsg = TradingSignalGenerator(row['代码']) # 修复 TypeError
            tsg.fetch_stock_data()
            inds = tsg.get_indicators()
            if not inds: continue
            
            score = sum(inds.get(k, 0) * (v/100) for k, v in self.weights.items())
            res = tsg.calculate_logic()
            if res:
                res.update({'name': row['名称'], 'code': row['代码'], 'total_score': score})
                results.append(res)

        candidates = sorted(results, key=lambda x: x['total_score'], reverse=True)[:50]
        context = "\n".join([f"编号:{i} | {c['name']}({c['code']}) | 预期:+{c['target_gain']}%" for i, c in enumerate(candidates)])
        
        prompt = f"今日热点:{hotspots}\n\n候选池:\n{context}\n\n选出 5 个最符合热点且空间大的编号，逗号分隔。"
        indices = self.llm.ai_final_selection_with_prompt(prompt)
        top_5 = [candidates[i] for i in indices if i < len(candidates)]

        # 记录结果供明日复盘
        os.makedirs("strategy_log", exist_ok=True)
        pd.DataFrame(top_5)[['code', 'name', 'target_gain']].to_csv(self.hist_path, mode='a', index=False)

        print("\n" + "★"*45 + " AI 深度决策选股报告 (TOP 5) " + "★"*45)
        for i, s in enumerate(top_5):
            bar = f"[{'#' * int(s['position_pct']/5)}{'-' * (20 - int(s['position_pct']/5))}]"
            print(f"{i+1}. {s['code']} {s['name']} | 核心分:{s['total_score']:.1f} | 现价:{s['price']} | 预期:+{s['target_gain']}%")
            print(f"   🚩 交易计划：目标价 {s['target']} | 止损价 {s['stop_loss']}")
            # 修复 KeyError：将 '支撑' 改为 'support'
            print(f"   📊 空间分析：位阶 {bar} {s['position_pct']}% | 支撑:{s['support']} | 阻力:{s['resistance']}")
            print("-" * 105)

if __name__ == "__main__":
    AutoStrategyOptimizer().run()