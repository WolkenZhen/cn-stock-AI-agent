import pandas as pd
import akshare as ak
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
        start = (datetime.now() - timedelta(days=60)).strftime("%Y%m%d")
        try:
            # 自动补全代码格式
            symbol = self.stock_code.replace("sh","").replace("sz","")
            self.stock_data = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start, end_date=end, adjust="qfq")
            if self.stock_data is not None and not self.stock_data.empty:
                self.latest_price = self.stock_data.iloc[-1]['收盘']
        except:
            self.stock_data = None

    def get_indicators(self) -> Dict:
        if self.stock_data is None or len(self.stock_data) < 20: return {}
        close = self.stock_data['收盘']
        vol = self.stock_data['成交量']
        return {
            "涨幅动能": min(max((close.iloc[-1]/close.iloc[-5]-1)*200 + 50, 0), 100),
            "成交量放大": 100 if vol.iloc[-1] > vol.mean() else 30,
            "均线多头": 100 if close.iloc[-1] > close.rolling(20).mean().iloc[-1] else 0,
            "RSI强弱": 60
        }

    def calculate_boundaries(self) -> Dict:
        if self.stock_data is None or self.stock_data.empty: return {"支撑": 0, "阻力": 0}
        return {
            "支撑": round(self.stock_data['最低'].tail(5).min(), 2),
            "阻力": round(self.stock_data['最高'].tail(5).max(), 2)
        }