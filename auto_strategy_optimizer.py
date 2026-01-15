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

    def get_market_sentiment(self):
        """
        [大盘引力引擎] 计算市场情绪系数
        逻辑：跌势中系数 < 1.0 (压制评分)，涨势中系数 > 1.0 (增强评分)
        """
        print(f"📡 正在探测大盘引力场 (上证指数)...")
        try:
            df = ak.stock_zh_index_daily(symbol="sh000001")
            recent = df.tail(20).copy()
            ma20 = recent['close'].mean()
            current_p = recent['close'].iloc[-1]
            
            # 计算连跌天数
            last_3_days = recent['close'].tail(3).tolist()
            is_dropping = all(last_3_days[i] < last_3_days[i-1] for i in range(1, len(last_3_days)))
            
            # 基础系数：现价在20日线上方为1.1，下方为0.8
            base_factor = 1.1 if current_p > ma20 else 0.8
            # 连跌惩罚
            if is_dropping: base_factor *= 0.85 
            
            status = "📉 市场低迷" if base_factor < 1.0 else "🚀 市场活跃"
            print(f"   >>> 当前大盘状态: {status} | 评分系数: {base_factor:.2f}")
            return base_factor
        except: return 1.0

    def calculate_three_day_high(self, match_data, score):
        """三日委托卖出价算法 (基于ATR与动态评分)"""
        price = match_data['price']
        atr = match_data.get('atr', price * 0.03)
        # 评分越高，预测冲高溢价越高
        score_multiplier = 1 + (score / 1500) 
        pred_high = max(match_data.get('resistance', price * 1.05), price + (atr * 1.8 * score_multiplier))
        return round(pred_high, 2)

    def run(self):
        print(f"\n🚀 [AI 深度挖掘量化引擎 V3.0] 启动：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 获取市场情绪系数
        market_factor = self.get_market_sentiment()
        
        # 2. AI 获取今日审美
        ai_keywords, ai_shape = self.llm.get_market_selection_criteria()
        
        # 3. 扫描主板 1000 活跃股
        print(f"🔍 正在深度挖掘 1000 只主板活跃股 (过滤创业/科创)...")
        spot_df = ak.stock_zh_a_spot_em()
        spot_df['code_str'] = spot_df['代码'].astype(str).str.zfill(6)
        # 仅限沪深主板
        main_df = spot_df[~spot_df['code_str'].str.startswith(('30', '688', '43', '83', '87', '92'))]
        active_stocks = main_df.sort_values(by='成交额', ascending=False).head(1000)

        full_pool = []
        for _, row in active_stocks.iterrows():
            code = row['code_str']
            tsg = TradingSignalGenerator(code)
            tsg.fetch_stock_data()
            inds = tsg.get_indicators(name=row['名称'], hot_keywords=ai_keywords)
            if not inds: continue
            
            # 计算量化基础分
            raw_score = sum(inds.get(k, 0) * (float(v)/100) for k, v in self.weights.items())
            # 应用市场系数：如果是跌势，评分会大幅缩水
            adjusted_score = round(raw_score * market_factor, 1)
            
            res = tsg.calculate_logic()
            if res:
                res.update({'name': row['名称'], 'code': code, 'score': adjusted_score})
                full_pool.append(res)

        # 4. 取前 50 名进入 DeepSeek 深度深度评审 (增加挖掘深度)
        elite_pool = sorted(full_pool, key=lambda x: x['score'], reverse=True)[:50]
        elite_table = "\n".join([f"{c['code']} | {c['name']} | 量化分:{c['score']}" for c in elite_pool])

        # 5. DeepSeek 终极裁定与 AI 二次评分
        print(f"🧠 DeepSeek 正在对前 50 名进行二次评分与逻辑挖掘...")
        ai_results = self.llm.ai_deep_mining(f"{ai_keywords} - {ai_shape}", elite_table)

        # 6. 整合并最终排序
        final_list = []
        for item in elite_pool:
            code = item['code']
            if code in ai_results:
                # 最终总分 = 量化分 + AI 逻辑分
                item['ai_reason'] = ai_results[code]['reason']
                item['final_score'] = item['score'] + ai_results[code].get('alpha_score', 0)
                final_list.append(item)

        # 严格降序排列
        final_list = sorted(final_list, key=lambda x: x['final_score'], reverse=True)[:10]

        # 7. 打印结果
        print("\n" + "🥇" * 15 + " 深度量化挖掘 TOP 10 (按综合评分降序) " + "🥇" * 15)
        
        if market_factor < 1.0:
            print(f"\n⚠️ 风险警示：当前市场环境弱，整体评分已按 {market_factor:.2f} 系数下调，建议轻仓或观望。")

        for i, match in enumerate(final_list):
            three_day_high = self.calculate_three_day_high(match, match['final_score'])
            print(f"{i+1}. {match['code']} | {match['name']} | 🏆 综合评分: {match['final_score']}")
            print(f"   >>> 💡 DeepSeek挖掘逻辑: {match['ai_reason']}")
            print(f"   >>> 💰 当日建议买入委托价: {match['entrust_buy']}")
            print(f"   >>> 📈 三日委托卖出价: {three_day_high} (预测冲高点)")
            print(f"   >>> 🎯 止盈目标: {match['target']} | 止损参考: {match['stop_loss']}")
            print("-" * 85)
            
            # 记录
            with open(self.hist_path, 'a', newline='') as f:
                csv.writer(f).writerow([match['code'], match['name'], match['final_score'], match['price']])

if __name__ == "__main__":
    AutoStrategyOptimizer().run()