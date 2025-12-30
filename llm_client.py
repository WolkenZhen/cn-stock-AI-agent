import requests, json, re
from config import LLM_CONFIG

class FreeLLMClient:
    def __init__(self):
        self.api_url = LLM_CONFIG["api_url"]
        self.api_key = LLM_CONFIG["api_key"]
        self.model_name = LLM_CONFIG["model_name"]
        
        # 深度注入：专家筛选标准
        self.expert_persona = """您是一位专业的中国股票筛选专家。
筛选维度包括：
1. 基本面：ROE、净利润增长、PE/PB/PEG、资产负债率等。
2. 技术面：均线系统、MACD、KDJ、动量指标及量价关系。
3. 市场面：主力/北向资金流向、机构重仓、板块活跃度。
4. 政策面：国家政策扶持、改革红利。

筛选策略：结合价值投资（低估高分红）、成长投资（高增长新行业）和主题投资（政策驱动）。"""

    def _call_llm(self, prompt, system="你是一个顶级量化专家"):
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.model_name, "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}], "temperature": 0.3}
        try:
            res = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            return res.json()['choices'][0]['message']['content']
        except: return None

    def analyze_market_hotspots(self):
        prompt = "作为股票专家，总结今日 A 股最热门的 3 个产业新闻和政策方向，说明其核心逻辑。"
        return self._call_llm(prompt, self.expert_persona)

    def evolve_strategy(self, history_str, current_weights):
        # 强制要求 AI 返回中文 Key 以对应代码
        prompt = f"根据历史表现：{history_str}。当前权重：{current_weights}。请微调权重。要求：返回 JSON，且 Key 必须维持 '趋势'、'动能'、'成交'、'弹性'。"
        res = self._call_llm(prompt, "你是一个量化策略优化专家")
        try:
            return json.loads(re.search(r'\{.*\}', res, re.DOTALL).group())
        except: return None

    def ai_expert_selection(self, context):
        prompt = f"【待选池】:\n{context}\n\n请基于基本面、技术面、市场面和政策面维度，选出 5 个最具有爆发潜力的个股编号。直接返回编号，逗号分隔。"
        res = self._call_llm(prompt, self.expert_persona)
        try:
            return [int(x) for x in re.findall(r'\d+', res)]
        except: return []