import requests, json, re
import akshare as ak
import pandas as pd
from config import LLM_CONFIG

class FreeLLMClient:
    def __init__(self):
        self.api_url = LLM_CONFIG["api_url"]
        self.api_key = LLM_CONFIG["api_key"]
        self.model_name = LLM_CONFIG["model_name"]
        self.expert_persona = "您是精通A股短线博弈的量化基金经理，擅长通过盘面细节捕捉市场情绪。"

    def _call_llm(self, prompt, system=None):
        system_msg = system if system else self.expert_persona
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model_name,
            "messages": [{"role": "system", "content": system_msg}, {"role": "user", "content": prompt}],
            "temperature": 0.5 # 稍微提高温度，增加分析的灵活性
        }
        try:
            res = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            return res.json()['choices'][0]['message']['content']
        except: return None

    def fetch_market_analysis(self):
        """
        全方位大盘扫描：双重热点源 + 深度逻辑推演
        """
        sectors, status = ["数据获取中"], "震荡观望"
        try:
            # 1. 获取上证指数技术面
            index_df = ak.stock_zh_index_daily(symbol="sh000001")
            last_close = index_df['close'].iloc[-1]
            pct_change = (last_close / index_df['close'].iloc[-2] - 1) * 100
            ma5 = index_df['close'].rolling(5).mean().iloc[-1]
            ma20 = index_df['close'].rolling(20).mean().iloc[-1]
            vol_change = (index_df['volume'].iloc[-1] / index_df['volume'].iloc[-2] - 1) * 100
            
            # 2. 获取实时热点 (双重保险)
            top_industries = []
            try:
                # 尝试获取行业板块
                ind_df = ak.stock_board_industry_spot_em()
                ind_df = ind_df.sort_values(by=ind_df.columns[2], ascending=False).head(5) # 按涨跌幅排序
                top_industries = ind_df['板块名称'].tolist()
            except: pass
            
            top_concepts = []
            try:
                # 尝试获取概念板块 (往往比行业更精准)
                con_df = ak.stock_board_concept_name_em()
                con_df = con_df.sort_values(by=con_df.columns[2], ascending=False).head(5)
                top_concepts = con_df['板块名称'].tolist()
            except: pass
            
            # 合并热点信息
            hot_info = f"领涨行业：{top_industries}；领涨概念：{top_concepts}"
            
            # 3. 构造深度思考提示词
            prompt = f"""
            【实时盘面数据】
            上证指数：{last_close} (涨跌幅 {pct_change:.2f}%)
            均线状态：MA5={ma5:.0f}, MA20={ma20:.0f} (现价{'站上' if last_close>ma5 else '跌破'}5日线)
            成交量变化：较昨日{'放量' if vol_change>0 else '缩量'} {abs(vol_change):.1f}%
            【资金战场】
            {hot_info}
            
            【任务】
            1. 分析市场情绪：是普涨、分化还是退潮？
            2. 提炼3个最核心的短线题材关键词（优先用概念名）。
            3. 给出明确的操作建议（进攻/防守/空仓）及仓位。
            
            【输出格式】
            关键词1,关键词2,关键词3 ### 建议：进攻/防守 | 仓位：X成 | 理由：一句话简述逻辑
            """
            
            res = self._call_llm(prompt)
            if res and "###" in res:
                parts = res.split("###")
                sectors = [k.strip() for k in parts[0].split(",") if k.strip()]
                status = parts[1].strip()
                
                # 打印原始热点数据，供您验证
                print(f"🔎 实时抓取热点源数据: {hot_info}")
                
        except Exception as e:
            print(f"⚠️ 大盘分析降级: {e}")
            sectors = ["科技", "新能源", "大消费"]
            status = "震荡整理 | 建议半仓 | 数据源异常，启动安全模式"
            
        return sectors, status

    def get_ai_expert_factor(self, stock_info):
        """专家打分 (保持不变)"""
        prompt = f"""对以下个股进行波段潜力诊断。
        【目标】寻找不仅明日能冲高，且具备3-5天上涨持续性的个股。
        【要求】
        1. 排除已涨停无法买入的（给低分）。
        2. 优先选择底部放量、突破关键压力位的主升浪初期标的。
        数据：{stock_info}
        返回JSON: {{"score": 85, "reason": "xxx", "alpha": 10}}"""
        res = self._call_llm(prompt)
        try:
            match = re.search(r'\{.*\}', res, re.DOTALL)
            data = json.loads(match.group())
            return data.get("score", 60), data.get("reason", "形态良好"), data.get("alpha", 0)
        except: return 60, "量化趋势稳健", 0

    def optimize_weights_deep_evolution(self, history_data, current_weights, market_context):
        """保持不变"""
        prompt = f"""
        【任务】基于历史战绩进行Transformer自注意力权重优化。
        【今日市场环境】{market_context}
        【历史多周期战报】
        {history_data if history_data else "暂无足够T+3数据，请根据市场预判。"}
        【当前权重】{json.dumps(current_weights)}
        【输出】
        只返回JSON，总和100：{{"量价爆发": 40, "趋势强度": 15, ...}}
        """
        res = self._call_llm(prompt)
        try:
            match = re.search(r'\{.*\}', res, re.DOTALL)
            return json.loads(match.group())
        except: return current_weights