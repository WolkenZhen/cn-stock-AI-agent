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
        # 初始权重，后续由AI根据回馈自动调整
        self.weights = {"趋势": 30, "动能": 20, "成交": 15, "弹性": 15, "专家": 20}
        self.log_dir = "strategy_log"
        self.hist_path = os.path.join(self.log_dir, "selection_history.csv")
        if not os.path.exists(self.log_dir): os.makedirs(self.log_dir)

    def check_market_risk(self):
        """
        深度大盘风控：分析上证指数(sh000001)近30个交易日走势
        返回判定结果及风险标志
        """
        print(f"📊 正在执行大盘基本面深度分析 (过去30个交易日)...")
        try:
            # 抓取足够数据计算均线
            df_index = ak.stock_zh_index_daily(symbol="sh000001")
            if df_index.empty: return "数据获取失败", False

            # 计算关键趋势指标
            df_index['ma20'] = df_index['close'].rolling(20).mean()
            
            recent_30 = df_index.tail(30).copy()
            current_price = recent_30['close'].iloc[-1]
            ma20_now = recent_30['ma20'].iloc[-1]
            ma20_prev = recent_30['ma20'].iloc[-5] # 5天前的20日线位置
            
            # 判定条件
            is_ma20_down = ma20_now < ma20_prev  # 20日线拐头向下
            is_below_ma = current_price < ma20_now # 价格在20日线下方
            
            # 区间涨跌幅
            start_price = recent_30['close'].iloc[0]
            period_return = (current_price / start_price - 1) * 100
            
            print(f"   >>> 上证指数: {current_price:.2f} | 20日线: {ma20_now:.2f}")
            print(f"   >>> 近30日区间涨跌幅: {period_return:.2f}%")

            decision = "可以买入"
            is_stop = False

            if is_below_ma and is_ma20_down:
                decision = "⛔ 停止买入 (趋势严重破位，震荡下行中)"
                is_stop = True
            elif period_return < -5:
                decision = "⚠️ 停止买入 (短期跌幅过大，市场情绪极差)"
                is_stop = True
            elif is_below_ma:
                decision = "⚖️ 谨慎买入 (处于均线下方，建议轻仓)"
            else:
                decision = "🚀 可以买入 (趋势良好或处于企稳区间)"

            print("\n" + "═"*60)
            print(f"📢 大盘风控决策：【 {decision} 】")
            print("═"*60 + "\n")
            
            return decision, is_stop

        except Exception as e:
            print(f"❌ 大盘数据获取异常: {e}")
            return "可以买入 (默认)", False

    def _get_feedback_str(self):
        """获取近期选股的实盘反馈用于AI进化"""
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
            return " | ".join(fb) if fb else "等待行情验证"
        except: return "复盘分析中..."

    def run(self):
        print(f"\n🚀 [AI 进化选股引擎 V2.5 - 全市场版] 启动：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 大盘风控判定
        market_decision, stop_flag = self.check_market_risk()
        
        # 2. 权重自动进化
        fb_str = self._get_feedback_str()
        print(f"📊 历史策略反馈：{fb_str}")
        full_res = self.llm.evolve_strategy(fb_str, self.weights)
        if full_res and isinstance(full_res, dict):
            print(f"📈 因子权重动态优化详情：")
            print(json.dumps(full_res, indent=4, ensure_ascii=False))
            raw_w = full_res.get("新权重", full_res)
            self.weights = {k: v for k, v in raw_w.items() if isinstance(v, (int, float))}
        
        # 3. 获取 AI 初筛指导
        ai_keywords, ai_shape = self.llm.get_market_selection_criteria()
        print(f"💡 AI 今日审美偏好：关键词({','.join(ai_keywords)}) | 技术形态({ai_shape})")

        # 4. 全市场 1000 只活跃股扫描 (包含科创板、创业板)
        print(f"🔍 正在执行全市场(沪深/创业/科创)前 1000 只活跃股扫描...")
        spot_df = ak.stock_zh_a_spot_em()
        # 排除 ST 和 退市股
        spot_df = spot_df[~spot_df['名称'].str.contains('ST|退')]
        
        # 选出成交额前 1000 名的活跃品种
        spot_df = spot_df.sort_values(by='成交额', ascending=False).head(1000)

        full_pool = []
        for _, row in spot_df.iterrows():
            code = str(row['代码']).zfill(6)
            tsg = TradingSignalGenerator(code) 
            tsg.fetch_stock_data()
            inds = tsg.get_indicators(name=row['名称'], hot_keywords=ai_keywords)
            if not inds: continue
            
            # 计算综合量化得分
            score = sum(inds.get(k, 0) * (float(v)/100) for k, v in self.weights.items())
            res = tsg.calculate_logic()
            if res:
                res.update({'name': row['名称'], 'code': code, 'score': round(score, 1)})
                full_pool.append(res)

        # 5. 锁定 300 只精英池 (量化评分最高者)
        elite_pool = sorted(full_pool, key=lambda x: x['score'], reverse=True)[:300]
        # 传送给 AI 决策的压缩表（取前 100 供 AI 精选）
        elite_table = "\n".join([f"{c['code']} | {c['name']} | 评分:{c['score']} | 位阶:{c['position_pct']}%" for c in elite_pool[:100]])

        # 6. DeepSeek 终极裁定 (从300只中选出最强10只)
        print(f"🧠 DeepSeek 正在从 300 只精英池中甄选 10 强决策...")
        final_decisions = self.llm.ai_deep_decision(f"{ai_keywords} - {ai_shape}", elite_table)

        # 7. 打印结果
        print("\n" + "🎯" * 15 + " 今日全市场 10 强个股决策 " + "🎯" * 15)
        
        if stop_flag:
            print("\n" + "!"*60)
            print(f"🚨 风险提示：当前大盘环境被判定为【 {market_decision} 】")
            print("🚨 选股结果仅供观察，实盘请严格控制仓位，避免在震荡下行区间重仓！")
            print("!"*60 + "\n")

        top_count = 0
        for code, reason in final_decisions.items():
            # 兼容性查找
            match = next((x for x in elite_pool if str(x['code']) in str(code)), None)
            if match:
                print(f"{top_count+1}. {match['code']} | {match['name']} | 🏆 综合评分: {match['score']}")
                print(f"   >>> 💡 专家逻辑理由: {reason}")
                print(f"   >>> 💰 今日买入参考价: {match['entrust_buy']}")
                print(f"   🎯 止盈目标: {match['target']} | 止损参考: {match['stop_loss']}")
                print("-" * 80)
                
                # 保存历史记录以便后续进化
                with open(self.hist_path, 'a', newline='') as f:
                    csv.writer(f).writerow([match['code'], match['name'], match['score'], match['price']])
                
                top_count += 1
                if top_count >= 10: break

        if top_count == 0:
            print("⚠️  AI 决策层未返回有效结果，以下是量化评分排名前10的个股供参考：")
            for i, item in enumerate(elite_pool[:10]):
                print(f"{i+1}. {item['code']} | {item['name']} | 评分: {item['score']}")

if __name__ == "__main__":
    AutoStrategyOptimizer().run()
