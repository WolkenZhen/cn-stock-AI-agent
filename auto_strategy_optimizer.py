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
        # 确保 Key 与 TradingSignalGenerator 输出一致
        self.weights = {"趋势": 50, "动能": 20, "成交": 15, "弹性": 15}
        self.log_dir = "strategy_log"
        self.hist_path = os.path.join(self.log_dir, "selection_history.csv")
        if not os.path.exists(self.log_dir): os.makedirs(self.log_dir)

    def _get_feedback(self):
        if not os.path.exists(self.hist_path): return "暂无历史记录"
        try:
            df = pd.read_csv(self.hist_path, quotechar='"', on_bad_lines='skip')
            if df.empty or 'price' not in df.columns: return "记录为空"
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
            return " | ".join(feedback) if feedback else "正在匹配实时行情..."
        except: return "反馈加载中"

    def run(self):
        print(f"\n🚀 [AI 进化选股引擎] 启动：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        fb = self._get_feedback()
        print(f"📊 近期表现：{fb}")
        
        if "%" in fb:
            new_w = self.llm.evolve_strategy(fb, self.weights)
            if new_w and all(k in new_w for k in self.weights):
                self.weights = new_w
                print(f"📈 权重自动优化：{self.weights}")

        print("🧠 正在同步 AI 市场热点并分析专家维度...")
        hotspots = self.llm.analyze_market_hotspots() # 后台分析，不再直接 print

        # 量化初筛选
        df = ak.stock_zh_a_spot_em()
        df = df[(df['成交额'] > 600000000) & (~df['名称'].str.contains('ST|退'))]
        df = df.sort_values(by='成交额', ascending=False).head(200)

        pool = []
        for _, row in df.iterrows():
            tsg = TradingSignalGenerator(row['代码'])
            tsg.fetch_stock_data()
            inds = tsg.get_indicators()
            if not inds or inds.get("趋势", 0) < 1: continue
            
            # 关键修复：确保 inds 的 key 与 self.weights 对应
            score = sum(inds.get(k, 0) * (v/100) for k, v in self.weights.items())
            res = tsg.calculate_logic()
            if res:
                res.update({'name': row['名称'], 'code': row['代码'], 'score': score})
                pool.append(res)

        candidates = sorted(pool, key=lambda x: x['score'], reverse=True)[:35]
        cand_str = "\n".join([f"编号:{i} | {c['name']}({c['code']}) | 技术评分:{c['score']:.1f}" for i, c in enumerate(candidates)])
        
        # DeepSeek 专家最终决策
        indices = self.llm.ai_expert_selection(f"【热点环境】:{hotspots}\n【量化候选池】:\n{cand_str}")
        
        seen_codes = set()
        top_5 = []
        for idx in indices:
            if idx < len(candidates):
                item = candidates[idx]
                if item['code'] not in seen_codes:
                    top_5.append(item)
                    seen_codes.add(item['code'])
                    if len(top_5) == 5: break

        # 如果 AI 抽风返回编号不对，兜底取前5
        if not top_5: top_5 = candidates[:5]

        # 记录
        pd.DataFrame(top_5)[['code','name','score','price']].to_csv(self.hist_path, mode='a', index=False, quoting=csv.QUOTE_ALL)

        print("\n" + "★"*48 + " TOP 5 AI 深度决策报告 " + "★"*48)
        for i, s in enumerate(top_5):
            pos_val = int(s['position_pct']/5)
            pos_bar = f"[{'#' * pos_val}{'-' * (20 - pos_val)}]"
            print(f"{i+1}. {s['code']} | {s['name']} | 🏆 综合评分: {s['score']:.1f}")
            print(f"   💰 财务参考：现价: {s['price']} | 支撑: {s['support']} | 位阶: {pos_bar} {s['position_pct']}%")
            print(f"   🎯 操盘计划：预期涨幅: +{s['target_gain']}% | 目标价: {s['target']} | 止损价: {s['stop_loss']}")
            print("-" * 110)
        
        print(f"💡 AI 选股逻辑已融合今日热点（{len(hotspots)}字策略已执行）。")

if __name__ == "__main__":
    AutoStrategyOptimizer().run()