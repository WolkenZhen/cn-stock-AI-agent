import argparse
from datetime import datetime
from trading_signal import TradingSignalGenerator
from llm_client import FreeLLMClient
import akshare as ak

def get_stock_name(stock_code: str) -> str:
    try:
        code = stock_code.replace("sh", "").replace("sz", "")
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'] == code]
        return row.iloc[0]['名称'] if not row.empty else "未知"
    except: return "未知"

def analyze_single_stock(stock_code: str):
    tsg = TradingSignalGenerator(stock_code)
    tsg.fetch_stock_data()
    res = tsg.calculate_logic()
    if res:
        name = get_stock_name(stock_code)
        print(f"\n🚀 [AI 深度个股诊断] {name}({stock_code})")
        print(f"   现价:{res['price']} | 位阶:{res['position_pct']}% | 支撑:{res['support']} | 阻力:{res['resistance']}")
        print(f"   目标:{res['target']} (+{res['target_gain']}%) | 止损:{res['stop_loss']}")
        llm = FreeLLMClient()
        p = f"分析{name}({stock_code})，现价{res['price']}，空间位阶{res['position_pct']}%。给出两句话投资建议。"
        print(f"\n💡 AI 点评：{llm._call_llm(p)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", type=str, required=True)
    args = parser.parse_args()
    analyze_single_stock(args.code)