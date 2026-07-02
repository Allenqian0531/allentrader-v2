"""
回测报告生成器
复用现有 reports/generator.py 的 HTML 结构
"""
import os
from datetime import datetime


def generate_report(result: dict, symbol: str = '',
                    strategy_name: str = '',
                    output_dir: str = None) -> str:
    """
    生成回测 HTML 报告

    Returns:
        file path
    """
    if output_dir is None:
        output_dir = '/home/admin/sites/allenqian.online/reports'
    os.makedirs(output_dir, exist_ok=True)

    trend_cls = 'good' if result['excess_return'] > 0 else 'warn'

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{symbol} 回测报告 | {strategy_name}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0d1117;color:#c9d1d9;font-family:-apple-system,BlinkMacSystemFont,"Microsoft YaHei",sans-serif;line-height:1.6}}
.container{{max-width:800px;margin:0 auto;padding:30px 20px}}
.header{{background:linear-gradient(135deg,#1a1f35,#0d1117);border:1px solid #21262d;border-radius:14px;padding:28px 32px;margin-bottom:24px}}
.header h1{{font-size:24px;color:#f0f6fc}}
.header .meta{{color:#8b949e;font-size:13px;margin-top:6px}}
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:24px}}
.kpi{{background:#161b22;border:1px solid #21262d;border-radius:10px;padding:14px}}
.kpi .l{{font-size:11px;color:#8b949e;margin-bottom:4px}}
.kpi .v{{font-size:22px;font-weight:700;color:#f0f6fc}}
.kpi .s{{font-size:10px;color:#8b949e;margin-top:2px}}
.kpi.warn .v{{color:#ef4444}}
.kpi.good .v{{color:#22c55e}}
.section{{background:#161b22;border:1px solid #21262d;border-radius:10px;padding:24px;margin-bottom:20px}}
.section h2{{font-size:18px;color:#e6edf3;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid #21262d}}
.section table{{width:100%;border-collapse:collapse}}
.section th{{background:#21262d;color:#8b949e;text-align:left;padding:8px 12px;font-size:11px}}
.section td{{padding:8px 12px;border-bottom:1px solid #1a1f2e;font-size:13px}}
.tag{{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:500}}
.t-r{{background:rgba(239,68,68,0.12);color:#ef4444}}
.t-g{{background:rgba(34,197,94,0.12);color:#22c55e}}
.t-y{{background:rgba(245,158,11,0.12);color:#f59e0b}}
.footer{{text-align:center;color:#484f58;font-size:11px;margin-top:30px;padding-top:20px;border-top:1px solid #21262d}}
</style></head>
<body>
<div class="container">
<div class="header">
    <h1>{symbol} · {strategy_name} 回测报告</h1>
    <div class="meta">{datetime.now().strftime('%Y-%m-%d %H:%M')} · AllenTrader v2</div>
</div>

<div class="kpi-grid">
    <div class="kpi"><div class="l">策略收益</div><div class="v" style="color:{'#22c55e' if result['return_pct']>0 else '#ef4444'}">{result['return_pct']:+.2f}%</div></div>
    <div class="kpi"><div class="l">基准收益</div><div class="v">{result['benchmark_return']:+.2f}%</div></div>
    <div class="kpi {trend_cls}"><div class="l">超额收益</div><div class="v">{result['excess_return']:+.2f}%</div></div>
    <div class="kpi"><div class="l">最大回撤</div><div class="v" style="color:#f59e0b">{result['max_drawdown']:.2f}%</div></div>
    <div class="kpi"><div class="l">交易次数</div><div class="v">{result['total_trades']}</div></div>
    <div class="kpi"><div class="l">胜率</div><div class="v">{result['won']}/{result['total_trades']}</div></div>
</div>

<div class="section">
    <h2>策略参数</h2>
    <table>
        <tr><th>参数</th><th>值</th></tr>
        <tr><td>标的</td><td>{symbol}</td></tr>
        <tr><td>策略</td><td>{strategy_name}</td></tr>
        <tr><td>初始资金</td><td>¥1,000,000</td></tr>
    </table>
</div>

<div class="section">
    <h2>技术研判</h2>
    <p style="font-size:13px;color:#8b949e;line-height:1.8">
    策略在下跌行情中主要通过<span class="tag t-g">空仓观望</span>规避主跌浪。
    当前最大回撤 <span class="tag t-y">{result['max_drawdown']}%</span>，
    超额收益 <span class="tag {'t-g' if result['excess_return']>0 else 't-r'}">{result['excess_return']:+.2f}%</span>。
    </p>
</div>

<div class="footer">AllenTrader v2 · 基于 backtrader · 不构成投资建议</div>
</div>
</body></html>'''

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'bt_{symbol}_{ts}.html'
    path = os.path.join(output_dir, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    return path
