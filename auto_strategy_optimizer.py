import pandas as pd
import akshare as ak
import json, os, warnings
from datetime import datetime
from trading_signal import TradingSignalGenerator
from llm_client import FreeLLMClient
from config import *

# 忽略数据处理过程中的警告
warnings.filterwarnings('ignore')

class AutoStrategyOptimizer:
    def __init__(self):
        self.llm = FreeLLMClient()
        # 默认因子权重配置
        self.weights = {"涨幅动能": 35, "成交量放大": 20, "均线多头": 15, "价格弹性": 30}

    def run(self):
        # 补全年月日时间戳
        current_full_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n" + "=="*25 + f" AI 高空间选股系统 [{current_full_time}] " + "=="*25)
        print(f"🎯 策略目标：寻找支撑位稳健且预期收益 > 10% 的高弹性标的")
        
        try:
            # 1. 扫描全市场活跃股票
            df = ak.stock_zh_a_spot_em()
            df = df[~df['名称'].str.contains('ST|退', na=False)]
            df['成交额'] = pd.to_numeric(df['成交额'], errors='coerce') / 1e8
            # 筛选日成交额大于1.5亿的活跃个股，取前150只进行深度诊断
            df = df[df['成交额'] >= 1.5].head(150) 
        except Exception as e:
            print(f"❌ 市场数据抓取失败: {e}")
            return

        scored_list = []
        for _, row in df.iterrows():
            tsg = TradingSignalGenerator(row['代码'])
            tsg.fetch_stock_data()
            inds = tsg.get_indicators()
            
            if not inds: continue
            
            # 计算加权综合评分
            score = sum(inds.get(k, 0) * (self.weights.get(k, 25)/100) for k in self.weights)
            res = tsg.calculate_logic()
            
            # 核心筛选逻辑：预期收益率需接近或超过10%
            if res and res['target_gain'] >= 9.5: 
                res.update({'name': row['名称'], 'code': row['代码'], 'total_score': score})
                scored_list.append(res)

        # 取评分最高的前5名
        top_stocks = sorted(scored_list, key=lambda x: x['total_score'], reverse=True)[:5]

        print("\n" + "—"*40 + " 今日 AI 10% 潜力股空间报告 " + "—"*40)
        
        if not top_stocks:
            print("💡 当前市场波幅较小，未找到符合 10% 预期收益的潜力标的。")
        
        for i, s in enumerate(top_stocks):
            # 格式化输出位阶进度条
            bar_len = int(max(0, min(s['position_pct'], 100)) / 5)
            progress_bar = f"[{'#' * bar_len}{'-' * (20 - bar_len)}]"
            
            print(f"{i+1}. **{s['code']} {s['name']}** [潜力评分: {s['total_score']:.1f}]")
            print(f"   📈 空间位置：支撑 {s['support']} | **最新价 {s['price']}** | 阻力 {s['resistance']}")
            print(f"   📊 当前位阶：{progress_bar} {s['position_pct']}% (越低安全边际越高)")
            print(f"   🎯 盈利预测：目标价 {s['target']} | 预期收益 **+{s['target_gain']}%**")
            print(f"   🛡️ 风险防御：止损价 {s['stop_loss']} | 信号状态：{s['signal']}")
            print(f"   📝 专家点评：{s['advice']}")
            print("-" * 105)

if __name__ == "__main__":
    AutoStrategyOptimizer().run()