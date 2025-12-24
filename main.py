import argparse
import akshare as ak
import json
import re
from datetime import datetime
from trading_signal import TradingSignalGenerator
from llm_client import FreeLLMClient
from config import *

def get_stock_name(stock_code: str) -> str:
    """获取股票名称"""
    try:
        code = stock_code.replace("sh", "").replace("sz", "")
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'] == code]
        if not row.empty:
            return row.iloc[0]['名称']
    except:
        return "未知股票"
    return "未知股票"

def analyze_single_stock(stock_code: str):
    """单只股票详细分析（补全时间戳、空间分析与美化输出）"""
    current_full_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n🚀 [AI 深度个股诊断] 启动时间: {current_full_time}")
    print("=" * 75)
    
    try:
        tsg = TradingSignalGenerator(stock_code)
        llm = FreeLLMClient()
        
        tsg.fetch_stock_data()
        if tsg.stock_data is None or tsg.stock_data.empty:
            print(f"❌ 错误：无法获取股票 {stock_code} 的行情数据。")
            return
            
        stock_name = get_stock_name(stock_code)
        res = tsg.calculate_logic()
        if not res:
            print("❌ 错误：指标计算失败。")
            return

        # 空间可视化进度条
        bar_len = int(max(0, min(res['position_pct'], 100)) / 5)
        progress_bar = f"[{'#' * bar_len}{'-' * (20 - bar_len)}]"

        print(f"📊 诊断标的：{stock_code} {stock_name}")
        print(f"   📈 空间位置：支撑 {res['support']} | **最新价 {res['price']}** | 阻力 {res['resistance']}")
        print(f"   🧭 当前位阶：{progress_bar} {res['position_pct']}% (靠近100%提示短线超买风险)")
        print(f"   🎯 空间预测：目标价 {res['target']} | 预期收益 **+{res['target_gain']}%**")
        print(f"   🛡️ 风险防御：建议止损 {res['stop_loss']} | 信号：{res['signal']}")
        print(f"   📝 核心点评：{res['advice']}")
        print("-" * 75)

        # 调用 AI 并处理 JSON 格式
        print("🧠 AI 逻辑分析中...")
        indicators = tsg.get_indicators()
        prompt = f"""
        作为量化专家，请对 {stock_name}({stock_code}) 进行专业复盘：
        现价:{res['price']}, 支撑:{res['support']}, 阻力:{res['resistance']}, 弹性分:{indicators.get('价格弹性', 0)}。
        请直接给出“空间评价”和“博弈建议”。
        """
        
        raw_analysis = llm._call_llm(prompt)
        
        # 尝试从 JSON 中提取文字，如果不是 JSON 则直接显示
        try:
            if raw_analysis.startswith('{'):
                data = json.loads(raw_analysis)
                print(f"\n💡 AI 空间评价：{data.get('空间爆发力评价', data.get('空间评价', ''))}")
                print(f"💡 AI 博弈建议：{data.get('操作博弈建议', data.get('博弈建议', ''))}")
            else:
                print(f"\n💡 AI 深度解读：\n{raw_analysis.strip()}")
        except:
            print(f"\n💡 AI 深度解读：\n{raw_analysis.strip()}")
        
    except Exception as e:
        print(f"\n❌ 分析失败：{str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI 单股深度诊断工具")
    parser.add_argument("--code", type=str, required=True, help="股票代码")
    args = parser.parse_args()
    analyze_single_stock(args.code)