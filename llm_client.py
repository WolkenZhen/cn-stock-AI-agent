import requests, json, re
from config import LLM_CONFIG

class FreeLLMClient:
    def __init__(self):
        self.api_url = LLM_CONFIG["api_url"]
        self.api_key = LLM_CONFIG["api_key"]
        self.model_name = LLM_CONFIG["model_name"]
        self.expert_persona = "您是一位深耕中国A股的量化策略专家，擅长从技术面与情绪面捕捉逆势黑马。"

    def _call_llm(self, prompt, system=None):
        system_msg = system if system else self.expert_persona
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model_name,
            "messages": [{"role": "system", "content": system_msg}, {"role": "user", "content": prompt}],
            "temperature": 0.2
        }
        try:
            res = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            return res.json()['choices'][0]['message']['content']
        except: return None

    def get_market_selection_criteria(self):
        prompt = "请给出今日选股的3个核心关键词和偏好的形态。格式：关键词1,关键词2,关键词3 ### 形态描述"
        res = self._call_llm(prompt)
        if res and "###" in res:
            parts = res.split("###")
            return [k.strip() for k in parts[0].split(",")], parts[1].strip()
        return ["价值收缩", "放量支撑"], "底部放量"

    def ai_deep_mining(self, criteria, candidates):
        """
        [挖掘引擎] 让 DeepSeek 对精英池进行二次打分 (Alpha Score)
        """
        prompt = f"""
        今日市场策略关键词：{criteria}
        候选股列表：
        {candidates}
        
        请从上述候选股中挖掘出最符合“逆势抗跌”或“突破动能”的10只个股。
        对于每只入选股，请提供：
        1. alpha_score (追加评分：0-20分，根据你的逻辑判断该股的溢价能力)
        2. reason (简短的深度挖掘理由)
        
        必须以严格的 JSON 格式返回，键为股票代码。示例：
        {{"000001": {{"alpha_score": 15, "reason": "理由..."}}}}
        """
        res = self._call_llm(prompt)
        try:
            match = re.search(r'\{.*\}', res, re.DOTALL)
            return json.loads(match.group()) if match else {}
        except: return {}

    def evolve_strategy(self, history, weights):
        # 原有权重优化逻辑保留
        return {"新权重": weights}