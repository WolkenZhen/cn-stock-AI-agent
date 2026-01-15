import pandas as pd
import akshare as ak
import numpy as np
from datetime import datetime, timedelta

class TradingSignalGenerator:
    def __init__(self, stock_code: str):
        self.stock_code = stock_code
        self.stock_data = None

    def fetch_stock_data(self):
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=160)).strftime("%Y%m%d")
        try:
            symbol = str(self.stock_code).zfill(6)
            self.stock_data = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start, end_date=end, adjust="qfq")
        except: self.stock_data = None

    def get_indicators(self, name="", hot_keywords=[]):
        """计算核心量化指标"""
        if self.stock_data is None or len(self.stock_data) < 60: return {}
        df = self.stock_data
        curr = df['收盘'].iloc[-1]
        
        # 1. 趋势得分 (MA20, MA60)
        ma20 = df['收盘'].rolling(20).mean().iloc[-1]
        ma60 = df['收盘'].rolling(60).mean().iloc[-1]
        trend = 100 if curr > ma20 and curr > ma60 else (50 if curr > ma20 else 10)
        
        # 2. 动能得分 (近20日涨跌)
        momentum = (curr / df['收盘'].iloc[-20] - 1) * 100
        
        # 3. 成交量得分 (量比)
        vol_ratio = df['成交量'].iloc[-1] / df['成交量'].tail(10).mean()
        
        # 4. 弹性 (波动率)
        amplitude = ((df['最高'] - df['最低']) / df['收盘'].shift(1)).tail(5).mean() * 100
        
        # 5. 专家分 (关键词匹配)
        expert = 100 if any(k in str(name) for k in hot_keywords) else 0
        
        return {
            "趋势": trend, 
            "动能": round(max(0, momentum * 5), 1), 
            "成交": round(vol_ratio * 15, 1), 
            "弹性": round(amplitude * 10, 1), 
            "专家": expert
        }

    def calculate_logic(self):
        """计算交易核心价位"""
        if self.stock_data is None or self.stock_data.empty: return None
        df = self.stock_data
        price = df['收盘'].iloc[-1]
        
        # ATR 波动率
        high_low = df['最高'] - df['最低']
        atr = high_low.tail(14).mean()
        
        # 支撑位与压力位
        support = round(df['最低'].tail(10).min(), 2)
        resistance = round(df['最高'].tail(10).max(), 2)
        
        return {
            'price': price,
            'atr': atr,
            'resistance': resistance,
            'entrust_buy': round(price * 0.985, 2), # 建议在现价下方1.5%处挂单
            'target': round(price + (atr * 1.5), 2),
            'stop_loss': round(price - (atr * 1.2), 2)
        }