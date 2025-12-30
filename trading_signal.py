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
            symbol = self.stock_code.replace("sh", "").replace("sz", "")
            self.stock_data = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start, end_date=end, adjust="qfq")
        except: self.stock_data = None

    def get_indicators(self):
        if self.stock_data is None or len(self.stock_data) < 65: return {}
        df = self.stock_data
        
        curr = df['收盘'].iloc[-1]
        ma20 = df['收盘'].rolling(20).mean().iloc[-1]
        ma20_prev = df['收盘'].rolling(20).mean().iloc[-2]
        ma60 = df['收盘'].rolling(60).mean().iloc[-1]
        
        # 趋势得分（100或0）
        is_uptrend = (curr > ma60) and (ma20 > ma20_prev) and (curr > ma20)
        trend_score = 100 if is_uptrend else 0
        
        momentum = (df['收盘'].iloc[-1] / df['收盘'].iloc[-20] - 1) * 100
        vol_ratio = df['成交量'].iloc[-1] / df['成交量'].tail(10).mean()
        amplitude = ((df['最高'] - df['最低']) / df['收盘'].shift(1)).tail(5).mean() * 100
        
        return {
            "趋势": trend_score, 
            "动能": round(max(0, momentum * 5), 1), 
            "成交": round(vol_ratio * 15, 1), 
            "弹性": round(amplitude * 10, 1)
        }

    def calculate_logic(self):
        if self.stock_data is None or self.stock_data.empty: return None
        df = self.stock_data
        price = df['收盘'].iloc[-1]
        
        support = round(df['最低'].tail(20).min(), 2)
        resistance = round(df['最高'].tail(20).max(), 2)
        range_size = resistance - support
        position_pct = round(((price - support) / range_size * 100), 1) if range_size != 0 else 50
        
        df['TR'] = np.maximum(df['最高'] - df['最低'], 
                             np.maximum(abs(df['最高'] - df['收盘'].shift(1)), 
                                        abs(df['最低'] - df['收盘'].shift(1))))
        atr = df['TR'].tail(14).mean()
        
        target_gain = round(((df['最高'] - df['最低']) / df['最低']).tail(10).mean() * 6 * 100, 2)

        return {
            "price": price, "support": support, "resistance": resistance,
            "position_pct": position_pct, "target": round(price * (1 + target_gain/100), 2),
            "target_gain": target_gain, "stop_loss": round(price - (2 * atr), 2)
        }