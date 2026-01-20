import argparse
import pandas as pd
import akshare as ak
from trading_signal import TradingSignalGenerator
from llm_client import FreeLLMClient

def get_stock_name(stock_code: str) -> str:
    """获取股票名称"""
    try:
        code = str(stock_code).zfill(6)
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'] == code]
        return row.iloc[0]['名称'] if not row.empty else "未知个股"
    except: return "未知"

def analyze_single_stock(stock_code: str, cost_price=None):
    # 1. 初始化信号生成器并获取数据
    tsg = TradingSignalGenerator(stock_code)
    tsg.fetch_stock_data()
    
    # 2. 获取计算逻辑
    res = tsg.calculate_logic(cost_price)
    
    if not res or tsg.stock_data is None:
        print(f"❌ 无法获取股票 {stock_code} 的数据，请检查网络或代码。")
        return

    # 3. 补全技术指标
    df = tsg.stock_data
    low_160 = df['最低'].min()
    high_160 = df['最高'].max()
    curr_price = df['收盘'].iloc[-1]
    
    # 计算位阶
    position_pct = round((curr_price - low_160) / (high_160 - low_160) * 100, 1) if high_160 != low_160 else 50
    
    # 计算近期支撑与阻力
    support = df['最低'].tail(10).min()
    # 关键修改：如果现价已经接近或超过近期高点，阻力位应向上看高一线（天空才是尽头）
    resistance_raw = df['最高'].tail(10).max()
    
    # 判断是否为突破形态
    is_breakout = False
    status_desc = "通道内震荡"
    
    if curr_price >= resistance_raw * 0.99:
        is_breakout = True
        status_desc = "🔥 强势突破/主升浪阶段"
        resistance = "上方无套牢盘 (天空)"
    else:
        resistance = resistance_raw

    name = get_stock_name(stock_code)
    
    # --- 打印诊断结果 ---
    print(f"\n🚀 [AI 深度个股诊断] {name}({stock_code})")
    print(f"   状态: {status_desc}")
    print(f"   现价: {res['price']} | 位阶: {position_pct}%")
    print(f"   支撑: {support} | 阻力: {resistance}")
    print("-" * 70)
    
    # --- 持仓管理建议 ---
    if cost_price:
        profit = (res['price'] / float(cost_price) - 1) * 100
        print(f"🏮 【持仓建议】")
        print(f"   >>> 当前成本: {cost_price} | 当前盈亏: {profit:.2f}%")
        print(f"   >>> 建议止盈参考: {res['target']} | 动态止损线: {res['stop_loss']}")
    else:
        print(f"💡 【持仓管理提示】")
        print(f"   >>> 若需针对性卖出建议，请带参数运行: --cost [你的成本价]")
    
    print("-" * 70)
    print(f"🎯 【交易参考】")
    print(f"   >>> 当日建议买入委托价: {res['entrust_buy']}")
    print(f"   >>> 止盈目标: {res['target']} | 止损参考: {res['stop_loss']}")
    print("-" * 70)

    # 4. 调用 DeepSeek 专家点评
    print("🧠 DeepSeek 专家点评：")
    llm = FreeLLMClient()
    
    # 构造更聪明的提示词，解决“恐高”问题
    if is_breakout:
        strategy_hint = "该股处于强势突破阶段，位阶较高是正常的动量特征。请重点分析上涨空间的持续性，不要仅仅因为位阶高就建议卖出。重点关注是否为真突破。"
    else:
        strategy_hint = "该股处于震荡区间，请基于支撑阻力位给出高抛低吸建议。"

    diagnose_prompt = f"""
    请对 {name}({stock_code}) 进行专家级简评。
    【技术数据】：现价{res['price']}, 历史位阶{position_pct}%, 近期支撑{support}。
    【形态判断】：{status_desc}。
    【特别指示】：{strategy_hint}
    
    请输出：
    1. 【{name}走势研判】：分析是主升浪开启还是顶部风险。
    2. 【操作策略】：针对激进型（追涨）和稳健型（回调买）投资者的不同建议。
    """
    
    analysis = llm._call_llm(diagnose_prompt)
    if analysis:
        print(analysis)
    else:
        print("   >>> 暂时无法获取 AI 点评，请检查 API 配置。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A股个股深度诊断工具')
    parser.add_argument('--code', type=str, required=True, help='股票代码，如 002498')
    parser.add_argument('--cost', type=float, help='持仓成本价')
    args = parser.parse_args()
    
    analyze_single_stock(args.code, args.cost)