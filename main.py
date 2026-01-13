import argparse
import pandas as pd
import akshare as ak
from trading_signal import TradingSignalGenerator
from llm_client import FreeLLMClient

def get_stock_name(stock_code: str) -> str:
    try:
        code = str(stock_code).replace("sh", "").replace("sz", "").zfill(6)
        # 获取即时行情快照以获取名称
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'] == code]
        return row.iloc[0]['名称'] if not row.empty else "未知个股"
    except: return "未知"

def analyze_single_stock(stock_code: str, cost_price=None):
    # 1. 初始化信号生成器
    tsg = TradingSignalGenerator(stock_code)
    tsg.fetch_stock_data()
    
    # 2. 调用逻辑计算 (传入成本价以计算卖出建议)
    res = tsg.calculate_logic(cost_price=cost_price)
    
    if res:
        name = get_stock_name(stock_code)
        print(f"\n🚀 [AI 深度个股诊断] {name}({stock_code})")
        print(f"   现价: {res['price']} | 位阶: {res['position_pct']}% | 支撑: {res['support']} | 阻力: {res['resistance']}")
        print("-" * 70)
        
        # --- 补回持仓管理建议功能 ---
        if cost_price:
            # 如果提供了成本价，计算收益并给出卖出参考
            profit = (res['price'] / float(cost_price) - 1) * 100
            print(f"🏮 【持仓建议】")
            print(f"   >>> 当前成本: {cost_price} | 当前盈亏: {profit:.2f}%")
            print(f"   >>> 今日建议卖出委托价: {res['entrust_sell']} (基于ATR及成本计算)")
        else:
            # 如果没提供成本价，给出引导提示
            print(f"💡 【持仓管理提示】")
            print(f"   >>> 若需针对性卖出建议，请带参数运行: --cost [你的成本价]")
        
        print("-" * 70)
        print(f"🎯 【交易参考】")
        print(f"   >>> 当日建议买入委托价: {res['entrust_buy']}")
        print(f"   >>> 止盈目标: {res['target']} | 止损参考: {res['stop_loss']}")
        print("-" * 70)

        # 3. 调用 DeepSeek 专家点评
        llm = FreeLLMClient()
        p = f"请作为顶级分析师，简要点评{name}({stock_code})。现价{res['price']}，空间位阶{res['position_pct']}%，支撑位{res['support']}。给出两句话的操作策略建议。"
        print(f"🧠 DeepSeek 专家点评：\n   {llm._call_llm(p)}\n")
    else:
        print(f"❌ 无法获取 {stock_code} 的完整行情数据，请稍后重试。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A股单兵诊断工具")
    parser.add_argument("--code", type=str, required=True, help="股票代码，如 002149")
    parser.add_argument("--cost", type=float, help="持仓成本价")
    
    args = parser.parse_args()
    analyze_single_stock(args.code, args.cost)