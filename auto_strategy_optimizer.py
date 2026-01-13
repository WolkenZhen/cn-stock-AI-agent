import pandas as pd
import akshare as ak
import os, warnings, csv, json, time
from datetime import datetime
from trading_signal import TradingSignalGenerator
from llm_client import FreeLLMClient

warnings.filterwarnings('ignore')

class AutoStrategyOptimizer:
    def __init__(self):
        self.llm = FreeLLMClient()
        self.weights = {"趋势": 30, "动能": 20, "成交": 15, "弹性": 15, "专家": 20}
        self.log_dir = "strategy_log"
        self.hist_path = os.path.join(self.log_dir, "selection_history.csv")
        if not os.path.exists(self.log_dir): os.makedirs(self.log_dir)

    def _get_feedback_str(self):
        if not os.path.exists(self.hist_path): return "暂无历史记录"
        try:
            df = pd.read_csv(self.hist_path, names=['code','name','score','price'], header=None).tail(10)
            df['code'] = df['code'].astype(str).str.zfill(6)
            current_spot = ak.stock_zh_a_spot_em()
            fb = []
            for _, r in df.iterrows():
                spot = current_spot[current_spot['代码'] == r['code']]
                if not spot.empty:
                    now_p = float(spot.iloc[0]['最新价'])
                    profit = (now_p / float(r['price']) - 1) * 100
                    fb.append(f"{r['name']}:{profit:.1f}%")
            return " | ".join(fb) if fb else "等待行情数据"
        except: return "复盘中..."

    def run(self):
        print(f"\n🚀 [AI 进化选股引擎 V2.0 - 千股扫描&强化版] 启动：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 复盘近期表现
        fb_str = self._get_feedback_str()
        print(f"📊 近期表现：{fb_str}")
        
        # 2. 权重进化及详细显示
        full_res = self.llm.evolve_strategy(fb_str, self.weights)
        if full_res and isinstance(full_res, dict):
            print(f"📈 权重自动优化详情：")
            print(json.dumps(full_res, indent=4, ensure_ascii=False))
            raw_w = full_res.get("新权重", full_res)
            self.weights = {k: v for k, v in raw_w.items() if isinstance(v, (int, float))}
        
        # 3. 获取 AI 初筛标准
        ai_keywords, ai_shape = self.llm.get_market_selection_criteria()
        print(f"💡 AI 初筛建议：关键词({','.join(ai_keywords)}) | 形态({ai_shape})")

        # 4. 全市场 1000 只活跃股技术扫描
        print(f"🔍 正在执行全市场前 1000 只活跃股技术扫描...")
        spot_df = ak.stock_zh_a_spot_em()
        spot_df = spot_df[~spot_df['名称'].str.contains('ST|退')].sort_values(by='成交额', ascending=False).head(1000)

        full_pool = []
        for _, row in spot_df.iterrows():
            code = str(row['代码']).zfill(6)
            tsg = TradingSignalGenerator(code) 
            tsg.fetch_stock_data()
            inds = tsg.get_indicators(name=row['名称'], hot_keywords=ai_keywords)
            if not inds: continue
            
            score = sum(inds.get(k, 0) * (float(v)/100) for k, v in self.weights.items())
            res = tsg.calculate_logic()
            if res:
                res.update({'name': row['名称'], 'code': code, 'score': round(score, 1)})
                full_pool.append(res)

        # 5. 锁定 300 只精英池
        elite_pool = sorted(full_pool, key=lambda x: x['score'], reverse=True)[:300]
        elite_table = "\n".join([f"{c['code']} | {c['name']} | 评分:{c['score']} | 位阶:{c['position_pct']}%" for c in elite_pool])

        # 6. DeepSeek 终极裁定
        print(f"🧠 DeepSeek 正在从 300 只精英股中进行最终决策...")
        final_decisions = self.llm.ai_deep_decision(f"{ai_keywords} - {ai_shape}", elite_table)

        # 7. 打印结果 (修改为 10 只)
        print("\n" + "🎯" * 15 + " 今日新推个股决策 (1000选300选10) " + "🎯" * 15)
        top_count = 0
        for code, reason in final_decisions.items():
            match = next((x for x in elite_pool if str(x['code']) in str(code)), None)
            if match:
                print(f"{top_count+1}. {match['code']} | {match['name']} | 🏆 量化评分: {match['score']}")
                print(f"   >>> 💡 专家深度理由: {reason}")
                print(f"   >>> 💰 今日建议买入委托价: {match['entrust_buy']}")
                print(f"   🎯 止盈目标: {match['target']} | 止损参考: {match['stop_loss']}")
                print("-" * 80)
                # 保存到记录
                with open(self.hist_path, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([match['code'], match['name'], match['score'], match['price']])
                top_count += 1
                if top_count >= 10: break

        if top_count == 0:
            print("⚠️ AI 决策返回异常，输出量化排名前 10 名：")
            for i, s in enumerate(elite_pool[:10]):
                print(f"{i+1}. {s['code']} | {s['name']} | 评分: {s['score']}")

if __name__ == "__main__":
    AutoStrategyOptimizer().run()