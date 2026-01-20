import pandas as pd
import akshare as ak
import numpy as np
from datetime import datetime, timedelta

class TradingSignalGenerator:
    def __init__(self, stock_code: str):
        self.stock_code = str(stock_code).zfill(6)
        self.stock_data = None

    def fetch_stock_data(self):
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=160)).strftime("%Y%m%d")
        try:
            self.stock_data = ak.stock_zh_a_hist(symbol=self.stock_code, period="daily", start_date=start, end_date=end, adjust="qfq")
        except: self.stock_data = None

    def get_indicators(self):
        if self.stock_data is None or len(self.stock_data) < 30: return None
        df = self.stock_data
        curr = df.iloc[-1]
        
        # 1. 量价爆发
        vol_ratio = curr['成交量'] / df['成交量'].tail(5).mean()
        price_change = curr['涨跌幅']
        
        f1 = 40
        if price_change > 9.7: f1 = 10 # 涨停不追
        elif price_change > 5: f1 += 50
        
        if 1.5 < vol_ratio < 4: f1 += 30
        if curr['收盘'] > df['收盘'].iloc[-20:-1].max() * 0.98: f1 += 20
        
        # 2. 趋势强度
        ma20 = df['收盘'].rolling(20).mean().iloc[-1]
        f2 = 100 if curr['收盘'] > ma20 else 30

        # 3. 资金流向
        strength = (curr['收盘'] - curr['最低']) / (curr['最高'] - curr['最低'] + 0.01)
        f3 = strength * 100

        # 4. 基本面安全垫
        f4 = 60
        if curr['收盘'] > 3: f4 += 20
        if df['涨跌幅'].tail(5).min() > -7: f4 += 20

        return {"量价爆发": round(f1, 1), "趋势强度": round(f2, 1), "资金流向": round(f3, 1), "基本面安全垫": f4}

    def calculate_logic(self, weights=None):
        """
        参数 weights: 当前 AI 进化的权重字典，用于动态调整止盈策略
        """
        if self.stock_data is None or self.stock_data.empty: return None
        df = self.stock_data
        price = df['收盘'].iloc[-1]
        atr = (df['最高'] - df['最低']).tail(14).mean()
        
        # 委托买入价
        ma5 = df['收盘'].rolling(5).mean().iloc[-1]
        entrust_buy = round(max(price * 0.99, ma5), 2)
        
        # --- 动态止盈逻辑 ---
        # 默认 T+1 止盈是 1.2倍 ATR
        profit_ratio = 1.2
        
        # 如果 AI 认为现在适合“量价爆发”（权重>35），说明是进攻行情，格局放大，看 T+3
        if weights and weights.get("量价爆发", 0) > 35:
            profit_ratio = 2.0 # 目标位拉高到 2.0 ATR (博弈连板)
        
        t1_sell_target = round(price + profit_ratio * atr, 2)
        stop_loss = round(min(price - 0.8 * atr, df['最低'].iloc[-1] * 0.98), 2)
        
        return {
            'price': price,
            'entrust_buy': entrust_buy,
            'entrust_sell_t1': t1_sell_target,
            'target': t1_sell_target,
            'stop_loss': stop_loss,
            'atr': round(atr, 2)
        }