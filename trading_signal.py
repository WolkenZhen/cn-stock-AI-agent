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
        start = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
        try:
            symbol = self.stock_code.replace("sh", "").replace("sz", "")
            self.stock_data = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start, end_date=end, adjust="qfq")
            if self.stock_data is not None and not self.stock_data.empty:
                self.latest_price = round(self.stock_data.iloc[-1]['收盘'], 2)
        except:
            self.stock_data = None

    def get_indicators(self) -> Dict:
        if self.stock_data is None or len(self.stock_data) < 20: return {}
        df = self.stock_data
        close = df['收盘']
        # 价格弹性：10日振幅
        elasticity = (df['最高'].tail(10).max() - df['最低'].tail(10).min()) / close.iloc[-1]
        
        return {
            "涨幅动能": min(max((close.iloc[-1]/close.iloc[-5]-1)*200 + 50, 0), 100),
            "成交量放大": 100 if df['成交量'].iloc[-1] > df['成交量'].mean() * 1.5 else 30,
            "均线多头": 100 if self.latest_price > close.rolling(20).mean().iloc[-1] else 0,
            "价格弹性": min(elasticity * 500, 100)
        }

    def calculate_logic(self):
        if self.stock_data is None or self.stock_data.empty: return None
        df = self.stock_data
        support = round(df['最低'].tail(10).min(), 2)
        resistance = round(df['最高'].tail(20).max(), 2)
        
        range_val = resistance - support
        pos_pct = round(((self.latest_price - support) / range_val * 100), 1) if range_val > 0 else 50.0
        
        volatility = ((df['最高'] - df['最低']) / df['收盘'].shift(1)).tail(20).mean()
        target_gain = max(0.12, volatility * 4.5)
        
        return {
            "price": self.latest_price,
            "support": support,
            "resistance": resistance,
            "position_pct": pos_pct,
            "target": round(self.latest_price * (1 + target_gain), 2),
            "target_gain": round(target_gain * 100, 2),
            "stop_loss": round(min(support, self.latest_price * 0.94), 2),
            "signal": "空间启动" if pos_pct < 45 else "趋势持有",
            "advice": "安全边际较高" if pos_pct < 60 else "高位注意震荡"
        }