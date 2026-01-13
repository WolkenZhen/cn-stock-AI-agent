import pandas as pd
import akshare as ak
import os, warnings, csv, json, time
import numpy as np
from datetime import datetime, timedelta
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

    def check_market_risk(self):
        """
        升级版大盘风控：分析上证指数(sh000001)近30个交易日走势
        返回判定结果：'停止买入' 或 '可以买入'
        """
        print(f"📊 正在深度分析大盘基本面趋势 (近30个交易日)...")
        try:
            # 抓取 60 天数据以确保 20/30 日均线计算准确
            df_index = ak.stock_zh_index_daily(symbol="sh000001")
            if df_index.empty: return "无法获取数据", False

            # 计算关键指标
            df_index['ma20'] = df_index['close'].rolling(20).mean()
            df_index['ma30'] = df_index['close'].rolling(30).mean()
            
            recent_30 = df_index.tail(30).copy()
            current_price = recent_30['close'].iloc[-1]
            ma20_now = recent_30['ma20'].iloc[-1]
            ma20_prev = recent_30['ma20'].iloc[-5] # 5天前的均线位置，判断斜率
            
            # 1. 均线趋势判断 (斜率)
            is_ma20_down = ma20_now < ma20_prev
            
            # 2. 价格相对位置
            is_below_ma = current_price < ma20_now
            
            # 3. 近30日波动统计
            start_price = recent_30['close'].iloc[0]
            max_price = recent_30['high'].max()
            min_price = recent_30['low'].min()
            period_return = (current_price / start_price - 1) * 100
            
            print(f"   >>> 当前指数: {current_price:.2f} | 20日均线: {ma20_now:.2f}")
            print(f"   >>> 近30日涨跌幅: {period_return:.2f}% | 区间波幅: {((max_price/min_price-1)*100):.2f}%")

            # 决策逻辑
            decision = "可以买入"
            warning_level = "NORMAL"

            if is_below_ma and is_ma20_down:
                decision = "⛔ 停止买入 (震荡下行趋势显著)"
                warning_level = "DANGER"
            elif period_return < -5:
                decision = "⚠️ 停止买入 (区间跌幅过大，风险未释放)"
                warning_level = "WARNING"
            elif is_below_ma:
                decision = "⚖️ 谨慎买入 (处于20日线下方震荡)"
                warning_level = "CAUTION"
            else:
                decision = "🚀 可以买入 (趋势向好或处于反弹区间)"
                warning_level = "SAFE"

            print("\n" + "═"*60)
            print(f"📢 大盘风控决策：【 {decision} 】")
            print("═"*60 + "\n")
            
            return decision, (warning_level in ["DANGER", "WARNING"])

        except Exception as e:
            print(f"❌ 大盘分析异常: {e}")
            return "可以买入 (数据异常，默认通过)", False

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
        print(f"\n🚀 [AI 进化选股引擎 V2.5] 启动：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 30日大盘基本面风控
        market_decision, stop_flag = self.check_market_risk()
        
        # 2. 复盘与权重进化 (保持原有功能)
        fb_str = self._get_feedback_str()
        full_res = self.llm.evolve_strategy(fb_str, self.weights)
        if full_res and isinstance(full_res, dict):
            raw_w = full_res.get("新权重", full_res)
            self.weights = {k: v for k, v in raw_w.items() if isinstance(v, (int, float))}
        
        # 3. 获取 AI 初筛关键词
        ai_keywords, ai_shape = self.llm.get_market_selection_criteria()
        print(f"💡 AI 今日审美：关键词({','.join(ai_keywords)})")

        # 4. 全市场 1000 只活跃股扫描 (仅限沪深主板)
        print(f"🔍 正在扫描沪深主板前 1000 只活跃股 (已剔除创业板/科创板)...")
        spot_df = ak.stock_zh_a_spot_em()
        spot_df = spot_df[~spot_df['名称'].str.contains('ST|退')]
        
        # 板块过滤逻辑
        spot_df['代码_str'] = spot_df['代码'].astype(str).str.zfill(6)
        # 排除 30 (创业板) 和 688 (科创板)
        spot_df = spot_df[~spot_df['代码_str'].str.startswith(('30', '688'))]
        
        # 按成交额排序取前 1000
        spot_df = spot_df.sort_values(by='成交额', ascending=False).head(1000)

        full_pool = []
        for _, row in spot_df.iterrows():
            code = row['代码_str']
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
        elite_table = "\n".join([f"{c['code']} | {c['name']} | 评分:{c['score']}" for c in elite_pool[:100]])

        # 6. AI 最终决策 10 只
        print(f"🧠 DeepSeek 正在从 300 只沪深主板精英股中裁定 10 强...")
        final_decisions = self.llm.ai_deep_decision(f"{ai_keywords}", elite_table)

        # 7. 打印结果
        print("\n" + "🎯" * 15 + " 今日沪深主板 10 强决策 " + "🎯" * 15)
        
        # 如果判定停止买入，打印醒目的红色警告
        if stop_flag:
            print("\n" + "!"*60)
            print(f"🚨 警告：大盘目前处于【{market_decision}】状态")
            print("🚨 建议：系统虽选出 10 强，但大盘趋势不佳，请务必空仓或极小仓位试错！")
            print("!"*60 + "\n")

        top_count = 0
        for code, reason in final_decisions.items():
            match = next((x for x in elite_pool if str(x['code']) in str(code)), None)
            if match:
                print(f"{top_count+1}. {match['code']} | {match['name']} | 🏆 评分: {match['score']}")
                print(f"   >>> 💡 专家理由: {reason}")
                print(f"   >>> 💰 买入委托参考: {match['entrust_buy']} | 目标: {match['target']}")
                print("-" * 80)
                # 记录到历史
                with open(self.hist_path, 'a', newline='') as f:
                    csv.writer(f).writerow([match['code'], match['name'], match['score'], match['price']])
                top_count += 1
                if top_count >= 10: break

if __name__ == "__main__":
    AutoStrategyOptimizer().run()