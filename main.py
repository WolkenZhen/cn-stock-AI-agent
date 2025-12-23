import argparse
import akshare as ak
import json
from datetime import datetime
from trading_signal import TradingSignalGenerator
from llm_client import FreeLLMClient
from config import *

def get_stock_name(stock_code: str) -> str:
    """获取股票名称的辅助函数"""
    try:
        # 统一去掉可能的前缀
        code = stock_code.replace("sh", "").replace("sz", "")
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'] == code]
        if not row.empty:
            return row.iloc[0]['名称']
    except:
        return "未知股票"
    return "未知股票"

def analyze_single_stock(stock_code: str):
    """单只股票详细分析（集成 DeepSeek 诊断）"""
    print(f"🚀 正在启动 AI 深度分析：{stock_code}")
    print("=" * 65)
    
    try:
        # 1. 初始化工具
        tsg = TradingSignalGenerator(stock_code)
        llm = FreeLLMClient()
        
        # 2. 获取基础数据
        tsg.fetch_stock_data()
        if tsg.stock_data is None or tsg.stock_data.empty:
            print(f"❌ 错误：无法获取股票 {stock_code} 的行情数据，请检查网络或代码。")
            return
            
        # 3. 计算核心指标逻辑 (调用我们优化后的 trading_signal)
        res = tsg.calculate_logic()
        if not res:
            print("❌ 错误：指标计算异常。")
            return
            
        stock_name = get_stock_name(stock_code)
        
        # 4. 输出结构化诊断结果 (满足你要求的格式)
        print(f"\n诊断结果: {stock_code} {stock_name}")
        print(f"   基础信息：最新价{res['price']}元 | 支撑位{res['support']}元 | 阻力位{res['resistance']}元")
        print(f"   均线状态：5日({res['ma']['ma5']}) | 20日({res['ma']['ma20']})")
        print(f"   交易信号：{res['signal']}")
        print(f"   操作建议：{res['advice']} | 止损价{res['stop_loss']}元 | 目标价{res['target']}元")
        print("-" * 65)

        # 5. 调用 DeepSeek 进行逻辑点评
        print("🧠 正在请求 DeepSeek AI 进行盘面解读...")
        
        # 构造给 AI 的复盘提示词
        prompt = f"""
        作为量化分析专家，请根据以下数据对 {stock_name}({stock_code}) 进行简短复盘：
        - 当前价格: {res['price']} (支撑:{res['support']}, 阻力:{res['resistance']})
        - 均线状态: MA5={res['ma']['ma5']}, MA20={res['ma']['ma20']}
        - 因子分值: {tsg.get_indicators()}
        请从“趋势强度”和“入场风险”两个维度给出点评，150字以内，语气专业。
        """
        
        # 注意：这里调用的是 llm_client 中的 _call_llm 方法
        ai_review = llm._call_llm(prompt)
        
        if ai_review:
            print(f"\n🤖 AI 深度诊断报告：")
            print(ai_review)
        else:
            print("\n⚠️ AI 诊断接口响应超时，请检查 DeepSeek API Key 或网络。")
            
        print("\n" + "=" * 65)
        
    except Exception as e:
        print(f"\n❌ 程序运行出错：{str(e)}")

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='A股单股AI深度诊断工具')
    parser.add_argument('--code', type=str, required=True, help='股票代码，例如 600519')
    args = parser.parse_args()
    
    # 执行分析
    analyze_single_stock(args.code)