import pandas as pd
import akshare as ak
import numpy as np
from datetime import datetime, timedelta
from typing import Dict
from config import *

class TradingSignalGenerator:
    def __init__(self, stock_code: str):
        self.stock_code = stock_code
        self.stock_data = None
        self.latest_price = 0

    def fetch_stock_data(self):
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
        try:
            symbol = self.stock_code.replace("sh", "").replace("sz", "")
            self.stock_data = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start, end_date=end, adjust="qfq")
            if self.stock_data is not None and not self.stock_data.empty:
                self.latest_price = round(self.stock_data.iloc[-1]['收盘'], 2)
        except:
            self.stock_data = None

    def get_indicators(self) -> Dict:
        if self.stock_data is None or len(self.stock_data) < 20: 
            return {}
        
        df = self.stock_data
        close = df['收盘']
        # 计算价格弹性：最近10日的波幅
        high_low_range = (df['最高'].tail(10).max() - df['最低'].tail(10).min()) / close.iloc[-1]
        
        return {
            "涨幅动能": min(max((close.iloc[-1]/close.iloc[-5]-1)*200 + 50, 0), 100),
            "成交量放大": 100 if df['成交量'].iloc[-1] > df['成交量'].mean() * 1.5 else 30,
            "均线多头": 100 if self.latest_price > close.rolling(20).mean().iloc[-1] else 0,
            "价格弹性": min(high_low_range * 500, 100)
        }

    def calculate_logic(self):
        """整合支撑、阻力与位阶分析"""
        if self.stock_data is None or self.stock_data.empty: return None
        
        df = self.stock_data
        # 支撑取10日最低，阻力取20日最高
        support = round(df['最低'].tail(10).min(), 2)
        resistance = round(df['最高'].tail(20).max(), 2)
        
        # 计算位置百分比 (0%表示在支撑点，100%表示在阻力点)
        range_val = resistance - support
        if range_val <= 0:
            position_pct = 50.0
        else:
            position_pct = round(((self.latest_price - support) / range_val) * 100, 1)
        
        # 预期收益逻辑 (基于波动率)
        daily_range = (df['最高'] - df['最低']) / df['收盘'].shift(1)
        target_gain_pct = max(0.10, daily_range.tail(20).mean() * 4.0) 
        target = round(self.latest_price * (1 + target_gain_pct), 2)
        
        return {
            "price": self.latest_price,
            "support": support,
            "resistance": resistance,
            "position_pct": position_pct,
            "signal": "低位启动" if position_pct < 30 else ("高位突破" if position_pct > 90 else "趋势持仓"),
            "advice": "价格弹性充足，建议持有" if position_pct < 80 else "面临阻力，注意回调",
            "stop_loss": round(min(support, self.latest_price * 0.95), 2),
            "target": target,
            "target_gain": round(target_gain_pct * 100, 2)
        }