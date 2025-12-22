import argparse
from trading_signal import TradingSignalGenerator
from llm_client import FreeLLMClient
from config import *
import json

def analyze_single_stock(stock_code: str):
    """单只股票详细分析（含LLM报告）"""
    print(f"🚀 正在分析股票：{stock_code}")
    print("="*50)
    
    try:
        # 1. 初始化工具
        signal_generator = TradingSignalGenerator(stock_code)
        llm_client = FreeLLMClient()
        
        # 2. 获取基础数据
        signal_generator.fetch_stock_data()
        latest_price = signal_generator.latest_price
        
        # 3. 计算关键指标
        ma_data = signal_generator.calculate_ma()
        support_resistance = signal_generator.calculate_support_resistance()
        rsi = signal_generator.calculate_rsi()
        
        # 4. 生成交易信号
        default_params = {"short_ma":5, "long_ma":20, "support_days":5, "buy_margin":0.01}
        trading_signal = signal_generator.generate_signal(default_params)
        
        # 5. 调用LLM生成详细分析报告
        stock_data_for_llm = {
            "code": stock_code,
            "name": get_stock_name(stock_code),
            "close": round(latest_price, 2),
            "5d_change": round((signal_generator.stock_data.iloc[-1]['收盘'] / signal_generator.stock_data.iloc[-6]['开盘'] - 1) * 100, 2),
            "avg_volume": round(signal_generator.stock_data['成交额'].tail(5).mean() / 10000, 2),
            "market_cap": get_stock_market_cap(stock_code),
            "score": calculate_stock_score(signal_generator)
        }
        
        strategy_params_for_llm = {
            "short_ma": default_params['short_ma'],
            "long_ma": default_params['long_ma'],
            "support": support_resistance['支撑位'],
            "resistance": support_resistance['阻力位'],
            "buy_margin": default_params['buy_margin'],
            "stop_loss": round(support_resistance['支撑位'] * 0.985, 2),
            "target_price": round(support_resistance['阻力位'] * 1.02, 2)
        }
        
        llm_analysis = llm_client.generate_stock_analysis(stock_data_for_llm, strategy_params_for_llm)
        
        # 6. 输出分析结果
        print("\n📊 基础指标分析：")
        print(f"当前价格：{latest_price:.2f}元")
        print(f"近30天均线：短期{ma_data.iloc[-1]['short_ma']:.2f}元 | 长期{ma_data.iloc[-1]['long_ma']:.2f}元")
        print(f"支撑位：{support_resistance['支撑位']:.2f}元 | 阻力位：{support_resistance['阻力位']:.2f}元")
        print(f"RSI指标：{rsi}（30-70为合理区间）")
        print(f"交易信号：{trading_signal['信号类型']} | 信号原因：{trading_signal['信号原因']}")
        
        print(f"\n🤖 LLM详细分析报告：")
        print(llm_analysis)
        
        print(f"\n💡 操作建议：")
        print(f"买入区间：{strategy_params_for_llm['support']:.2f} - {latest_price:.2f}元")
        print(f"止损价：{strategy_params_for_llm['stop_loss']:.2f}元（跌破立即卖出）")
        print(f"目标价：{strategy_params_for_llm['target_price']:.2f}元（预期收益2%）")
        print(f"持仓比例：建议不超过总资金的{SINGLE_STOCK_RATIO*100:.2f}%")
        
        # 7. 保存分析报告
        report = {
            "股票代码": stock_code,
            "股票名称": stock_data_for_llm['name'],
            "分析日期": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "基础指标": {
                "当前价格": round(latest_price, 2),
                "支撑位": support_resistance['支撑位'],
                "阻力位": support_resistance['阻力位'],
                "RSI指标": rsi,
                "均线状态": "多头排列" if ma_data.iloc[-1]['short_ma'] > ma_data.iloc[-1]['long_ma'] else "空头排列"
            },
            "交易信号": trading_signal,
            "LLM分析报告": llm_analysis,
            "操作建议": {
                "买入区间": f"{strategy_params_for_llm['support']:.2f} - {latest_price:.2f}元",
                "止损价": strategy_params_for_llm['stop_loss'],
                "目标价": strategy_params_for_llm['target_price'],
                "持仓比例限制": f"≤{SINGLE_STOCK_RATIO*100:.2f}%"
            }
        }
        
        with open(f"strategy_log/single_stock_analysis_{stock_code}_{datetime.now().strftime('%Y%m%d')}.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 分析报告已保存至：strategy_log/single_stock_analysis_{stock_code}_{datetime.now().strftime('%Y%m%d')}.json")
        
    except Exception as e:
        print(f"\n❌ 分析失败：{str(e)}")

def get_stock_name(stock_code: str) -> str:
    """获取股票名称"""
    try:
        stock_spot = ak.stock_zh_a_spot()
        stock_info = stock_spot[stock_spot['代码'] == stock_code]
        return stock_info.iloc[0]['名称'] if not stock_info.empty else "未知股票"
    except:
        return "未知股票"

def get_stock_market_cap(stock_code: str) -> float:
    """获取股票市值"""
    try:
        stock_spot = ak.stock_zh_a_spot()
        stock_info = stock_spot[stock_spot['代码'] == stock_code]
        return round(pd.to_numeric