import pandas as pd
import akshare as ak
import numpy as np
from datetime import datetime, timedelta

class TradingSignalGenerator:
    def __init__(self, stock_code: str):
        self.stock_code = stock_code
        self.stock_data = None
        self.industry = ""

    def fetch_stock_data(self):
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=160)).strftime("%Y%m%d")
        try:
            symbol = self.stock_code.replace("sh", "").replace("sz", "")
            # 获取历史数据
            self.stock_data = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start, end_date=end, adjust="qfq")
        except: self.stock_data = None

    def get_indicators(self, name="", hot_keywords=[]):
        """
        新增 hot_keywords: LLM 提取的今日热点关键词
        """
        if self.stock_data is None or len(self.stock_data) < 65: return {}
        df = self.stock_data
        curr = df['收盘'].iloc[-1]
        ma20 = df['收盘'].rolling(20).mean().iloc[-1]
        ma60 = df['收盘'].rolling(60).mean().iloc[-1]
        
        # 1. 趋势评分
        is_uptrend = (curr > ma60) and (curr > ma20)
        trend_score = 100 if is_uptrend else 20
        
        # 2. 动能评分
        momentum = (df['收盘'].iloc[-1] / df['收盘'].iloc[-20] - 1) * 100
        
        # 3. 成交评分
        vol_ratio = df['成交量'].iloc[-1] / df['成交量'].tail(10).mean()
        
        # 4. 弹性评分
        amplitude = ((df['最高'] - df['最低']) / df['收盘'].shift(1)).tail(5).mean() * 100

        # 5. 【新增】专家因子评分 (基于关键词匹配)
        expert_score = 0
        for kw in hot_keywords:
            if kw in name: # 匹配股票名称（如“中际旭创”含“创”或根据行业匹配）
                expert_score = 100
                break
        
        return {
            "趋势": trend_score, 
            "动能": round(max(0, momentum * 5), 1), 
            "成交": round(vol_ratio * 15, 1), 
            "弹性": round(amplitude * 10, 1),
            "专家": expert_score
        }

    def calculate_logic(self):
        if self.stock_data is None or self.stock_data.empty: return None
        df = self.stock_data
        price = df['收盘'].iloc[-1]
        support = round(df['最低'].tail(20).min(), 2)
        target_gain = round(((df['最高'] - df['最低']) / df['最低']).tail(10).mean() * 6 * 100, 2)
        
        # 计算位阶
        low, high = df['最低'].tail(60).min(), df['最高'].tail(60).max()
        pos_pct = round((price - low) / (high - low) * 100, 1) if high != low else 50

        return {
            "price": price, "support": support, "position_pct": pos_pct,
            "target": round(price * (1 + target_gain/100), 2),
            "target_gain": target_gain, "stop_loss": round(price * 0.92, 2)
        }