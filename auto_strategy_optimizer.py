import pandas as pd
import akshare as ak
import json, os, warnings, time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from trading_signal import TradingSignalGenerator
from llm_client import FreeLLMClient
from config import *

warnings.filterwarnings('ignore')

class AutoStrategyOptimizer:
    def __init__(self):
        self.llm = FreeLLMClient()
        self.weights = self._load_weights()

    def _load_weights(self):
        if os.path.exists(WEIGHTS_PATH):
            try:
                with open(WEIGHTS_PATH, 'r') as f: return json.load(f)
            except: pass
        return DEFAULT_WEIGHTS

    def _save_weights(self, weights):
        with open(WEIGHTS_PATH, 'w') as f: json.dump(weights, f, indent=2)

    def track_and_evolve(self):
        """跟踪历史表现并进化策略"""
        if not os.path.exists(HISTORY_PATH):
            print("ℹ️  首次运行，尚无历史数据可跟踪。")
            return

        try:
            history_df = pd.read_csv(HISTORY_PATH)
            last_date = history_df['日期'].max()
            last_picks = history_df[history_df['日期'] == last_date]
            
            perf_list = []
            for _, s in last_picks.iterrows():
                tsg = TradingSignalGenerator(s['代码'])
                tsg.fetch_stock_data()
                if tsg.latest_price > 0:
                    chg = round((tsg.latest_price / s['推荐价'] - 1) * 100, 2)
                    perf_list.append(f"{s['名称']}: 推荐价{s['推荐价']}->现价{tsg.latest_price} ({chg}%)")
            
            if perf_list:
                report = "\n".join(perf_list)
                print(f"📊 历史表现反馈：\n{report}")
                new_w = self.llm.evolve_strategy(report, self.weights)
                if new_w != self.weights:
                    print(f"💡 AI 策略进化！权重更新：{new_w}")
                    self.weights = new_w
                    self._save_weights(new_w)
        except Exception as e:
            print(f"⚠️ 历史跟踪失败: {e}")

    def fetch_market_with_retry(self, retries=3):
        """修复 JSONDecodeError：增加 API 重试逻辑"""
        for i in range(retries):
            try:
                df = ak.stock_zh_a_spot_em()
                if df is not None and not df.empty: return df
            except Exception as e:
                print(f"🔄 数据接口请求中 (尝试 {i+1}/{retries})...")
                time.sleep(2)
        return None

    def worker(self, row):
        try:
            tsg = TradingSignalGenerator(row['代码'])
            tsg.fetch_stock_data()
            inds = tsg.get_indicators()
            if not inds: return None
            score = sum(inds.get(k, 0) * (self.weights.get(k, 25)/100) for k in self.weights)
            res = tsg.calculate_logic()
            if res:
                res.update({'name': row['名称'], 'code': row['代码'], 'total_score': round(score, 1)})
                return res
        except: return None

    def run(self):
        # 1. 策略进化
        self.track_and_evolve()
        
        print(f"\n🚀 [AI 进化选股引擎] 启动：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 2. 抓取市场活跃数据
        df = self.fetch_market_with_retry()
        if df is None:
            print("❌ 无法连接到行情服务器，请检查网络或稍后再试。")
            return
            
        df = df[~df['名称'].str.contains('ST|退', na=False)]
        df['成交额'] = pd.to_numeric(df['成交额'], errors='coerce') / 1e8
        df = df.sort_values(by='成交额', ascending=False).head(SCAN_POOL_SIZE)

        # 3. 多线程诊断
        all_results = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(self.worker, row) for _, row in df.iterrows()]
            for f in as_completed(futures):
                res = f.result()
                if res: all_results.append(res)

        # 4. 量化初筛 -> AI 最终决策
        candidates = sorted(all_results, key=lambda x: x['total_score'], reverse=True)[:TOP_CANDIDATES]
        if not candidates:
            print("💡 未能找到符合条件的候选股。")
            return

        final_indices = self.llm.ai_final_selection(candidates)
        top_5 = [candidates[i] for i in final_indices if i < len(candidates)]

        # 5. 输出报告并持久化
        new_picks = []
        print("\n" + "★"*40 + " AI 深度决策选股报告 (TOP 5) " + "★"*40)
        for i, s in enumerate(top_5):
            bar = f"[{'#' * int(s['position_pct']/5)}{'-' * (20 - int(s['position_pct']/5))}]"
            print(f"{i+1}. {s['code']} {s['name']} | 得分:{s['total_score']} | 现价:{s['price']} | 预期:+{s['target_gain']}%")
            print(f"   位阶：{bar} {s['position_pct']}% | 支撑:{s['support']} | 阻力:{s['resistance']}")
            new_picks.append({"日期": datetime.now().strftime("%Y-%m-%d"), "代码": s['code'], "名称": s['name'], "推荐价": s['price']})
        print("-" * 100)

        # 保存结果用于明日跟踪
        new_df = pd.DataFrame(new_picks)
        if os.path.exists(HISTORY_PATH):
            new_df.to_csv(HISTORY_PATH, mode='a', header=False, index=False)
        else:
            new_df.to_csv(HISTORY_PATH, index=False)

if __name__ == "__main__":
    AutoStrategyOptimizer().run()