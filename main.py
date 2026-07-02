"""
AllenTrader v2 - 量化交易系统入口

用法:
    python main.py fetch --symbol sh600519    # 拉取数据
    python main.py backtest --symbol 600519    # 回测
    python main.py report --symbol 600519      # 生成报告
    python main.py watch --symbols 600519,000858  # 盯盘
    python main.py serve                       # 启动Web服务
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


def cmd_fetch(args):
    """拉取行情数据"""
    from data.feeds import DataFeed
    symbol = args.symbol

    print(f'📡 拉取 {symbol} 行情...')
    feed = DataFeed()

    if args.market == 'a':
        df = feed.get_a_share_daily(symbol, start_date=args.start, end_date=args.end)
    elif args.market == 'us':
        df = feed.get_us_daily(symbol, months=args.months)
    else:
        print('不支持的market类型')
        return

    print(f'✅ 获取 {len(df)} 条数据')
    print(df.tail(5))
    df.to_csv(f'/tmp/{symbol}_data.csv')
    print(f'💾 已保存到 /tmp/{symbol}_data.csv')


def cmd_realtime(args):
    """实时行情"""
    from data.feeds import DataFeed
    data = DataFeed.get_realtime(args.symbol, market=args.market)
    for k, v in data.items():
        print(f'  {k}: {v}')


def cmd_backtest(args):
    """回测"""
    from data.feeds import DataFeed
    from backtest import BacktestEngine
    from strategy import TrendStrategy

    print(f'🔬 回测 {args.symbol}...')

    # 获取数据
    df = DataFeed.get_a_share_daily(args.symbol, start_date=args.start, end_date=args.end)

    # 运行回测
    engine = BacktestEngine(initial_cash=args.cash)
    strategy = TrendStrategy()
    result = engine.run(df, strategy)

    print('\n📊 回测结果:')
    print(result.summary())
    print(f'\n交易明细: {len(result.trades)} 笔')


def cmd_report(args):
    """生成报告"""
    from data.feeds import DataFeed
    from reports import ReportGenerator

    print(f'📝 生成 {args.symbol} 报告...')

    data = DataFeed.get_realtime(args.symbol, market=args.market)
    gen = ReportGenerator()

    url = gen.create_html(
        title=f'{data.get("name", args.symbol)} 行情报告',
        kpis=[
            {'label': '最新价', 'value': str(data.get('price', 'N/A')),
             'trend': 'up' if data.get('change_pct', 0) > 0 else 'down'},
            {'label': '涨跌幅', 'value': f'{data.get("change_pct", 0):+.2f}%',
             'sub': f'成交 {data.get("volume", 0):,}'},
            {'label': '市盈率', 'value': str(data.get('pe', 'N/A'))},
            {'label': '52周区间', 'value': f'{data.get("low_52w")}-{data.get("high_52w")}'},
        ],
        sections=[{
            'title': '行情概览',
            'content': f'''
            <table>
            <tr><th>指标</th><th>数值</th></tr>
            <tr><td>开盘</td><td>{data.get("prev_close", "N/A")}</td></tr>
            <tr><td>最高</td><td>{data.get("high", "N/A")}</td></tr>
            <tr><td>最低</td><td>{data.get("low", "N/A")}</td></tr>
            </table>'''
        }]
    )

    print(f'✅ 报告已生成: {url}')


def cmd_serve(args):
    """启动Web服务"""
    import subprocess
    print('🚀 启动 Web 服务...')
    subprocess.run([
        sys.executable, '-m', 'web.app',
        '--host', args.host, '--port', str(args.port)
    ])


def main():
    parser = argparse.ArgumentParser(description='AllenTrader v2')
    sub = parser.add_subparsers(dest='command')

    # fetch
    p = sub.add_parser('fetch', help='拉取行情数据')
    p.add_argument('--symbol', '-s', required=True)
    p.add_argument('--market', '-m', default='a', choices=['a', 'us', 'hk'])
    p.add_argument('--start', default=None)
    p.add_argument('--end', default=None)
    p.add_argument('--months', type=int, default=6)

    # realtime
    p = sub.add_parser('realtime', help='实时行情')
    p.add_argument('--symbol', '-s', required=True)
    p.add_argument('--market', '-m', default='a', choices=['a', 'us', 'hk'])

    # backtest
    p = sub.add_parser('backtest', help='回测')
    p.add_argument('--symbol', '-s', required=True)
    p.add_argument('--start', default='20250601')
    p.add_argument('--end', default='20260630')
    p.add_argument('--cash', type=float, default=100000)

    # report
    p = sub.add_parser('report', help='生成报告')
    p.add_argument('--symbol', '-s', required=True)
    p.add_argument('--market', '-m', default='a', choices=['a', 'us', 'hk'])

    # serve
    p = sub.add_parser('serve', help='启动Web服务')
    p.add_argument('--host', default='0.0.0.0')
    p.add_argument('--port', type=int, default=8080)

    args = parser.parse_args()

    if args.command == 'fetch':
        cmd_fetch(args)
    elif args.command == 'realtime':
        cmd_realtime(args)
    elif args.command == 'backtest':
        cmd_backtest(args)
    elif args.command == 'report':
        cmd_report(args)
    elif args.command == 'serve':
        cmd_serve(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
