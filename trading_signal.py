import pandas as pd
import akshare as ak
import numpy as np
from datetime import datetime, timedelta

class TradingSignalGenerator:
    def __init__(self, stock_code: str): # 确保这里接收 stock_code
        self.stock_code = stock_code
        self.stock_data = None

    def fetch_stock_data(self):
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=100)).strftime("%Y%m%d")
        try:
            symbol = self.stock_code.replace("sh", "").replace("sz", "")
            self.stock_data = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start, end_date=end, adjust="qfq")
        except: self.stock_data = None

    def get_indicators(self):
        if self.stock_data is None or len(self.stock_data) < 20: return {}
        df = self.stock_data
        # 1. 动能：近期涨幅
        momentum = (df['收盘'].iloc[-1] / df['收盘'].iloc[-10] - 1) * 100
        # 2. 成交量：对比均量
        vol_ratio = df['成交量'].iloc[-1] / df['成交量'].tail(10).mean()
        # 3. 弹性：基于振幅
        amplitude = ((df['最高'] - df['最低']) / df['收盘'].shift(1)).tail(5).mean() * 100
        
        return {"涨幅动能": momentum, "成交量放大": vol_ratio * 20, "空间弹性": amplitude * 10}

    def calculate_logic(self):
        if self.stock_data is None or self.stock_data.empty: return None
        df = self.stock_data
        price = df['收盘'].iloc[-1]
        support = df['最低'].tail(20).min()
        resistance = df['最高'].tail(20).max()
        
        # 倒推西部材料逻辑：利用平均振幅的 15 倍左右来模拟 100% 级别的空间
        avg_amp = ((df['最高'] - df['最低']) / df['收盘'].shift(1)).tail(15).mean()
        target_gain = round(avg_amp * 15 * 100, 2)
        
        return {
            "price": price,
            "support": support,
            "resistance": resistance,
            "target": round(price * (1 + target_gain/100), 2),
            "target_gain": target_gain,
            "stop_loss": round(price * 0.92, 2),
            "position_pct": round((price - support) / (resistance - support) * 100, 1) if resistance != support else 50
        }