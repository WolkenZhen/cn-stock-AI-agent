import requests, json, re
from config import LLM_CONFIG

class FreeLLMClient:
    def __init__(self):
        self.api_url = LLM_CONFIG["api_url"]
        self.api_key = LLM_CONFIG["api_key"]
        self.model_name = LLM_CONFIG["model_name"]
        self.expert_persona = """您是一位资深的A股量化交易专家。
        您擅长从混乱的市场中通过“技术形态”和“资金流向”挖掘具有 Alpha 超额收益的股票。
        您对创业板（20%涨跌幅）和科创板的波动风险有深刻认识。"""

    def _call_llm(self, prompt, system=None):
        system_msg = system if system else self.expert_persona
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1 # 降低随机性，确保逻辑严密
        }
        try:
            res = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            return res.json()['choices'][0]['message']['content']
        except: return None

    def get_market_selection_criteria(self):
        prompt = "分析当前A股热点，给出今日选股的3个核心关键词和偏好的技术形态。格式：关键词1,关键词2,关键词3 ### 形态描述"
        res = self._call_llm(prompt)
        if res and "###" in res:
            parts = res.split("###")
            return [k.strip() for k in parts[0].split(",")], parts[1].strip()
        return ["底部放量", "趋势修复"], "低位金叉"

    def ai_deep_mining(self, criteria, candidates):
        """[Alpha 挖掘逻辑] 让 DeepSeek 对精英池进行二次逻辑评分"""
        prompt = f"""
        今日市场审美：{criteria}
        以下是量化初筛后的候选股（包含主板、创业板、科创板）：
        {candidates}
        
        请作为专家，从中选出最具有爆发力的个股。
        对于入选的个股，请返回以下 JSON 格式：
        {{
          "代码": {{
            "alpha_score": 0-25之间的数值 (根据该股的技术形态契合度给分),
            "reason": "深度挖掘理由，字数在30字以内"
          }}
        }}
        注意：必须只返回 JSON，不要解释。
        """
        res = self._call_llm(prompt)
        try:
            # 提取 JSON 部分
            match = re.search(r'\{.*\}', res, re.DOTALL)
            return json.loads(match.group()) if match else {}
        except:
            return {}