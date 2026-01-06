import requests, json, re
from config import LLM_CONFIG

class FreeLLMClient:
    def __init__(self):
        self.api_url = LLM_CONFIG["api_url"]
        self.api_key = LLM_CONFIG["api_key"]
        self.model_name = LLM_CONFIG["model_name"]
        
        # 深度注入你提供的专业中国股市分析师提示词
        self.expert_persona = """您是一位专业的中国股市分析师。具备A股涨跌停、T+1、行业轮动、监管环境及市场情绪的深度理解。
您的分析重点包括：技术面分析、结合中国会计准则的基本面分析、评估政策影响的政策面分析，以及分析北向资金/融资融券的资金面分析。
您需要特别考虑中国股市特色：涨跌停限制、ST风险、板块差异、国企改革及中美关系影响。"""

    def _call_llm(self, prompt, system=None):
        system = system or self.expert_persona
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.model_name, "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}], "temperature": 0.3}
        try:
            res = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            return res.json()['choices'][0]['message']['content']
        except: return None

    def analyze_market_hotspots(self):
        # 增加提取关键词的要求，用于代码层面的强制匹配
        prompt = "总结今日A股最火的3个产业政策方向，并为每个方向提供2个核心关键词（如：半导体, 存储）。格式要求：[政策分析文本] ### 关键词1, 关键词2, 关键词3"
        res = self._call_llm(prompt)
        if "###" in res:
            text, keys = res.split("###")
            keywords = [k.strip() for k in keys.split(",") if len(k.strip()) > 0]
            return text.strip(), keywords
        return res, []

    def evolve_strategy(self, history_str, current_weights):
        # 支持 5 个权重的进化逻辑
        prompt = f"历史表现：{history_str}。当前权重：{current_weights}。请微调权重。要求：返回JSON，Key必须是：'趋势'、'动能'、'成交'、'弹性'、'专家'。"
        res = self._call_llm(prompt, "你是一个量化策略优化专家")
        try:
            return json.loads(re.search(r'\{.*\}', res, re.DOTALL).group())
        except: return None

    def ai_expert_selection(self, context):
        prompt = f"【量化候选池】:\n{context}\n\n请基于你作为中国股市专家的判断，选出5个最具爆发潜力的编号。直接返回编号，逗号分隔。"
        res = self._call_llm(prompt)
        try:
            return [int(x) for x in re.findall(r'\d+', res)]
        except: return []