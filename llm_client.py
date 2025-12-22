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
                {"role": "system", "content": "你是一个专业的量化策略专家，只输出JSON格式的数据。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": LLM_CONFIG["temperature"]
        }
        try:
            res = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            res.raise_for_status()
            return res.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"⚠️  API调用失败: {e}")
            return None

    def evolve_strategy(self, market_data: str, current_weights: Dict) -> Dict:
        """让DeepSeek分析市场并进化权重"""
        prompt = f"""
        当前因子权重: {current_weights}
        今日强势股特征:
        {market_data}
        
        请分析今日行情，并给出优化的明日因子权重（总和必须为100）。
        直接返回JSON，例如: {{"涨幅动能": 20, "成交量放大": 30, "均线多头": 30, "RSI强弱": 20}}
        """
        response = self._call_llm(prompt)
        if not response: return current_weights
        try:
            # 提取字符串中的JSON内容
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                return json.loads(match.group())
            return current_weights
        except:
            return current_weights