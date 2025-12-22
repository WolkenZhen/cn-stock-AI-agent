import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict  # 补充导入Dict
from llm_client import FreeLLMClient
from config import *
import os

class StrategyReportGenerator:
    def __init__(self):
        self.llm_client = FreeLLMClient()
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        self.yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    def load_log_data(self) -> Dict:
        """加载日志数据"""
        data = {
            "stock_selection": pd.DataFrame(),
            "param_optimization": pd.DataFrame(),
            "trading_signals": pd.DataFrame(),
            "factor_weights": DEFAULT_FACTOR_WEIGHTS
        }
        
        # 加载选股日志
        if os.path.exists("strategy_log/stock_selection_log.csv"):
            data["stock_selection"] = pd.read_csv("strategy_log/stock_selection_log.csv")
        
        # 加载参数优化日志
        if os.path.exists("strategy_log/param_optimization_log.csv"):
            data["param_optimization"] = pd.read_csv("strategy_log/param_optimization_log.csv")
        
        # 加载交易信号日志
        if os.path.exists("strategy_log/trading_signals_log.csv"):
            data["trading_signals"] = pd.read_csv("strategy_log/trading_signals_log.csv")
        
        # 加载因子权重
        if os.path.exists("strategy_log/factor_weights.json"):
            with open("strategy_log/factor_weights.json", "r") as f:
                data["factor_weights"] = json.load(f)
        
        return data
    
    def generate_daily_report(self) -> None:
        """生成每日策略报告（LLM增强）"""
        print(f"\n📄 正在生成{self.current_date}每日报告...")
        data = self.load_log_data()
        
        # 筛选今日数据
        daily_stocks = data["stock_selection"][data["stock_selection"]["日期"] == self.current_date]
        daily_params = data["param_optimization"][data["param_optimization"]["日期"] == self.current_date]
        daily_signals = data["trading_signals"][data["trading_signals"]["日期"] == self.current_date]
        
        if daily_stocks.empty or daily_params.empty or daily_signals.empty:
            print(f"⚠️  无{self.current_date}交易数据，无法生成每日报告")
            return
        
        # 提取关键数据
        top_stocks_str = "\n".join([f"- {row['股票名称']}（{row['代码']}）：综合得分{row['综合得分']:.1f}分" 
                                   for _, row in daily_stocks.iterrows()])
        best_params = daily_params.iloc[0].to_dict()
        total_invest = daily_signals["投入资金"].sum()
        avg_position_ratio = daily_signals["持仓比例"].mean()
        
        # LLM提示词
        prompt = f"""
        作为专业的A股短线策略分析师，基于以下数据生成{self.current_date}策略日报：
        一、市场概况
        - 选股池规模：{len(data['stock_selection'])}只符合条件的高流动性股票（市值≥500亿，日均成交额≥2亿）
        - TOP5潜力股：{top_stocks_str}
        - 市场特征：从选股结果看，近期高评分股票集中在{self._get_industry_distribution(daily_stocks)}等领域
        二、策略表现（基于180天回测）
        - 最优参数：短期均线{best_params['short_ma']}天，长期均线{best_params['long_ma']}天
        - 回测指标：年化收益率{best_params['年化收益率']}%，胜率{best_params['胜率']}%，最大回撤{best_params['最大回撤']}%
        - 资金配置：总持仓比例{total_invest/INITIAL_CASH*100:.2f}%，单只股票平均持仓{avg_position_ratio:.2f}%
        三、核心个股亮点（3只重点分析）
        {self._get_top3_stock_highlights(daily_signals)}
        四、明日操作建议
        1. 买入时机：优先在个股支撑位附近低吸，避免追高
        2. 风险控制：严格执行止损纪律，跌破止损价立即卖出
        3. 仓位管理：不追加额外资金，保持当前持仓比例
        4. 市场关注：关注大盘成交量变化，若缩量则降低操作频率
        报告要求：
        - 结构清晰，分4个部分，每部分不超过3句话
        - 语言专业简洁，适合短线投资者快速阅读
        - 突出关键数据和操作要点，避免冗余描述
        """
        
        # 调用LLM生成报告
        daily_report = self.llm_client._call_ollama(prompt)
        if not daily_report:
            daily_report = self._generate_default_daily_report(daily_stocks, daily_params, daily_signals)
        
        # 保存报告
        with open(f"strategy_log/daily_report_{self.current_date}.md", "w", encoding="utf-8") as f:
            f.write(f"# A股短线策略日报（{self.current_date}）\n\n")
            f.write(daily_report)
        
        print(f"✅ 每日报告已保存：strategy_log/daily_report_{self.current_date}.md")
    
    def _get_industry_distribution(self, stocks_df: pd.DataFrame) -> str:
        """获取行业分布（简化版）"""
        # 基于股票名称判断行业
        industry_keywords = {
            "金融": ["银行", "证券", "保险", "信托"],
            "消费": ["食品", "饮料", "家电", "零售"],
            "科技": ["科技", "电子", "软件", "芯片"],
            "制造": ["机械", "汽车", "化工", "建材"],
            "医药": ["医药", "生物", "医疗", "健康"]
        }
        
        industry_count = {}
        for _, row in stocks_df.iterrows():
            for industry, keywords in industry_keywords.items():
                if any(keyword in row['股票名称'] for keyword in keywords):
                    industry_count[industry] = industry_count.get(industry, 0) + 1
        
        if not industry_count:
            return "多行业分散"
        return ", ".join([f"{ind}