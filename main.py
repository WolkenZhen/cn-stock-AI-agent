import argparse
import pandas as pd
import akshare as ak
from trading_signal import TradingSignalGenerator
from llm_client import FreeLLMClient

def get_stock_name(stock_code: str) -> str:
    try:
        code = stock_code.replace("sh", "").replace("sz", "").zfill(6)
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'] == code]
        return row.iloc[0]['名称'] if not row.empty else "未知个股"
    except: return "未知"

def analyze_single_stock(stock_code: str, cost_price=None):
    tsg = TradingSignalGenerator(stock_code)
    tsg.fetch_stock_data()
    
    # 获取包含所有建议的计算结果
    res = tsg.calculate_logic(cost_price=cost_price)
    
    if res:
        name = get_stock_name(stock_code)
        print(f"\n🚀 [AI 深度个股诊断] {name}({stock_code})")
        print(f"   现价: {res['price']} | 位阶: {res['position_pct']}% | 支撑: {res['support']} | 阻力: {res['resistance']}")
        print("-" * 70)
        
        # 场景一：针对已持仓 (由 cost_price 触发)
        if cost_price:
            print(f"🏮 【持仓管理建议】 状态: {res['status']}")
            print(f"   >>> 🔔 当日委托卖出价: {res['entrust_sell']} (逻辑: 尝试回本或止盈离场)")
        else:
            print(f"🏮 【持仓管理建议】")
            print(f"   >>> 若需针对性卖出建议，请带参数运行: --cost [你的成本价]")

        # 场景二：针对准备买入
        print(f"\n🎯 【新开仓买入建议】")
        print(f"   >>> 💰 当日建议买入委托价: {res['entrust_buy']} (逻辑: 盘中回踩低吸点)")
        print(f"   🎯 止盈目标: {res['target']} | 止损参考: {res['stop_loss']}")
        print("-" * 70)

        # AI 点评
        llm = FreeLLMClient()
        p = f"分析{name}({stock_code})，现价{res['price']}，位阶{res['position_pct']}%。给出两句话实战操作建议。"
        print(f"💡 AI 专家点评：{llm._call_llm(p)}")
        print("\n")
    else:
        print(f"❌ 无法获取 {stock_code} 的数据，请检查代码输入是否正确。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", type=str, required=True, help="股票代码，如 002149")
    parser.add_argument("--cost", type=float, help="你的持仓成本价")
    args = parser.parse_args()
    
    analyze_single_stock(args.code, args.cost)