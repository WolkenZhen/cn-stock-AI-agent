import pandas as pd
import akshare as ak
import os, warnings, csv
from datetime import datetime
from trading_signal import TradingSignalGenerator
from llm_client import FreeLLMClient

warnings.filterwarnings('ignore')

class AutoStrategyOptimizer:
    def __init__(self):
        self.llm = FreeLLMClient()
        # 初始化 5 个权重，总和 100
        self.weights = {"趋势": 30, "动能": 15, "成交": 15, "弹性": 15, "专家": 25}
        self.log_dir = "strategy_log"
        self.hist_path = os.path.join(self.log_dir, "selection_history.csv")

    def _get_feedback(self):
        if not os.path.exists(self.hist_path): return "暂无历史记录"
        try:
            df = pd.read_csv(self.hist_path).tail(10)
            # 这里简单返回个股收益率，供 AI 进化权重
            return df.to_string()
        except: return "反馈加载中"

    def run(self):
        print(f"\n🚀 [AI 进化选股引擎 V2.0] 启动")
        
        # 1. 算法闭环进化 (5 因子同步调整)
        fb = self._get_feedback()
        new_w = self.llm.evolve_strategy(fb, self.weights)
        if new_w: self.weights = new_w
        print(f"📈 权重自动优化：{self.weights}")

        # 2. AI 专家库同步 (静默模式，提取关键词)
        print("🧠 正在同步 AI 专家维度与题材画像...")
        hot_text, hot_keywords = self.llm.analyze_market_hotspots()
        # 不再打印 hot_text，直接进入选股

        # 3. 量化初筛
        spot_df = ak.stock_zh_a_spot_em()
        # 排除 ST 和退市，选取成交活跃的个股
        spot_df = spot_df[(spot_df['成交额'] > 800000000) & (~spot_df['名称'].str.contains('ST|退'))].head(200)

        pool = []
        for _, row in spot_df.iterrows():
            tsg = TradingSignalGenerator(row['代码'])
            tsg.fetch_stock_data()
            # 传入关键词计算第五个因子
            inds = tsg.get_indicators(name=row['名称'], hot_keywords=hot_keywords)
            if not inds: continue
            
            # 计算 5 因子综合得分
            score = sum(inds.get(k, 0) * (v/100) for k, v in self.weights.items())
            
            res = tsg.calculate_logic()
            if res:
                res.update({'name': row['名称'], 'code': row['代码'], 'score': round(score, 1)})
                pool.append(res)

        # 4. 专家最终决策
        candidates = sorted(pool, key=lambda x: x['score'], reverse=True)[:35]
        cand_str = "\n".join([f"编号:{i} | {c['name']}({c['code']}) | 综合分:{c['score']}" for i, c in enumerate(candidates)])
        indices = self.llm.ai_expert_selection(cand_str)
        
        top_5 = []
        for idx in indices:
            if idx < len(candidates):
                top_5.append(candidates[idx])
                if len(top_5) == 5: break
        if not top_5: top_5 = candidates[:5]

        # 5. 输出报告
        print("\n" + "★"*40 + " TOP 5 中国股市深度决策报告 " + "★"*40)
        for i, s in enumerate(top_5):
            print(f"{i+1}. {s['code']} | {s['name']} | 🏆 综合评分: {s['score']}")
            print(f"   🎯 操盘计划：预期涨幅: +{s['target_gain']}% | 目标价: {s['target']} | 止损价: {s['stop_loss']}")
            print("-" * 105)
        
        # 记录
        pd.DataFrame(top_5)[['code','name','score','price']].to_csv(self.hist_path, mode='a', index=False)
        print(f"💡 决策逻辑已融合今日热点关键词：{', '.join(hot_keywords)}")

if __name__ == "__main__":
    AutoStrategyOptimizer().run()