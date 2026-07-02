"""
回测引擎 — backtrader.cerebro 封装

用法:
    from backtest.engine import run_backtest
    from strategy.trend_breakout import TrendBreakout

    result = run_backtest('600519', TrendBreakout, start='20250701', end='20260702')
"""
import backtrader as bt
from core.data_feed import load_bt_data


def run_backtest(symbol: str, strategy_cls,
                 start: str = None, end: str = None,
                 cash: float = 1_000_000.0,
                 commission: float = 0.0003,
                 **strategy_kwargs) -> dict:
    """
    运行回测

    Args:
        symbol: 标的代码 (如 '600519')
        strategy_cls: 策略类 (继承 BaseStrategy)
        start/end: 日期范围
        cash: 初始资金
        commission: 佣金费率
        **strategy_kwargs: 传给策略的额外参数

    Returns:
        {
            'final_value': float,
            'return_pct': float,
            'benchmark_return': float,
            'excess_return': float,
            'max_drawdown': float,
            'total_trades': int,
            'won': int,
            'lost': int,
            'trades': [(entry_date, exit_date, pnl), ...]
        }
    """
    data = load_bt_data(symbol, start=start, end=end)
    df_raw = data._dataname if hasattr(data, '_dataname') else data.p.dataname

    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.addstrategy(strategy_cls, **strategy_kwargs)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

    cerebro.broker.setcash(cash)
    cerebro.broker.setcommission(commission=commission)

    start_val = cerebro.broker.getvalue()
    results = cerebro.run()
    final_val = cerebro.broker.getvalue()

    strat = results[0]
    ta = strat.analyzers.trades.get_analysis()
    dd = strat.analyzers.drawdown.get_analysis()
    ret_analyzer = strat.analyzers.returns.get_analysis()

    total = ta.get('total', {}).get('total', 0)
    won = ta.get('won', {}).get('total', 0)
    lost = ta.get('lost', {}).get('total', 0)
    max_dd = dd.get('max', {}).get('drawdown', 0)

    ret_pct = (final_val - start_val) / start_val * 100

    # 买入持有收益
    bench_ret = (df_raw['close'].iloc[-1] - df_raw['close'].iloc[0]) / df_raw['close'].iloc[0] * 100

    return {
        'final_value': final_val,
        'return_pct': round(ret_pct, 2),
        'benchmark_return': round(bench_ret, 2),
        'excess_return': round(ret_pct - bench_ret, 2),
        'max_drawdown': round(max_dd, 2),
        'total_trades': total,
        'won': won,
        'lost': lost,
        'annual_return': ret_analyzer.get('rnorm100', 0),
    }


def print_result(result: dict):
    """格式化打印回测结果"""
    print(f"""
╔══════════════════════════════╗
║         回 测 结 果          ║
╠══════════════════════════════╣
║ 策略收益:  {result['return_pct']:>8.2f}%         ║
║ 基准收益:  {result['benchmark_return']:>8.2f}%         ║
║ 超额收益:  {result['excess_return']:>8.2f}%         ║
║ 最大回撤:  {result['max_drawdown']:>8.2f}%         ║
║ 总交易:    {result['total_trades']:>8} 笔         ║
║ 胜率:      {result['won']}/{result['total_trades']}                 ║
╚══════════════════════════════╝
""")


def optimize(symbol: str, strategy_cls,
             param_grid: dict,
             start: str = None, end: str = None,
             cash: float = 1_000_000.0,
             metric: str = 'excess_return') -> list:
    """
    参数网格搜索

    Args:
        symbol: 标的
        strategy_cls: 策略类
        param_grid: {param_name: [v1, v2, ...]}
        start/end: 日期
        cash: 初始资金
        metric: 排序指标

    Returns:
        [{params, result}, ...] 按 metric 降序
    """
    data = load_bt_data(symbol, start=start, end=end)
    df_raw = data._dataname if hasattr(data, '_dataname') else data.p.dataname

    cerebro = bt.Cerebro(optreturn=False)
    cerebro.adddata(data)

    # 动态添加策略优化参数
    cerebro.optstrategy(strategy_cls, **param_grid)

    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.broker.setcash(cash)
    cerebro.broker.setcommission(commission=0.0003)

    start_val = cerebro.broker.getvalue()
    bench_ret = (df_raw['close'].iloc[-1] - df_raw['close'].iloc[0]) / df_raw['close'].iloc[0] * 100

    all_results = []
    for opt in cerebro.run():
        final_val = cerebro.broker.getvalue()
        ret_pct = (final_val - start_val) / start_val * 100

        strat = opt[0]
        ta = strat.analyzers.trades.get_analysis()
        dd = strat.analyzers.drawdown.get_analysis()

        result = {
            'params': {k: getattr(strat.params, k) for k in param_grid},
            'return_pct': round(ret_pct, 2),
            'excess_return': round(ret_pct - bench_ret, 2),
            'max_drawdown': round(dd.get('max', {}).get('drawdown', 0), 2),
            'total_trades': ta.get('total', {}).get('total', 0),
        }
        all_results.append(result)

    all_results.sort(key=lambda x: x[metric], reverse=True)
    return all_results
