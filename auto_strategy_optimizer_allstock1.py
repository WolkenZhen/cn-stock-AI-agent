import pandas as pd
import akshare as ak
import os, warnings, csv, json, time
import numpy as np
from datetime import datetime
from trading_signal import TradingSignalGenerator
from llm_client import FreeLLMClient

warnings.filterwarnings('ignore')

class AutoStrategyOptimizer:
    def __init__(self):
        self.llm = FreeLLMClient()
        # 初始因子权重
        self.weights = {"趋势": 30, "动能": 20, "成交": 15, "弹性": 15, "专家": 20}
        self.log_dir = "strategy_log"
        self.hist_path = os.path.join(self.log_dir, "selection_history.csv")
        if not os.path.exists(self.log_dir): os.makedirs(self.log_dir)

    def check_market_risk(self):
        """
        [大盘风控模块] 分析上证指数(sh000001)近30个交易日走势
        判定逻辑：
        - 若现价在20日均线下且均线向下：停止买入
        - 若近30日跌幅超过5%：停止买入
        """
        print(f"📊 正在深度分析大盘基本面趋势 (近30个交易日)...")
        try:
            # 获取上证指数历史数据
            df_index = ak.stock_zh_index_daily(symbol="sh000001")
            if df_index.empty: return "未知状态", False

            # 计算MA20（月线）
            df_index['ma20'] = df_index['close'].rolling(20).mean()
            recent_30 = df_index.tail(30).copy()
            
            curr_p = recent_30['close'].iloc[-1]
            ma20_now = recent_30['ma20'].iloc[-1]
            ma20_prev = recent_30['ma20'].iloc[-5] # 5天前的位置看斜率
            
            # 趋势指标
            is_downward = ma20_now < ma20_prev  # 均线向下
            is_below_ma = curr_p < ma20_now     # 价格在均线下
            
            # 涨跌幅统计
            start_p = recent_30['close'].iloc[0]
            period_ret = (curr_p / start_p - 1) * 100
            
            print(f"   >>> 当前指数: {curr_p:.2f} | 20日均线: {ma20_now:.2f}")
            print(f"   >>> 近30日涨跌幅: {period_ret:.2f}% | 区间波幅: {((recent_30['high'].max()/recent_30['low'].min()-1)*100):.2f}%")

            decision = "🚀 可以买入 (趋势向好或处于反弹区间)"
            is_risky = False

            if is_below_ma and is_downward:
                decision = "⛔ 停止买入 (市场处于震荡下行区间，风险极大)"
                is_risky = True
            elif period_ret < -5:
                decision = "⚠️ 停止买入 (短期跌幅过猛，建议空仓避险)"
                is_risky = True
            elif is_below_ma:
                decision = "⚖️ 谨慎买入 (处于均线下方，建议极小仓位)"
            
            print("\n" + "═"*60)
            print(f"📢 大盘风控决策：【 {decision} 】")
            print("═"*60 + "\n")
            
            return decision, is_risky
        except Exception as e:
            print(f"❌ 大盘分析异常: {e}")
            return "可以买入 (数据异常)", False

    def _get_feedback_str(self):
        """[复盘模块] 获取历史选股表现"""
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
        except: return "复盘分析中..."

    def run(self):
        print(f"\n🚀 [AI 进化选股引擎 V2.5 - 全市场版] 启动：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 大盘风控分析
        market_decision, stop_buy = self.check_market_risk()
        
        # 2. 策略反馈与权重进化
        fb_str = self._get_feedback_str()
        print(f"📊 近期表现：{fb_str}")
        
        full_res = self.llm.evolve_strategy(fb_str, self.weights)
        if full_res and isinstance(full_res, dict):
            print(f"📈 权重自动优化详情：")
            print(json.dumps(full_res, indent=4, ensure_ascii=False))
            raw_w = full_res.get("新权重", full_res)
            self.weights = {k: v for k, v in raw_w.items() if isinstance(v, (int, float))}
        
        # 3. AI 初筛审美获取
        ai_keywords, ai_shape = self.llm.get_market_selection_criteria()
        print(f"💡 AI 今日审美：关键词({','.join(ai_keywords)}) | 形态({ai_shape})")

        # 4. 全市场扫描 (不剔除创业板/科创板)
        print(f"🔍 正在执行全市场(包含主板/创业/科创)前 1000 只活跃股扫描...")
        spot_df = ak.stock_zh_a_spot_em()
        
        # 过滤垃圾股
        spot_df = spot_df[~spot_df['名称'].str.contains('ST|退')]
        
        # 按成交额排序取前 1000（保证流动性）
        spot_df = spot_df.sort_values(by='成交额', ascending=False).head(1000)

        full_pool = []
        for _, row in spot_df.iterrows():
            code = str(row['代码']).zfill(6)
            tsg = TradingSignalGenerator(code) 
            tsg.fetch_stock_data()
            # 获取技术因子
            inds = tsg.get_indicators(name=row['名称'], hot_keywords=ai_keywords)
            if not inds: continue
            
            # 量化评分计算
            score = sum(inds.get(k, 0) * (float(v)/100) for k, v in self.weights.items())
            res = tsg.calculate_logic()
            if res:
                res.update({'name': row['名称'], 'code': code, 'score': round(score, 1)})
                full_pool.append(res)

        # 5. 锁定 300 只精英池
        elite_pool = sorted(full_pool, key=lambda x: x['score'], reverse=True)[:300]
        # 传送压缩后的数据给AI，取前100进行精选
        elite_table = "\n".join([f"{c['code']} | {c['name']} | 评分:{c['score']} | 位阶:{c['position_pct']}%" for c in elite_pool[:100]])

        # 6. DeepSeek 终极裁定 (选出10只)
        print(f"🧠 DeepSeek 正在从 300 只精英股中进行最终决策...")
        final_decisions = self.llm.ai_deep_decision(f"{ai_keywords} - {ai_shape}", elite_table)

        # 7. 打印最终结果
        print("\n" + "🎯" * 15 + " 今日新推个股决策 (1000选300选10) " + "🎯" * 15)
        
        if stop_buy:
            print("\n" + "!"*60)
            print(f"🚨 避险警告：大盘目前处于【 {market_decision} 】")
            print("🚨 此时买入风险极高，以下建议仅作技术研究参考，不建议实盘操作！")
            print("!"*60 + "\n")

        top_count = 0
        for code, reason in final_decisions.items():
            # 兼容性匹配代码
            match = next((x for x in elite_pool if str(x['code']) in str(code)), None)
            if match:
                print(f"{top_count+1}. {match['code']} | {match['name']} | 🏆 评分: {match['score']}")
                print(f"   >>> 💡 专家理由: {reason}")
                print(f"   >>> 💰 买入参考价: {match['entrust_buy']} | 目标: {match['target']}")
                print("-" * 80)
                
                # 记录到历史记录（供下次动态调整权重）
                with open(self.hist_path, 'a', newline='') as f:
                    csv.writer(f).writerow([match['code'], match['name'], match['score'], match['price']])
                
                top_count += 1
                if top_count >= 10: break

if __name__ == "__main__":
    AutoStrategyOptimizer().run()
