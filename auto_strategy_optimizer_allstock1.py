import pandas as pd
import akshare as ak
import os, warnings, csv, json, time, re
from datetime import datetime
from trading_signal import TradingSignalGenerator
from llm_client import FreeLLMClient

warnings.filterwarnings('ignore')

class AutoStrategyOptimizer:
    def __init__(self):
        self.llm = FreeLLMClient()
        # 初始权重
        self.weights = {"趋势": 30, "动能": 20, "成交": 15, "弹性": 15, "专家": 20}
        self.log_dir = "strategy_log"
        self.hist_path = os.path.join(self.log_dir, "selection_history.csv")
        if not os.path.exists(self.log_dir): os.makedirs(self.log_dir)

    def check_market_risk(self):
        """分析上证指数(sh000001)近30个交易日走势，给出买入建议"""
        print(f"📊 正在深度分析大盘基本面趋势 (近30个交易日)...")
        try:
            df_index = ak.stock_zh_index_daily(symbol="sh000001")
            if df_index.empty: return "未知", False
            
            df_index['ma20'] = df_index['close'].rolling(20).mean()
            recent_30 = df_index.tail(30).copy()
            
            curr_p = recent_30['close'].iloc[-1]
            ma20_now = recent_30['ma20'].iloc[-1]
            ma20_prev = recent_30['ma20'].iloc[-5] # 5天前
            
            # 趋势判定：价格在20日线下且20日线向下
            is_downward = ma20_now < ma20_prev
            is_below_ma = curr_p < ma20_now
            period_ret = (curr_p / recent_30['close'].iloc[0] - 1) * 100
            
            print(f"   >>> 当前指数: {curr_p:.2f} | 20日均线: {ma20_now:.2f}")
            print(f"   >>> 近30日涨跌幅: {period_ret:.2f}% | 区间波幅: {((recent_30['high'].max()/recent_30['low'].min()-1)*100):.2f}%")

            decision = "🚀 可以买入 (趋势向好或处于反弹区间)"
            is_stop = False

            if is_below_ma and is_downward:
                decision = "⛔ 停止买入 (中期趋势走弱，建议空仓)"
                is_stop = True
            elif period_ret < -5:
                decision = "⚠️ 停止买入 (短期超跌严重，风险未释放)"
                is_stop = True
            
            print("\n" + "═"*60)
            print(f"📢 大盘风控决策：【 {decision} 】")
            print("═"*60 + "\n")
            return decision, is_stop
        except: return "可以买入", False

    def _get_feedback_str(self):
        """对比历史选股记录与当前市价，生成反馈字符串"""
        if not os.path.exists(self.hist_path): return "暂无历史记录"
        try:
            # 读取最近10条历史记录
            df = pd.read_csv(self.hist_path, names=['code','name','score','price'], header=None).tail(10)
            df['code'] = df['code'].astype(str).str.zfill(6)
            
            # 获取实时行情对比
            current_spot = ak.stock_zh_a_spot_em()
            fb_list = []
            for _, r in df.iterrows():
                row = current_spot[current_spot['代码'] == r['code']]
                if not row.empty:
                    now_p = float(row.iloc[0]['最新价'])
                    profit = (now_p / float(r['price']) - 1) * 100
                    fb_list.append(f"{r['name']}:{profit:.1f}%")
            return " | ".join(fb_list) if fb_list else "等待行情验证"
        except: return "复盘分析中..."

    def run(self):
        print(f"\n🚀 [AI 进化选股引擎 V2.5] 启动：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 大盘风控
        market_decision, stop_flag = self.check_market_risk()
        
        # 2. 【核心补全】近期表现复盘与权重动态进化
        feedback_str = self._get_feedback_str()
        print(f"📊 近期表现：{feedback_str}")
        
        # 调用 LLM 进行权重微调
        evolution_res = self.llm.evolve_strategy(feedback_str, self.weights)
        if evolution_res and isinstance(evolution_res, dict):
            print(f"📈 权重自动优化详情：")
            print(json.dumps(evolution_res, indent=4, ensure_ascii=False))
            # 提取新权重
            new_w = evolution_res.get("新权重", evolution_res)
            self.weights = {k: v for k, v in new_w.items() if isinstance(v, (int, float))}
        
        # 3. AI 获取今日初筛标准
        ai_keywords, ai_shape = self.llm.get_market_selection_criteria()
        print(f"💡 AI 今日审美：关键词({','.join(ai_keywords)}) | 形态({ai_shape})")

        # 4. 全市场 1000 只活跃股扫描 (不剔除板块)
        print(f"🔍 正在执行全市场前 1000 只活跃股扫描 (含主板/创业/科创)...")
        spot_df = ak.stock_zh_a_spot_em()
        spot_df = spot_df[~spot_df['名称'].str.contains('ST|退')]
        
        # 按成交额排序选前 1000 名
        spot_df = spot_df.sort_values(by='成交额', ascending=False).head(1000)

        full_pool = []
        for _, row in spot_df.iterrows():
            code = str(row['代码']).zfill(6)
            tsg = TradingSignalGenerator(code) 
            tsg.fetch_stock_data()
            inds = tsg.get_indicators(name=row['名称'], hot_keywords=ai_keywords)
            if not inds: continue
            
            # 计算动态加权总分
            score = sum(inds.get(k, 0) * (float(v)/100) for k, v in self.weights.items())
            res = tsg.calculate_logic()
            if res:
                res.update({'name': row['名称'], 'code': code, 'score': round(score, 1)})
                full_pool.append(res)

        # 5. 精英池 (1000选300)
        elite_pool = sorted(full_pool, key=lambda x: x['score'], reverse=True)[:300]
        # 为 LLM 准备前 100 只备选列表
        elite_table = "\n".join([f"{c['code']} | {c['name']} | 评分:{c['score']} | 位阶:{c['position_pct']}%" for c in elite_pool[:100]])

        # 6. DeepSeek 终极决策 (300选10)
        print(f"🧠 DeepSeek 正在从 300 只精英股中进行最终决策...")
        final_decisions = self.llm.ai_deep_decision(f"{ai_keywords} - {ai_shape}", elite_table)

        # 7. 打印结果
        print("\n" + "🎯" * 15 + " 今日选股 10 强决策 (1000选300选10) " + "🎯" * 15)
        
        if stop_flag:
            print("\n" + "!"*60)
            print(f"🚨 风险提示：当前大盘判定为【 {market_decision} 】")
            print("🚨 选股结果仅供观察，实盘请务必谨慎或空仓！")
            print("!"*60 + "\n")

        top_count = 0
        for code, reason in final_decisions.items():
            match = next((x for x in elite_pool if str(x['code']) in str(code)), None)
            if match:
                print(f"{top_count+1}. {match['code']} | {match['name']} | 🏆 评分: {match['score']}")
                print(f"   >>> 💡 专家理由: {reason}")
                print(f"   >>> 💰 买入委托价: {match['entrust_buy']} | 止盈目标: {match['target']}")
                print("-" * 80)
                
                # 写入历史记录，用于下一次运行时的复盘对比
                with open(self.hist_path, 'a', newline='') as f:
                    csv.writer(f).writerow([match['code'], match['name'], match['score'], match['price']])
                
                top_count += 1
                if top_count >= 10: break

if __name__ == "__main__":
    AutoStrategyOptimizer().run()
