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
        self.weights = {"趋势": 30, "动能": 15, "成交": 15, "弹性": 15, "专家": 25}
        self.log_dir = "strategy_log"
        self.hist_path = os.path.join(self.log_dir, "selection_history.csv")
        if not os.path.exists(self.log_dir): os.makedirs(self.log_dir)

    def _get_feedback(self):
        if not os.path.exists(self.hist_path): return "暂无历史记录"
        try:
            df = pd.read_csv(self.hist_path, quotechar='"', on_bad_lines='skip')
            if df.empty or 'price' not in df.columns: return "记录为空"
            # 获取实时价格进行收益计算
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            recent = df.dropna(subset=['price']).tail(10).copy()
            
            current_spot = ak.stock_zh_a_spot_em()
            current_spot['最新价'] = pd.to_numeric(current_spot['最新价'], errors='coerce')
            
            feedback = []
            for _, row in recent.iterrows():
                code = str(row['code']).zfill(6)
                spot = current_spot[current_spot['代码'] == code]
                if not spot.empty:
                    now_val = spot.iloc[0]['最新价']
                    old_val = row['price']
                    if pd.notna(now_val) and old_val > 0:
                        profit = (float(now_val) / float(old_val) - 1) * 100
                        feedback.append(f"{row['name']}({code}): {profit:.1f}%")
            return " | ".join(feedback) if feedback else "计算中..."
        except: return "反馈加载中"

    def run(self):
        # 补回时间戳并去掉冗余提示
        print(f"\n🚀 [AI 进化选股引擎 V2.0] 启动：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        fb = self._get_feedback()
        print(f"📊 近期表现：{fb}")

        # 1. 自动进化权重
        new_w = self.llm.evolve_strategy(fb, self.weights)
        if new_w and all(k in new_w for k in self.weights):
            self.weights = new_w
            print(f"📈 权重自动优化：{self.weights}")

        # 2. 静默获取热点（已删冗余打印）
        _, hot_keywords = self.llm.analyze_market_hotspots()

        # 3. 量化扫描
        spot_df = ak.stock_zh_a_spot_em()
        spot_df = spot_df[(spot_df['成交额'] > 600000000) & (~spot_df['名称'].str.contains('ST|退'))].head(200)

        pool = []
        for _, row in spot_df.iterrows():
            tsg = TradingSignalGenerator(row['代码'])
            tsg.fetch_stock_data()
            inds = tsg.get_indicators(name=row['名称'], hot_keywords=hot_keywords)
            if not inds: continue
            
            # 动态 5 因子综合计分
            score = sum(inds.get(k, 0) * (v/100) for k, v in self.weights.items())
            res = tsg.calculate_logic()
            if res:
                res.update({'name': row['名称'], 'code': row['代码'], 'score': round(score, 1)})
                pool.append(res)

        # 4. 深度专家决策
        candidates = sorted(pool, key=lambda x: x['score'], reverse=True)[:35]
        cand_str = "\n".join([f"编号:{i} | {c['name']}({c['code']}) | 综合分:{c['score']}" for i, c in enumerate(candidates)])
        indices = self.llm.ai_expert_selection(cand_str)
        
        top_5 = []
        for idx in indices:
            if idx < len(candidates) and candidates[idx]['code'] not in [x['code'] for x in top_5]:
                top_5.append(candidates[idx])
                if len(top_5) == 5: break
        if not top_5: top_5 = candidates[:5]

        # 5. 记录并输出
        pd.DataFrame(top_5)[['code','name','score','price']].to_csv(self.hist_path, mode='a', index=False, quoting=csv.QUOTE_ALL)

        print("\n" + "★"*48 + " TOP 5 AI 深度决策报告 " + "★"*48)
        for i, s in enumerate(top_5):
            print(f"{i+1}. {s['code']} | {s['name']} | 🏆 综合评分: {s['score']}")
            print(f"   🎯 操盘计划：预期涨幅: +{s['target_gain']}% | 目标价: {s['target']} | 止损价: {s['stop_loss']}")
            print("-" * 110)
        
        if hot_keywords:
            print(f"💡 AI 策略提示：已对齐今日热点关键词：{', '.join(hot_keywords[:5])}")

if __name__ == "__main__":
    AutoStrategyOptimizer().run()