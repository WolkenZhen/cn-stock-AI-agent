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
            symbol = self.stock_code.replace("sh","").replace("sz","")
            self.stock_data = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start, end_date=end, adjust="qfq")
            if self.stock_data is not None and not self.stock_data.empty:
                self.latest_price = round(self.stock_data.iloc[-1]['收盘'], 2)
        except:
            self.stock_data = None

    def get_ma_values(self) -> Dict:
        """获取具体的均线数值"""
        if self.stock_data is None or len(self.stock_data) < 20:
            return {"ma5": 0, "ma20": 0}
        df = self.stock_data
        return {
            "ma5": round(df['收盘'].rolling(5).mean().iloc[-1], 2),
            "ma20": round(df['收盘'].rolling(20).mean().iloc[-1], 2)
        }

    def get_indicators(self) -> Dict:
        """供LLM评分使用的因子分布"""
        if self.stock_data is None or len(self.stock_data) < 20: return {}
        close = self.stock_data['收盘']
        ma20 = close.rolling(20).mean().iloc[-1]
        return {
            "涨幅动能": min(max((close.iloc[-1]/close.iloc[-5]-1)*200 + 50, 0), 100),
            "成交量放大": 100 if self.stock_data['成交量'].iloc[-1] > self.stock_data['成交量'].mean() else 30,
            "均线多头": 100 if self.latest_price > ma20 else 0,
            "RSI强弱": 60 
        }

    def calculate_logic(self):
        """核心交易逻辑：信号与区间"""
        if self.stock_data is None: return None
        
        ma = self.get_ma_values()
        low_10 = self.stock_data['最低'].tail(10).min()
        high_10 = self.stock_data['最高'].tail(10).max()
        
        # 简单信号算法
        if self.latest_price > ma['ma20'] and self.latest_price > ma['ma5']:
            signal = "买入/持有"
            advice = "趋势走强，建议继续持有"
        elif self.latest_price < ma['ma20']:
            signal = "减仓"
            advice = "跌破生命线，注意风险"
        else:
            signal = "观察"
            advice = "区间震荡，等待方向"

        return {
            "price": self.latest_price,
            "ma": ma,
            "support": round(low_10, 2),
            "resistance": round(high_10, 2),
            "signal": signal,
            "advice": advice,
            "stop_loss": round(low_10 * 0.97, 2),
            "target": round(high_10 * 1.05, 2)
        }