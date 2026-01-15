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
        # 初始权重
        self.weights = {"趋势": 30, "动能": 20, "成交": 15, "弹性": 15, "专家": 20}
        self.log_dir = "strategy_log"
        self.hist_path = os.path.join(self.log_dir, "selection_history.csv")
        if not os.path.exists(self.log_dir): os.makedirs(self.log_dir)

    def get_market_sentiment(self):
        """[大盘引力引擎] 计算市场情绪系数，跌势减分，涨势加分"""
        print(f"📡 正在探测全市场情绪引力 (上证指数)...")
        try:
            df = ak.stock_zh_index_daily(symbol="sh000001")
            recent = df.tail(20).copy()
            ma20 = recent['close'].mean()
            current_p = recent['close'].iloc[-1]
            
            # 判断最近3日是否连跌
            last_3_days = recent['close'].tail(3).tolist()
            is_dropping = all(last_3_days[i] < last_3_days[i-1] for i in range(1, len(last_3_days)))
            
            # 基础情绪系数
            base_factor = 1.1 if current_p > ma20 else 0.8
            if is_dropping: base_factor *= 0.8  # 连跌惩罚更重
            
            status = "📉 市场低迷 (建议谨慎)" if base_factor < 1.0 else "🚀 市场活跃"
            print(f"   >>> 当前大盘状态: {status} | 评分调节系数: {base_factor:.2f}")
            return base_factor
        except: return 1.0

    def calculate_three_day_high(self, match_data, final_score):
        """三日高点预测：现价 + (波动率 * 评分溢价)"""
        price = match_data['price']
        atr = match_data.get('atr', price * 0.04) # 创业板/科创板默认波动率设高一点
        # 评分溢价：分越高，预期冲高力度越大
        premium = 1 + (final_score / 1200)
        pred_high = max(match_data.get('resistance', price * 1.05), price + (atr * 2.0 * premium))
        return round(pred_high, 2)

    def run(self):
        print(f"\n🚀 [AI 全市场深度挖掘引擎 V3.1] 启动：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📌 本版本包含：主板、创业板、科创板")

        # 1. 环境感知
        market_factor = self.get_market_sentiment()
        
        # 2. AI 获取审美
        ai_keywords, ai_shape = self.llm.get_market_selection_criteria()
        print(f"💡 AI 今日审美：关键词({','.join(ai_keywords)}) | 形态({ai_shape})")

        # 3. 扫描全市场前 1000 活跃股 (不排除任何板块)
        print(f"🔍 正在深度扫描全市场成交额前 1000 的个股...")
        spot_df = ak.stock_zh_a_spot_em()
        spot_df['code_str'] = spot_df['代码'].astype(str).str.zfill(6)
        
        # 取成交额前 1000 (通常包含大量 300 和 688)
        active_stocks = spot_df.sort_values(by='成交额', ascending=False).head(1000)

        full_pool = []
        for _, row in active_stocks.iterrows():
            code = row['code_str']
            tsg = TradingSignalGenerator(code)
            tsg.fetch_stock_data()
            inds = tsg.get_indicators(name=row['名称'], hot_keywords=ai_keywords)
            if not inds: continue
            
            # 计算量化基础分
            raw_score = sum(inds.get(k, 0) * (float(v)/100) for k, v in self.weights.items())
            # 应用市场系数 (跌势中整体分值会下降)
            adjusted_score = round(raw_score * market_factor, 1)
            
            res = tsg.calculate_logic()
            if res:
                res.update({'name': row['名称'], 'code': code, 'score': adjusted_score})
                full_pool.append(res)

        # 4. 取量化前 60 名进入 DeepSeek 深度评审
        elite_pool = sorted(full_pool, key=lambda x: x['score'], reverse=True)[:60]
        elite_table = "\n".join([f"{c['code']} | {c['name']} | 量化分:{c['score']}" for c in elite_pool])

        # 5. DeepSeek 终极裁定与 AI 二次评分 (Alpha挖掘)
        print(f"🧠 DeepSeek 正在评估 {len(elite_pool)} 只精英股并挖掘 Alpha 收益...")
        ai_results = self.llm.ai_deep_mining(f"{ai_keywords} - {ai_shape}", elite_table)

        # 6. 整合总分并排序
        final_list = []
        for item in elite_pool:
            code = item['code']
            # 基础分 + AI 附加分 (DeepSeek 会根据逻辑给符合审美个股加分)
            ai_info = ai_results.get(code) or ai_results.get(str(code))
            if ai_info:
                item['ai_reason'] = ai_info['reason']
                item['final_score'] = round(item['score'] + ai_info.get('alpha_score', 0), 1)
                final_list.append(item)

        # 严格按最终总分降序排列
        final_list = sorted(final_list, key=lambda x: x['final_score'], reverse=True)[:10]

        # 7. 打印结果
        print("\n" + "🏆" * 15 + " 全市场深度挖掘 TOP 10 (由高到低) " + "🏆" * 15)
        
        if market_factor < 1.0:
            print(f"⚠️  [风控提醒] 大盘趋势较弱，量化分已整体下调。当前榜首个股即便评分高，也需提防系统性回撤。")

        for i, match in enumerate(final_list):
            three_day_high = self.calculate_three_day_high(match, match['final_score'])
            
            # 标注所属板块
            board = "主板"
            if match['code'].startswith('30'): board = "创业板"
            elif match['code'].startswith('688'): board = "科创板"
            
            print(f"{i+1}. {match['code']} ({board}) | {match['name']} | 🏆 总评分: {match['final_score']}")
            print(f"   >>> 💡 深度逻辑: {match['ai_reason']}")
            print(f"   >>> 💰 当日建议买入委托价: {match['entrust_buy']}")
            print(f"   >>> 📈 三日委托卖出价: {three_day_high} (预期高抛)")
            print(f"   >>> 🎯 止盈参考: {match['target']} | 止损参考: {match['stop_loss']}")
            print("-" * 85)
            
            # 历史记录
            with open(self.hist_path, 'a', newline='') as f:
                csv.writer(f).writerow([match['code'], match['name'], match['final_score'], match['price']])

if __name__ == "__main__":
    AutoStrategyOptimizer().run()