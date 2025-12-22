import requests
import json
import re
from config import LLM_CONFIG
from typing import Dict, Optional

class FreeLLMClient:
    def __init__(self):
        self.api_url = LLM_CONFIG["api_url"]
        self.api_key = LLM_CONFIG["api_key"]
        self.model_name = LLM_CONFIG["model_name"]

    def _call_llm(self, prompt: str) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "你是一个量化专家，只返回JSON格式。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        try:
            res = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            return res.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"⚠️  LLM请求异常: {e}")
            return None

    def evolve_strategy(self, market_data: str, current_weights: Dict) -> Dict:
        prompt = f"当前权重:{current_weights}\n今日数据:{market_data}\n请给出优化后的权重JSON，总和100。"
        response = self._call_llm(prompt)
        if not response: return current_weights
        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            return json.loads(match.group()) if match else current_weights
        except:
            return current_weights