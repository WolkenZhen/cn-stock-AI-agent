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
        self.weights = {"趋势": 50, "动能": 20, "成交": 15, "弹性": 15}
        self.log_dir = "strategy_log"
        self.hist_path = os.path.join(self.log_dir, "selection_history.csv")
        if not os.path.exists(self.log_dir): os.makedirs(self.log_dir)

    def _get_feedback(self):
        if not os.path.exists(self.hist_path): return "暂无历史记录"
        try:
            df = pd.read_csv(self.hist_path, quotechar='"', on_bad_lines='skip')
            if df.empty or 'price' not in df.columns: return "记录为空或格式不兼容"
            
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            recent = df.dropna(subset=['price']).tail(10).copy()
            if recent.empty: return "无有效历史价格数据"

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
        except Exception as e:
            return f"反馈数据解析异常: {e}"

    def evolve(self):
        fb = self._get_feedback()
        print(f"📊 近期表现：{fb}")
        if "%" in fb:
            new_w = self.llm.evolve_strategy(fb, self.weights)
            if new_w and all(k in new_w for k in ["趋势", "动能", "成交", "弹性"]):
                self.weights = new_w
                print(f"📈 权重自动优化：{self.weights}")

    def run(self):
        # 补全日期和时间
        print(f"\n🚀 [AI 进化选股引擎] 启动：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.evolve()

        print("🧠 正在同步 AI 市场热点...")
        hotspots = self.llm.analyze_market_hotspots()

        df = ak.stock_zh_a_spot_em()
        # 初始过滤：成交额 > 6亿，剔除ST
        df = df[(df['成交额'] > 600000000) & (~df['名称'].str.contains('ST'))]
        df = df.sort_values(by='成交额', ascending=False).head(250)

        pool = []
        for _, row in df.iterrows():
            tsg = TradingSignalGenerator(row['代码'])
            tsg.fetch_stock_data()
            inds = tsg.get_indicators()
            if not inds or inds.get("趋势", 0) < 1: continue
            
            score = sum(inds.get(k, 0) * (v/100) for k, v in self.weights.items())
            res = tsg.calculate_logic()
            if res:
                res.update({'name': row['名称'], 'code': row['代码'], 'score': score})
                pool.append(res)

        candidates = sorted(pool, key=lambda x: x['score'], reverse=True)[:35]
        cand_str = "\n".join([f"{i}. {c['name']}({c['code']}) Score:{c['score']:.1f}" for i, c in enumerate(candidates)])
        
        indices = self.llm.ai_final_selection_with_prompt(f"热点:{hotspots}\n池:\n{cand_str}\n选出5个最稳个股编号。")
        
        # 优化：去重并提取前5个唯一索引
        unique_indices = []
        for idx in indices:
            if idx not in unique_indices and idx < len(candidates):
                unique_indices.append(idx)
        top_5 = [candidates[i] for i in unique_indices[:5]]

        # 记录
        pd.DataFrame(top_5)[['code','name','score','price']].to_csv(self.hist_path, mode='a', index=False, quoting=csv.QUOTE_ALL)

        print("\n" + "★"*48 + " TOP 5 AI 深度决策报告 " + "★"*48)
        for i, s in enumerate(top_5):
            pos = int(s['position_pct'] / 5)
            pos_bar = f"[{'#' * pos}{'-' * (20 - pos)}]"
            
            print(f"{i+1}. {s['code']} | {s['name']} | 🏆 综合评分: {s['score']:.1f}")
            print(f"   💰 财务参考：现价: {s['price']} | 支撑: {s['support']} | 阻力: {s['resistance']} | 位阶: {pos_bar} {s['position_pct']}%")
            print(f"   🎯 操盘计划：预期涨幅: +{s['target_gain']}% | 目标价: {s['target']} | 止损价: {s['stop_loss']} (ATR动态)")
            print("-" * 110)
        
        # 修复：删除 [:150] 限制，输出完整热点分析
        print(f"💡 AI 今日关注方向:\n{hotspots}")

if __name__ == "__main__":
    AutoStrategyOptimizer().run()