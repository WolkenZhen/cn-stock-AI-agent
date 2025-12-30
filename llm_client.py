import requests, json, re
from config import LLM_CONFIG

class FreeLLMClient:
    def __init__(self):
        self.api_url = LLM_CONFIG["api_url"]
        self.api_key = LLM_CONFIG["api_key"]
        self.model_name = LLM_CONFIG["model_name"]

    def _call_llm(self, prompt, system="你是一个顶级量化专家"):
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model_name, 
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}], 
            "temperature": 0.2
        }
        try:
            res = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            return res.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"❌ LLM API 调用失败: {e}")
            return None

    def analyze_market_hotspots(self):
        prompt = "检索并总结今日 A 股最热门的 3 个方向。要求：只选当前处于上升通道的板块。"
        return self._call_llm(prompt, "你是一个拥有实时感知能力的投资专家")

    def ai_final_selection_with_prompt(self, full_prompt):
        res = self._call_llm(full_prompt, "你是一个稳健派游资，拒绝下降趋势股")
        if res:
            try:
                return [int(x) for x in re.findall(r'\d+', res)][:5]
            except: return [0,1,2,3,4]
        return [0,1,2,3,4]

    def evolve_strategy(self, perf_report, current_weights):
        # 强制 AI 使用统一的键名：趋势, 动能, 成交, 弹性
        prompt = f"""
        【历史复盘数据】: {perf_report}
        【当前权重】: {current_weights}
        
        任务：根据盈亏表现优化权重。如果普遍亏损，必须大幅增加“趋势”权重（防御）。
        必须返回 JSON，键名必须严格为：趋势, 动能, 成交, 弹性。总和100。
        """
        res = self._call_llm(prompt)
        try:
            json_str = re.search(r'\{.*\}', res, re.S).group()
            return json.loads(json_str)
        except:
            return None