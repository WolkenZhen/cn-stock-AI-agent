import requests, json, re
from config import LLM_CONFIG

class FreeLLMClient:
    def __init__(self):
        self.api_url = LLM_CONFIG["api_url"]
        self.api_key = LLM_CONFIG["api_key"]
        self.model_name = LLM_CONFIG["model_name"]
        
        # 专家提示词：深度集成中国股市特色
        self.expert_persona = """您是一位专业的中国股市分析师，专门分析A股、港股等中国资本市场。您具备深厚的中国股市知识和丰富的本土投资经验。

您的专业领域包括：
1. **A股市场分析**: 深度理解A股的独特性，包括涨跌停制度、T+1交易、融资融券等
2. **中国经济政策**: 熟悉货币政策、财政政策对股市的影响机制
3. **行业板块轮动**: 掌握中国特色的板块轮动规律和热点切换
4. **监管环境**: 了解证监会政策、退市制度、注册制等监管变化
5. **市场情绪**: 理解中国投资者的行为特征和情绪波动

分析重点：
- **技术面分析**: 使用精确的技术指标分析形态
- **基本面分析**: 结合中国会计准则和财报特点
- **政策面分析**: 评估政策变化对个股和板块的影响
- **资金面分析**: 分析北向资金、融资融券、大宗交易等资金流向
- **市场风格**: 判断当前是成长风格还是价值风格占优"""

    def _call_llm(self, prompt, system=None):
        system_msg = system if system else self.expert_persona
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model_name, 
            "messages": [{"role": "system", "content": system_msg}, {"role": "user", "content": prompt}], 
            "temperature": 0.3
        }
        try:
            res = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            return res.json()['choices'][0]['message']['content']
        except: return None

    def get_market_selection_criteria(self):
        prompt = "基于当前政策面、行业轮动和资金情绪，请给出今日选股的3个核心关键词和偏好的技术形态描述。格式：关键词1,关键词2,关键词3 ### 形态描述"
        res = self._call_llm(prompt)
        if res and "###" in res:
            parts = res.split("###")
            return [k.strip() for k in parts[0].split(",") if k.strip()], parts[1].strip()
        return [], "放量突破"

    def evolve_strategy(self, history_str, current_weights):
        prompt = f"近期表现：{history_str}。当前权重：{current_weights}。请作为一个专业的量化专家微调权重。必须返回包含'调整说明'和'新权重'（包含趋势,动能,成交,弹性,专家）的JSON格式。"
        res = self._call_llm(prompt, system="您是专门负责因子权重优化的量化科学家")
        try:
            match = re.search(r'\{.*\}', res, re.DOTALL)
            return json.loads(match.group()) if match else None
        except: return None

    def ai_deep_decision(self, criteria, candidates_table):
        # 核心修改：明确要求选出 10 只个股
        prompt = f"""【今日选股审美】: {criteria}\n\n【精英备选池 (前300名)】:\n{candidates_table}\n\n请结合专家身份，从以上候选名单中选出10只逻辑最硬、爆发潜力最大的个股。返回JSON格式，Key为代码，Value为简短推荐理由。"""
        res = self._call_llm(prompt)
        try:
            match = re.search(r'\{.*\}', res, re.DOTALL)
            return json.loads(match.group()) if match else {}
        except: return {}