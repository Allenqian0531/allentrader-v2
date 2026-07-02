"""
AllenTrader v2 — 量化交易系统

用法:
    python main.py run 600519                    # 一键回测 + 优化 + 报告
    python main.py backtest 600519               # 单独回测
    python main.py optimize 600519               # 参数优化
    python main.py data 600519                   # 拉取数据
    python main.py chart 600519                  # 技术图表
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(__file__))


def cmd_data(args):
    """拉取行情"""
    from data.feeds import DataFeed
    feed = DataFeed()
    df = feed.get_a_share_daily(args.symbol, start_date=args.start, end_date=args.end)
    print(f'{args.symbol}: {len(df)} 条')
    print(df.tail(5).to_string())
    if args.output:
        df.to_csv(args.output)
        print(f'→ {args.output}')


def cmd_backtest(args):
    """回测"""
    from backtest.engine import run_backtest, print_result
    from strategy.trend_breakout import TrendBreakout

    print(f'🔬 回测 {args.symbol} 趋势线突破策略...\n')
    result = run_backtest(
        args.symbol, TrendBreakout,
        start=args.start, end=args.end, cash=args.cash,
    )
    print_result(result)


def cmd_optimize(args):
    """参数优化"""
    from backtest.engine import optimize
    from strategy.trend_breakout import TrendBreakout

    param_grid = {
        'confirm_bars': [1, 2, 3],
        'min_bars': [20, 30, 60],
    }

    print(f'🔍 参数优化 {args.symbol}...')
    print(f'   搜索空间: {param_grid}\n')

    results = optimize(
        args.symbol, TrendBreakout, param_grid,
        start=args.start, end=args.end, cash=args.cash,
    )

    print(f'{"排名":<4} {"confirm_bars":<14} {"min_bars":<10} {"收益":<10} {"超额":<10} {"回撤":<8} {"交易":<6}')
    print('-' * 65)
    for i, r in enumerate(results[:10]):
        p = r['params']
        print(f'{i+1:<4} {p["confirm_bars"]:<14} {p["min_bars"]:<10} '
              f'{r["return_pct"]:>+7.2f}%  {r["excess_return"]:>+7.2f}%  '
              f'{r["max_drawdown"]:>6.2f}%  {r["total_trades"]:>4}')


def cmd_chart(args):
    """生成技术图表"""
    import subprocess
    script = os.path.join(os.path.dirname(__file__),
                          'scripts', 'generate_moutai_chart.py')
    subprocess.run([sys.executable, script])


def cmd_run(args):
    """一键全流程：回测 → 优化 → 报告"""
    from backtest.engine import run_backtest, print_result, optimize
    from strategy.trend_breakout import TrendBreakout
    from reports.generator import generate_report

    symbol = args.symbol
    print(f'╔══════════════════════════════════════╗')
    print(f'║  AllenTrader v2 · 全流程             ║')
    print(f'║  标的: {symbol:<28} ║')
    print(f'╚══════════════════════════════════════╝\n')

    # 1. 回测
    print('▶ 阶段 1/3: 回测')
    result = run_backtest(symbol, TrendBreakout,
                          start=args.start, end=args.end, cash=args.cash)
    print_result(result)

    # 2. 优化
    print('▶ 阶段 2/3: 参数优化')
    param_grid = {'confirm_bars': [1, 2, 3], 'min_bars': [20, 30, 60]}
    opt_results = optimize(symbol, TrendBreakout, param_grid,
                           start=args.start, end=args.end, cash=args.cash)
    best = opt_results[0]
    print(f'  最优参数: {best["params"]}')
    print(f'  最优超额收益: {best["excess_return"]:+.2f}%\n')

    # 3. 报告
    print('▶ 阶段 3/3: 生成报告')
    report_path = generate_report(result, symbol=symbol,
                                  strategy_name='趋势线突破')
    print(f'  ✅ 报告已保存')
    print(f'  📄 {report_path}')
    print(f'  🌐 http://allenqian.online/reports/{os.path.basename(report_path)}')

    print(f'\n╔══════════════════════════════════════╗')
    print(f'║  ✅ 全流程完成                       ║')
    print(f'╚══════════════════════════════════════╝')


def cmd_live(args):
    """实盘交易（未实现）"""
    print('⚠️ 实盘交易待 QMT 对接。')
    print('   Broker 接口已就绪: live/broker.py')


def main():
    parser = argparse.ArgumentParser(description='AllenTrader v2')
    sub = parser.add_subparsers(dest='command')

    # data
    p = sub.add_parser('data', help='拉取行情')
    p.add_argument('symbol')
    p.add_argument('--start', default=None)
    p.add_argument('--end', default=None)
    p.add_argument('--output', '-o', default=None)

    # backtest
    p = sub.add_parser('backtest', help='回测')
    p.add_argument('symbol')
    p.add_argument('--start', default='20250101')
    p.add_argument('--end', default='20260701')
    p.add_argument('--cash', type=float, default=1_000_000)

    # optimize
    p = sub.add_parser('optimize', help='参数优化')
    p.add_argument('symbol')
    p.add_argument('--start', default='20250101')
    p.add_argument('--end', default='20260701')
    p.add_argument('--cash', type=float, default=1_000_000)

    # run (全流程)
    p = sub.add_parser('run', help='一键全流程')
    p.add_argument('symbol')
    p.add_argument('--start', default='20250101')
    p.add_argument('--end', default='20260701')
    p.add_argument('--cash', type=float, default=1_000_000)

    # chart
    p = sub.add_parser('chart', help='技术图表')
    p.add_argument('symbol', nargs='?', default='600519')

    # live
    p = sub.add_parser('live', help='实盘 (待 QMT)')
    p.add_argument('symbol')

    args = parser.parse_args()

    cmds = {
        'data': cmd_data,
        'backtest': cmd_backtest,
        'optimize': cmd_optimize,
        'run': cmd_run,
        'chart': cmd_chart,
        'live': cmd_live,
    }

    if args.command in cmds:
        cmds[args.command](args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
