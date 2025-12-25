import requests
import json
import re
from config import LLM_CONFIG
from typing import List, Dict, Optional

class FreeLLMClient:
    def __init__(self):
        self.api_url = LLM_CONFIG["api_url"]
        self.api_key = LLM_CONFIG["api_key"]
        self.model_name = LLM_CONFIG["model_name"]

    def _call_llm(self, prompt: str) -> Optional[str]:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "你是一个资深量化基金经理。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": LLM_CONFIG["temperature"]
        }
        try:
            res = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            return res.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"⚠️  LLM API 调用失败: {e}")
            return None

    def ai_final_selection(self, candidates: List[Dict]) -> List[int]:
        """让 AI 从候选名单中根据博弈逻辑选出 5 只"""
        context = ""
        for i, c in enumerate(candidates):
            context += f"编号:{i} | {c['name']}({c['code']}) | 现价:{c['price']} | 预期收益:{c['target_gain']}% | 位阶:{c['position_pct']}% | 核心分:{c['total_score']}\n"
        
        prompt = f"""
        请从以下量化初筛的潜力股中选出“爆发力最强且最稳健”的 5 只，请考虑空间位阶和收益比。
        {context}
        请直接给出选出的 5 个编号（如 0,3,7,12,15），用英文逗号分隔，不要输出任何解释文字。
        """
        response = self._call_llm(prompt)
        try:
            indices = [int(x.strip()) for x in re.findall(r'\d+', response)]
            return indices[:5]
        except:
            return list(range(min(5, len(candidates))))

    def evolve_strategy(self, perf_report: str, current_weights: Dict) -> Dict:
        """根据历史表现自动优化权重"""
        prompt = f"""
        历史表现报告: {perf_report}
        当前权重配置: {current_weights}
        
        请分析盈利和亏损原因，优化因子权重（总和100）。
        仅返回优化后的权重JSON格式，不要文字解释。
        """
        response = self._call_llm(prompt)
        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                new_w = json.loads(match.group())
                # 校验权重总计
                total = sum(new_w.values())
                return {k: round(v/total*100, 1) for k, v in new_w.items()}
        except:
            pass
        return current_weights