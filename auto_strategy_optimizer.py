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
        # 初始权重，后续由AI动态微调
        self.weights = {"趋势": 30, "动能": 20, "成交": 15, "弹性": 15, "专家": 20}
        self.log_dir = "strategy_log"
        self.hist_path = os.path.join(self.log_dir, "selection_history.csv")
        if not os.path.exists(self.log_dir): os.makedirs(self.log_dir)

    def check_market_risk(self):
        """[大盘风控] 分析上证指数近30个交易日趋势"""
        print(f"📊 正在深度分析大盘基本面趋势 (近30个交易日)...")
        try:
            df_index = ak.stock_zh_index_daily(symbol="sh000001")
            if df_index.empty: return "未知", False
            
            df_index['ma20'] = df_index['close'].rolling(20).mean()
            recent_30 = df_index.tail(30).copy()
            curr_p = recent_30['close'].iloc[-1]
            ma20_now = recent_30['ma20'].iloc[-1]
            ma20_prev = recent_30['ma20'].iloc[-5] 
            
            is_downward = ma20_now < ma20_prev
            is_below_ma = curr_p < ma20_now
            period_ret = (curr_p / recent_30['close'].iloc[0] - 1) * 100
            
            print(f"   >>> 当前指数: {curr_p:.2f} | 20日均线: {ma20_now:.2f}")
            print(f"   >>> 近30日涨跌幅: {period_ret:.2f}%")

            decision = "🚀 可以买入 (主板趋势稳健)"
            stop_flag = False
            if is_below_ma and is_downward:
                decision = "⛔ 停止买入 (主板趋势走弱)"
                stop_flag = True
            
            print("\n" + "═"*60)
            print(f"📢 大盘风控决策：【 {decision} 】")
            print("═"*60 + "\n")
            return decision, stop_flag
        except: return "可以买入", False

    def _get_feedback_str(self):
        """[复盘模块] 对比历史选股与当前表现"""
        if not os.path.exists(self.hist_path): return "暂无历史记录"
        try:
            df = pd.read_csv(self.hist_path, names=['code','name','score','price'], header=None).tail(10)
            df['code'] = df['code'].astype(str).str.zfill(6)
            current_spot = ak.stock_zh_a_spot_em()
            fb_list = []
            for _, r in df.iterrows():
                row = current_spot[current_spot['代码'] == r['code']]
                if not row.empty:
                    now_p = float(row.iloc[0]['最新价'])
                    profit = (now_p / float(r['price']) - 1) * 100
                    fb_list.append(f"{r['name']}:{profit:.1f}%")
            return " | ".join(fb_list)
        except: return "数据计算中..."

    def calculate_three_day_high(self, match_data):
        """
        [预测算法] 计算买入后三日内可能卖出的最高价格
        算法逻辑：现价 + (1.5 * ATR * (1 + 评分/1000))
        """
        price = match_data['price']
        atr = match_data.get('atr', price * 0.03)  # 默认波动率3%
        score = match_data.get('score', 100)
        resistance = match_data.get('resistance', price * 1.05)
        
        # 评分溢价系数：每高出100分，增加5%的波动预期空间
        premium = 1 + (score / 1000)
        
        # 计算预测高点：以阻力位和ATR扩张位中的较高者为基准，乘以溢价
        pred_high = max(resistance, price + (atr * 1.8 * premium))
        return round(pred_high, 2)

    def run(self):
        print(f"\n🚀 [AI 进化选股引擎 V2.6] 启动：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 大盘风控
        market_decision, stop_flag = self.check_market_risk()
        
        # 2. 复盘与权重动态调整
        fb_str = self._get_feedback_str()
        print(f"📊 近期历史表现：{fb_str}")
        
        evolution = self.llm.evolve_strategy(fb_str, self.weights)
        if evolution and isinstance(evolution, dict):
            print(f"📈 因子权重自动优化详情：")
            print(json.dumps(evolution, indent=4, ensure_ascii=False))
            new_w = evolution.get("新权重", self.weights)
            self.weights = {k: v for k, v in new_w.items() if isinstance(v, (int, float))}

        # 3. AI 获取今日审美
        ai_keywords, ai_shape = self.llm.get_market_selection_criteria()
        print(f"💡 AI 今日审美：关键词({','.join(ai_keywords)}) | 形态({ai_shape})")

        # 4. 扫描并剔除指定板块
        print(f"🔍 正在从 1000 只活跃股中剔除创业板/科创板...")
        spot_df = ak.stock_zh_a_spot_em()
        spot_df['code_str'] = spot_df['代码'].astype(str).str.zfill(6)
        
        # 核心过滤逻辑：剔除 300/301 (创业板) 和 688 (科创板)
        main_df = spot_df[~spot_df['code_str'].str.startswith(('30', '688'))]
        active_stocks = main_df.sort_values(by='成交额', ascending=False).head(1000)

        full_pool = []
        for _, row in active_stocks.iterrows():
            code = row['code_str']
            tsg = TradingSignalGenerator(code)
            tsg.fetch_stock_data()
            inds = tsg.get_indicators(name=row['名称'], hot_keywords=ai_keywords)
            if not inds: continue
            
            score = sum(inds.get(k, 0) * (float(v)/100) for k, v in self.weights.items())
            res = tsg.calculate_logic()
            if res:
                res.update({'name': row['名称'], 'code': code, 'score': round(score, 1)})
                full_pool.append(res)

        # 5. 精英筛选
        elite_pool = sorted(full_pool, key=lambda x: x['score'], reverse=True)[:300]
        elite_table = "\n".join([f"{c['code']} | {c['name']} | 评分:{c['score']}" for c in elite_pool[:100]])

        # 6. DeepSeek 终极决策
        print(f"🧠 DeepSeek 正在进行深度价值裁定与三日预测...")
        final_decisions = self.llm.ai_deep_decision(f"{ai_keywords} - {ai_shape}", elite_table)

        # 7. 打印结果
        print("\n" + "🎯" * 15 + " 今日沪深主板 10 强决策 " + "🎯" * 15)
        
        top_count = 0
        for code, reason in final_decisions.items():
            match = next((x for x in elite_pool if str(x['code']) in str(code)), None)
            if match:
                # 计算三日委托卖出价
                three_day_high = self.calculate_three_day_high(match)
                
                print(f"{top_count+1}. {match['code']} | {match['name']} | 🏆 评分: {match['score']}")
                print(f"   >>> 💡 专家理由: {reason}")
                print(f"   >>> 💰 当日建议买入委托价: {match['entrust_buy']}")
                print(f"   >>> 📈 三日委托卖出价: {three_day_high} (预测高抛点)")
                print(f"   >>> 🎯 止盈目标: {match['target']} | 止损参考: {match['stop_loss']}")
                print("-" * 80)
                
                # 记录到日志，供下次运行复盘
                with open(self.hist_path, 'a', newline='') as f:
                    csv.writer(f).writerow([match['code'], match['name'], match['score'], match['price']])
                
                top_count += 1
                if top_count >= 10: break

if __name__ == "__main__":
    AutoStrategyOptimizer().run()