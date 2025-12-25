import requests, json, re
from config import LLM_CONFIG

class FreeLLMClient:
    def __init__(self):
        self.api_url = LLM_CONFIG["api_url"]
        self.api_key = LLM_CONFIG["api_key"]
        self.model_name = LLM_CONFIG["model_name"]

    def _call_llm(self, prompt, system="你是一个顶级量化专家"):
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.model_name, "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}], "temperature": 0.3}
        try:
            res = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            return res.json()['choices'][0]['message']['content']
        except: return None

    def analyze_market_hotspots(self):
        # 彻底去 Hard-coding，由 AI 自主分析
        prompt = "检索并总结今日 A 股最热门的 3 个产业新闻和政策方向，说明为什么这些方向容易出翻倍股。"
        return self._call_llm(prompt, "你是一个拥有实时感知能力的投资内参官")

    def ai_final_selection_with_prompt(self, full_prompt):
        res = self._call_llm(full_prompt, "你是一个追求极限收益的激进派游资")
        return [int(x) for x in re.findall(r'\d+', res)][:5] if res else [0,1,2,3,4]

    def evolve_strategy(self, history, weights):
        prompt = f"昨日选股表现:{history}\n当前权重:{weights}\n请给出优化后的权重JSON（总和100）。"
        res = self._call_llm(prompt)
        try: return json.loads(re.search(r'\{.*\}', res, re.S).group())
        except: return weights