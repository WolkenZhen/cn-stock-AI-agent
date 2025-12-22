import pandas as pd
import json
from datetime import datetime
from config import *

class TradingExecutor:
    """交易建议格式化输出工具"""
    def __init__(self):
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.signals_path = "strategy_log/trading_signals_log.csv"

    def load_latest_signals(self) -> pd.DataFrame:
        """加载最新交易信号"""
        if not pd.io.common.file_exists(self.signals_path):
            raise FileNotFoundError("交易信号日志不存在，请先运行auto_strategy_optimizer.py")
        
        signals_df = pd.read_csv(self.signals_path)
        latest_signals = signals_df[signals_df["日期"] == self.current_date]
        if latest_signals.empty:
            raise ValueError(f"无{self.current_date}的交易信号，请先运行策略主程序")
        
        return latest_signals

    def format_trading_advice(self) -> str:
        """格式化交易建议（适合实盘参考）"""
        latest_signals = self.load_latest_signals()
        advice = f"📊 A股短线交易建议（{self.current_date}）\n"
        advice += "="*60 + "\n"
        
        total_invest = 0
        for _, row in latest_signals.iterrows():
            advice += f"\n【{row['股票名称']}（{row['股票代码']}）】\n"
            advice += f"📌 核心数据：\n"
            advice += f"   当前价格：{row['当前价格']:.2f}元\n"
            advice += f"   支撑位：{row['支撑位']:.2f}元 | 阻力位：{row['阻力位']:.2f}元\n"
            advice += f"   止损价：{row['止损价']:.2f}元 | 目标价：{row['目标价']:.2f}元\n"
            advice += f"📌 操作建议：\n"
            advice += f"   购买数量：{row['购买数量']}股\n"
            advice += f"   投入资金：{row['投入资金']:.2f}元（持仓比例：{row['持仓比例']:.2f}%）\n"
            advice += f"   买入区间：{row['支撑位']:.2f} - {row['当前价格']:.2f}元\n"
            advice += f"   执行纪律：跌破止损价立即卖出，达到目标价分批止盈\n"
            advice += "-"*50 + "\n"
            total_invest += row['投入资金']
        
        # 资金汇总
        advice += f"\n💰 资金配置汇总：\n"
        advice += f"   初始资金：{INITIAL_CASH:.2f}元\n"
        advice += f"   总投入资金：{total_invest:.2f}元\n"
        advice += f"   剩余资金：{INITIAL_CASH - total_invest:.2f}元\n"
        advice += f"   总持仓比例：{(total_invest/INITIAL_CASH)*100:.2f}%（≤{MAX_POSITION_RATIO*100}%）\n"
        
        # 风险提示
        advice += f"\n⚠️  风险提示：\n"
        advice += f"   1. 本建议基于量化模型分析，不构成投资决策\n"
        advice += f"   2. 实盘操作需结合大盘环境，避免盲目执行\n"
        advice += f"   3. 严格控制仓位，不追加额外资金，预留风险准备金\n"
        advice += f"   4. 交易时间：仅在A股交易时段（9:30-11:30，13:00-15:00）操作\n"
        
        return advice

    def export_advice_to_file(self) -> None:
        """导出交易建议到文件"""
        advice = self.format_trading_advice()
        file_path = f"strategy_log/trading_advice_{self.current_date}.txt"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(advice)
        
        print(f"✅ 交易建议已导出至：{file_path}")
        print("\n" + advice)

if __name__ == "__main__":
    try:
        executor = TradingExecutor()
        executor.export_advice_to_file()
    except Exception as e:
        print(f"❌ 导出交易建议失败：{str(e)}")