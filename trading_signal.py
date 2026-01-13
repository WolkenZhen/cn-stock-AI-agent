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
            symbol = str(self.stock_code).replace("sh", "").replace("sz", "").zfill(6)
            self.stock_data = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start, end_date=end, adjust="qfq")
        except: self.stock_data = None

    def get_indicators(self, name="", hot_keywords=[]):
        if self.stock_data is None or len(self.stock_data) < 65: return {}
        df = self.stock_data
        curr = df['收盘'].iloc[-1]
        ma20, ma60 = df['收盘'].rolling(20).mean().iloc[-1], df['收盘'].rolling(60).mean().iloc[-1]
        trend = 100 if (curr > ma60 and curr > ma20) else 20
        momentum = (df['收盘'].iloc[-1] / df['收盘'].iloc[-20] - 1) * 100
        vol_ratio = df['成交量'].iloc[-1] / df['成交量'].tail(10).mean()
        amplitude = ((df['最高'] - df['最低']) / df['收盘'].shift(1)).tail(5).mean() * 100
        expert = 100 if any(k in str(name) for k in hot_keywords) else 0
        return {"趋势": trend, "动能": round(max(0, momentum * 5), 1), "成交": round(vol_ratio * 15, 1), "弹性": round(amplitude * 10, 1), "专家": expert}

    def calculate_logic(self, cost_price=None):
        """兼容性接口：支持 cost_price 传入用于 main.py"""
        if self.stock_data is None or self.stock_data.empty: return None
        df = self.stock_data
        price = df['收盘'].iloc[-1]
        low_60, high_60 = df['最低'].tail(60).min(), df['最高'].tail(60).max()
        pos_pct = round((price - low_60) / (high_60 - low_60) * 100, 1) if high_60 != low_60 else 50
        support, resistance = round(df['最低'].tail(10).min(), 2), round(df['最高'].tail(10).max(), 2)
        atr = (df['最高'] - df['最低']).tail(5).mean() 

        # 计算建议价格
        entrust_buy = round(price - (atr * 0.45), 2)
        entrust_sell = 0
        if cost_price:
            cost = float(cost_price)
            entrust_sell = round(max(cost * 1.003, price + (atr * 0.6)), 2)

        return {
            "price": price, "position_pct": pos_pct, 
            "support": support, "resistance": resistance,
            "entrust_buy": entrust_buy, "entrust_sell": entrust_sell,
            "target": round(price * 1.15, 2), "stop_loss": round(price * 0.92, 2)
        }