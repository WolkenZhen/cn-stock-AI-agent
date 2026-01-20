import pandas as pd
import akshare as ak
import os, warnings, csv, json, time
from datetime import datetime, timedelta
from config import *
from trading_signal import TradingSignalGenerator
from llm_client import FreeLLMClient

warnings.filterwarnings('ignore')

class AutoStrategyOptimizer:
    def __init__(self):
        self.llm = FreeLLMClient()
        if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)
        
        print("⏳ 正在探测今日市场环境 (技术指标+RAG)...")
        self.hot_sectors, self.market_status = self.llm.fetch_market_analysis()
        
        # 核心升级：多周期回测
        self.update_historical_prices()
        self.weights = self._evolve_weights_via_deepseek()

    def update_historical_prices(self):
        """
        深度回测：不仅看次日，还追踪 T+3, T+5 表现
        """
        if not os.path.exists(HIST_PATH): return
        try:
            df = pd.read_csv(HIST_PATH, on_bad_lines='skip')
            updated = False
            today = datetime.now()
            
            # 确保有 T+3, T+5 列
            if 'price_t3' not in df.columns: df['price_t3'] = 0.0
            if 'price_t5' not in df.columns: df['price_t5'] = 0.0
            
            print(f"⏳ 正在深度回溯历史选股表现 (追踪 T+1~T+5 走势)...")
            
            for index, row in df.iterrows():
                # 只处理尚未填满数据的旧记录
                if row['next_day_price'] == 0 or row['price_t3'] == 0:
                    record_date = datetime.strptime(row['date'], "%Y-%m-%d")
                    days_passed = (today - record_date).days
                    
                    if days_passed > 1: # 至少过了一天
                        code = str(row['code']).zfill(6)
                        start_dt = record_date.strftime("%Y%m%d")
                        end_dt = today.strftime("%Y%m%d")
                        
                        try:
                            # 获取区间日线
                            stock_df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_dt, end_date=end_dt, adjust="qfq")
                            
                            # 填补 T+1
                            if len(stock_df) >= 2 and row['next_day_price'] == 0:
                                df.at[index, 'next_day_price'] = stock_df.iloc[1]['收盘']
                                updated = True
                            
                            # 填补 T+3
                            if len(stock_df) >= 4 and row['price_t3'] == 0:
                                df.at[index, 'price_t3'] = stock_df.iloc[3]['收盘']
                                updated = True
                                
                            # 填补 T+5
                            if len(stock_df) >= 6 and row['price_t5'] == 0:
                                df.at[index, 'price_t5'] = stock_df.iloc[5]['收盘']
                                updated = True
                                
                        except: pass
            
            if updated: 
                df.to_csv(HIST_PATH, index=False)
                print("✅ 历史波段数据更新完毕。")
                
        except Exception as e: 
            print(f"⚠️ 历史回测跳过: {e}")

    def _evolve_weights_via_deepseek(self):
        """
        深度进化：基于多周期表现优化权重
        """
        try:
            df = pd.read_csv(HIST_PATH, on_bad_lines='skip')
            # 筛选出至少 T+1 有价格的记录
            valid_df = df[df['next_day_price'] > 0].tail(EVOLUTION_LOOKBACK)
            
            history_summary = ""
            if not valid_df.empty:
                for _, row in valid_df.iterrows():
                    # 计算多周期收益
                    buy = row['buy_price']
                    p1 = row['next_day_price']
                    p3 = row.get('price_t3', 0)
                    
                    ret1 = (p1 - buy) / buy * 100
                    ret3 = (p3 - buy) / buy * 100 if p3 > 0 else 0
                    
                    # 结果标签：不仅看涨跌，还看是否是大牛股(T+3 > 15%)
                    label = "大妖股🚀" if ret3 > 15 else ("波段涨" if ret3 > 5 else ("一日游" if ret1 > 0 and ret3 < 0 else "亏损"))
                    
                    history_summary += f"{row['name']}: {label} | T+1:{ret1:.1f}% T+3:{ret3:.1f}% | 因子:{ {k: row.get(k,0) for k in DEFAULT_WEIGHTS} }\n"
            
            market_ctx = f"热点:{self.hot_sectors}, 状态:{self.market_status}"
            print(f"🧠 DeepSeek 正在进行【Transformer自注意力进化】...")
            print(f"   >>> 目标: 识别能穿越 T+1 到 T+{TARGET_HORIZON} 的波段因子")
            
            # 调用升级版的权重优化接口
            new_weights = self.llm.optimize_weights_deep_evolution(history_summary, DEFAULT_WEIGHTS, market_ctx)
            return new_weights if new_weights else DEFAULT_WEIGHTS
            
        except Exception as e:
            print(f"⚠️ 权重优化降级: {e}")
            return DEFAULT_WEIGHTS

    def run_daily_selection(self):
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"🚀 [AI 深A主板短线进攻引擎] 启动：{today}")
        print(f"📡 大盘操作建议: {self.market_status} | 核心热点: {self.hot_sectors}")
        print(f"⚖️  DeepSeek 进化权重: {self.weights}")
        print("🔍 正在扫描全市场活跃深A主板股 (已启用涨停过滤)...")

        try:
            pool = ak.stock_zh_a_spot_em()
            # 基础池过滤
            main_board = pool[
                (pool['代码'].str.startswith('00')) & 
                (pool['涨跌幅'] < 9.5) & 
                (pool['涨跌幅'] > 2.0) & # 剔除织布机
                (~pool['名称'].str.contains('ST')) &
                (pool['成交额'] > 100000000)
            ].sort_values(by='涨跌幅', ascending=False).head(100) # 扩大扫描范围
        except: return

        candidates = []
        for _, row in main_board.iterrows():
            code = row['代码']
            tsg = TradingSignalGenerator(code)
            tsg.fetch_stock_data()
            factors = tsg.get_indicators()
            
            if factors:
                score_ai, reason_ai, alpha = self.llm.get_ai_expert_factor(row.to_json())
                factors["专家因子"] = score_ai
                
                final_score = sum(factors[k] * self.weights.get(k, 20) / 100 for k in factors)
                
                # 传入当前权重给 logic 计算，以便动态调整止盈位
                prices = tsg.calculate_logic(self.weights) 
                
                candidates.append({
                    'code': code, 'name': row['名称'], 'final_score': round(final_score + alpha, 1),
                    'ai_reason': reason_ai, **factors, **prices
                })
                if len(candidates) >= 15: break

        top_10 = sorted(candidates, key=lambda x: x['final_score'], reverse=True)[:10]

        print("\n" + "🥇" * 15 + " 深A主板进攻 TOP 10 (波段潜力) " + "🥇" * 15)
        for i, s in enumerate(top_10):
            print(f"{i+1}. {s['code']} | {s['name']} | 🏆 总分: {s['final_score']}")
            print(f"   [因子] 量价:{s['量价爆发']} 趋势:{s['趋势强度']} 资金:{s['资金流向']} 专家:{s['专家因子']}")
            print(f"   >>> 💡 AI: {s['ai_reason']}")
            print(f"   >>> 💰 当日委托买入: {s['entrust_buy']} | 📈 T+1委托卖出: {s['entrust_sell_t1']}")
            print(f"   >>> 🛡️ 止损参考: {s['stop_loss']}")
            print("-" * 80)

        # 记录时预留 T+3, T+5 列
        self._log_history(top_10)

    def _log_history(self, top_stocks):
        file_exists = os.path.exists(HIST_PATH)
        # 扩展字段
        fieldnames = ['date', 'code', 'name', 'buy_price', 'next_day_price', 'price_t3', 'price_t5'] + list(DEFAULT_WEIGHTS.keys())
        
        with open(HIST_PATH, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists: writer.writeheader()
            for s in top_stocks:
                row = {
                    'date': datetime.now().strftime("%Y-%m-%d"), 
                    'code': s['code'], 'name': s['name'], 'buy_price': s['price'], 
                    'next_day_price': 0, 'price_t3': 0, 'price_t5': 0 # 初始占位
                }
                for k in DEFAULT_WEIGHTS: row[k] = s.get(k, 0)
                writer.writerow(row)

if __name__ == "__main__":
    optimizer = AutoStrategyOptimizer()
    optimizer.run_daily_selection()