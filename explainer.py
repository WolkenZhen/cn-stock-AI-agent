import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict
from llm_client import FreeLLMClient
from config import *
import os

class StrategyReportGenerator:
    def __init__(self):
        self.llm_client = FreeLLMClient()
        self.current_date = datetime.now().strftime("%Y-%m-%d")
    
    def load_log_data(self) -> Dict:
        """加载日志数据"""
        data = {
            "stock_selection": pd.DataFrame(),
            "param_optimization": pd.DataFrame(),
            "trading_signals": pd.DataFrame(),
            "factor_weights": {} # 默认为空
        }
        # 加载各路日志文件
        if os.path.exists("strategy_log/stock_selection_log.csv"):
            data["stock_selection"] = pd.read_csv("strategy_log/stock_selection_log.csv")
        if os.path.exists("strategy_log/trading_signals_log.csv"):
            data["trading_signals"] = pd.read_csv("strategy_log/trading_signals_log.csv")
        return data
    
    def generate_daily_report(self) -> None:
        """生成每日策略报告（LLM增强）"""
        print(f"\n📄 正在生成{self.current_date}每日报告...")
        data = self.load_log_data()
        
        daily_stocks = data["stock_selection"] # 简化逻辑：假设当前加载的就是最新选股
        
        if daily_stocks.empty:
            print(f"⚠️  无交易数据，无法生成每日报告")
            return
        
        # 提取选股展示字符串
        top_stocks_str = "\n".join([f"- {row['股票名称']}（{row['代码']}）" for _, row in daily_stocks.head(10).iterrows()])
        
        # LLM提示词
        prompt = f"""
        作为专业的A股分析师，生成{self.current_date}策略日报：
        1. 今日精选个股：{top_stocks_str}
        2. 选股逻辑：基于全市场1000只活跃股扫描，锁定综合评分前10。
        3. 操作核心：严格执行买入和止损参考价位。
        """
        
        # 修改点：确保调用接口名称一致
        daily_report = self.llm_client._call_llm(prompt)
        
        # 保存报告
        report_path = f"strategy_log/daily_report_{self.current_date}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# A股策略日报（{self.current_date}）\n\n")
            f.write(daily_report if daily_report else "报告生成失败")
        
        print(f"✅ 每日报告已保存：{report_path}")

if __name__ == "__main__":
    generator = StrategyReportGenerator()
    generator.generate_daily_report()