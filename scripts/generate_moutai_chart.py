#!/usr/bin/env python3
"""
茅台技术图表生成器 v2
- 下降趋势线从区间最高点开始
- 上升趋势线从区间最低点开始
- K线图 + 下方成交量柱状图
"""
import numpy as np
import os, sys
from datetime import datetime

sys.path.insert(0, '/home/admin/allentrader-v2')
from data.feeds import DataFeed

# ============================================================
# 1. 拉取数据
# ============================================================
print("📡 拉取数据...")
df = DataFeed.get_a_share_daily('600519', start_date='20250701', end_date='20260702')
dates = df.index.tolist()
opens = df['open'].values.astype(float)
highs = df['high'].values.astype(float)
lows = df['low'].values.astype(float)
closes = df['close'].values.astype(float)
volumes = df['volume'].values.astype(float)
n = len(dates)
print(f"✅ {n} 条数据, {dates[0].strftime('%Y-%m-%d')} ~ {dates[-1].strftime('%Y-%m-%d')}")

# ============================================================
# 2. 趋势线识别
#    - 下降线: 从区间最高点出发，连接后续更低高点
#    - 上升线: 从区间最低点出发，连接后续更高低点
#    验证: 全区间(起点→今天)不被突破/跌破
# ============================================================
log_h = np.log(highs + 1e-10)
log_l = np.log(lows + 1e-10)

def find_down_lines():
    """下降趋势线: 从全局最高点出发，首尾相连；最后一条可接受被突破"""
    peak_idx = int(np.argmax(highs))
    if peak_idx >= n - 3:
        return []

    result = []
    current_start = peak_idx

    while current_start < n - 3:
        # 从 current_start 出发，找所有有效的更低高点
        best = None
        for end in range(current_start + 3, n):
            if log_h[end] >= log_h[current_start]:
                continue
            slope = (log_h[end] - log_h[current_start]) / (end - current_start)
            intercept = log_h[current_start] - slope * current_start
            valid = True
            for i in range(current_start, end + 1):
                line_val = slope * i + intercept
                if log_h[i] > line_val + 0.005:
                    valid = False
                    break
            if valid:
                # 取跨度最大的
                if best is None or (end - current_start) > (best['end_idx'] - current_start):
                    best = {
                        'start_idx': current_start, 'end_idx': end,
                        'slope': slope, 'intercept': intercept,
                        'length': end - current_start
                    }
        if best is None:
            break
        result.append(best)
        current_start = best['end_idx']  # 首尾相连

    if not result:
        return []

    # 前向验证：除最后一条外
    final = []
    last_idx = len(result) - 1
    for i, c in enumerate(result):
        if i == last_idx:
            final.append(c)
        else:
            ok = True
            for j in range(c['end_idx'] + 1, n):
                line_val = c['slope'] * j + c['intercept']
                if log_h[j] > line_val + 0.005:
                    ok = False
                    break
            if ok:
                final.append(c)
    return final

def find_up_lines():
    """上升趋势线: 从全局最低点出发，首尾相连；最后一条可接受被跌破"""
    trough_idx = int(np.argmin(lows))
    if trough_idx >= n - 3:
        return []

    result = []
    current_start = trough_idx

    while current_start < n - 3:
        best = None
        for end in range(current_start + 3, n):
            if log_l[end] <= log_l[current_start]:
                continue
            slope = (log_l[end] - log_l[current_start]) / (end - current_start)
            intercept = log_l[current_start] - slope * current_start
            valid = True
            for i in range(current_start, end + 1):
                line_val = slope * i + intercept
                if log_l[i] < line_val - 0.005:
                    valid = False
                    break
            if valid:
                if best is None or (end - current_start) > (best['end_idx'] - current_start):
                    best = {
                        'start_idx': current_start, 'end_idx': end,
                        'slope': slope, 'intercept': intercept,
                        'length': end - current_start
                    }
        if best is None:
            break
        result.append(best)
        current_start = best['end_idx']  # 首尾相连

    if not result:
        return []

    # 前向验证：除最后一条外
    final = []
    last_idx = len(result) - 1
    for i, c in enumerate(result):
        if i == last_idx:
            final.append(c)
        else:
            ok = True
            for j in range(c['end_idx'] + 1, n):
                line_val = c['slope'] * j + c['intercept']
                if log_l[j] < line_val - 0.005:
                    ok = False
                    break
            if ok:
                final.append(c)
    return final

print("🔍 识别趋势线...")
down_lines = find_down_lines()
up_lines = find_up_lines()

print(f"  下降趋势线: {len(down_lines)} 条")
for i, dl in enumerate(down_lines):
    tag = " [最后一条,可能已被突破]" if i == len(down_lines) - 1 else ""
    print(f"    {i+1}. 起点 {dates[dl['start_idx']].strftime('%Y-%m-%d')}({highs[dl['start_idx']]:.0f}) → "
          f"终点 {dates[dl['end_idx']].strftime('%Y-%m-%d')}({highs[dl['end_idx']]:.0f}), "
          f"跨度{dl['length']}天{tag}")
print(f"  上升趋势线: {len(up_lines)} 条")
for i, ul in enumerate(up_lines):
    tag = " [最后一条,可能已被跌破]" if i == len(up_lines) - 1 else ""
    print(f"    {i+1}. 起点 {dates[ul['start_idx']].strftime('%Y-%m-%d')}({lows[ul['start_idx']]:.0f}) → "
          f"终点 {dates[ul['end_idx']].strftime('%Y-%m-%d')}({lows[ul['end_idx']]:.0f}), "
          f"跨度{ul['length']}天{tag}")

# ============================================================
# 3. 均线
# ============================================================
def calc_ma(arr, period):
    result = np.full(len(arr), np.nan)
    for i in range(period - 1, len(arr)):
        result[i] = np.mean(arr[i - period + 1:i + 1])
    return result

ma20 = calc_ma(closes, 20)
ma60 = calc_ma(closes, 60)

# ============================================================
# 4. SVG 图表
# ============================================================
print("🎨 生成 SVG...")

price_min, price_max = np.log(1080), np.log(1570)
log_range = price_max - price_min

# 布局参数
ML, MR = 80, 30           # 左右边距
CW = 1060                  # 画布宽
CH = 700                   # 画布高

# K线区域 (上)
KT, KB = 10, 520
KH = KB - KT

# 成交量区域 (下)
VT, VB = 530, 690
VH = VB - VT

x_scale = (CW - ML - MR) / (n - 1)
candle_w = max(2, x_scale * 0.7)

def px(i):
    """K线索引 → X坐标"""
    return ML + i * x_scale

def py(p):
    """价格 → Y坐标 (对数映射)"""
    return KB - (np.log(p + 1e-10) - price_min) / log_range * KH

# 月份刻度
month_ticks = []
prev_m = None
for i, d in enumerate(dates):
    ms = d.strftime('%m月')
    if ms != prev_m:
        month_ticks.append((i, ms))
        prev_m = ms

# 价格标签
price_labels = [1100, 1150, 1200, 1250, 1300, 1350, 1400, 1450, 1500, 1550]

vol_max = np.max(volumes) * 1.05

# 构建 SVG
svg = []
sv = svg.append

sv(f'<svg viewBox="0 0 {CW} {CH}" width="100%" xmlns="http://www.w3.org/2000/svg">')
sv(f'<rect width="{CW}" height="{CH}" fill="#0d1117" rx="10"/>')

# ── K 线图 ──
# 网格 + 价格标签
for p in price_labels:
    y = py(p)
    if KT <= y <= KB:
        sv(f'<line x1="{ML}" y1="{y:.1f}" x2="{CW-MR}" y2="{y:.1f}" stroke="#1a1f2e" stroke-width="0.5"/>')
        sv(f'<text x="{ML-8}" y="{y+4:.1f}" fill="#555" font-size="10" text-anchor="end">{p}</text>')

# 月份标签
for idx, label in month_ticks:
    x = px(idx)
    if ML <= x <= CW - MR:
        sv(f'<text x="{x:.1f}" y="{KB+18}" fill="#555" font-size="10" text-anchor="middle">{label}</text>')

# K 线柱子
for i in range(n):
    x = px(i)
    oy, cy, hy, ly = py(opens[i]), py(closes[i]), py(highs[i]), py(lows[i])
    color = '#22c55e' if closes[i] >= opens[i] else '#ef4444'
    bt = min(oy, cy)
    bh = max(abs(cy - oy), 0.8)
    w_top = min(hy, ly)
    w_h = max(abs(hy - ly), 0.8)
    sv(f'<line x1="{x:.1f}" y1="{w_top:.1f}" x2="{x:.1f}" y2="{w_top+w_h:.1f}" stroke="{color}" stroke-width="0.6"/>')
    sv(f'<rect x="{x-candle_w/2:.1f}" y="{bt:.1f}" width="{candle_w:.1f}" height="{bh:.1f}" fill="{color}" rx="0.5"/>')

# 均线
for ma_arr, color, name in [(ma20, '#f59e0b', 'MA20'), (ma60, '#8b5cf6', 'MA60')]:
    pts = []
    for i in range(len(ma_arr)):
        if not np.isnan(ma_arr[i]):
            pts.append(f'{px(i):.1f},{py(ma_arr[i]):.1f}')
    if pts:
        sv(f'<polyline points="{" L".join(pts)}" fill="none" stroke="{color}" stroke-width="1.2" opacity="0.8"/>')

# 趋势线
for i, dl in enumerate(down_lines):
    is_last = (i == len(down_lines) - 1)
    opacity = '0.55' if is_last else '0.85'
    label = '↓下降(最后一条,可能已突破)' if is_last else '↓下降趋势'
    x1, x2 = px(dl['start_idx']), px(n - 1)
    p1_log = dl['slope'] * dl['start_idx'] + dl['intercept']
    p2_log = dl['slope'] * (n - 1) + dl['intercept']
    y1, y2 = py(np.exp(p1_log)), py(np.exp(p2_log))
    sv(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#ef4444" stroke-width="2" stroke-dasharray="8,4" opacity="{opacity}"/>')
    mx = (x1 + px(dl['end_idx'])) / 2
    my = (y1 + py(np.exp(dl['slope'] * dl['end_idx'] + dl['intercept']))) / 2 + 14
    sv(f'<text x="{mx:.1f}" y="{my:.1f}" fill="#ef4444" font-size="9" font-weight="bold">{label}</text>')

for i, ul in enumerate(up_lines):
    is_last = (i == len(up_lines) - 1)
    opacity = '0.55' if is_last else '0.85'
    label = '↑上升(最后一条,可能已跌破)' if is_last else '↑上升趋势'
    x1, x2 = px(ul['start_idx']), px(n - 1)
    p1_log = ul['slope'] * ul['start_idx'] + ul['intercept']
    p2_log = ul['slope'] * (n - 1) + ul['intercept']
    y1, y2 = py(np.exp(p1_log)), py(np.exp(p2_log))
    sv(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#22c55e" stroke-width="2" stroke-dasharray="8,4" opacity="{opacity}"/>')
    mx = (x1 + px(ul['end_idx'])) / 2
    my = (y1 + py(np.exp(ul['slope'] * ul['end_idx'] + ul['intercept']))) / 2 - 8
    sv(f'<text x="{mx:.1f}" y="{my:.1f}" fill="#22c55e" font-size="9" font-weight="bold">{label}</text>')

# 最新价标记
lp_y = py(closes[-1])
lx = px(n - 1)
sv(f'<line x1="{ML}" y1="{lp_y:.1f}" x2="{CW-MR}" y2="{lp_y:.1f}" stroke="#fff" stroke-width="0.8" stroke-dasharray="4,4" opacity="0.35"/>')
sv(f'<circle cx="{lx:.1f}" cy="{lp_y:.1f}" r="5" fill="#fff" stroke="#0d1117" stroke-width="2"/>')
sv(f'<text x="{lx+8:.1f}" y="{lp_y-7:.1f}" fill="#fff" font-size="13" font-weight="bold">{closes[-1]:.2f}</text>')

# K线边框
sv(f'<line x1="{ML}" y1="{KT}" x2="{ML}" y2="{KB}" stroke="#333" stroke-width="1"/>')
sv(f'<line x1="{ML}" y1="{KB}" x2="{CW-MR}" y2="{KB}" stroke="#333" stroke-width="1"/>')

# ── 成交量柱状图 ──
sv(f'<line x1="{ML}" y1="{VB}" x2="{CW-MR}" y2="{VB}" stroke="#333" stroke-width="1"/>')
for i in range(n):
    x = px(i)
    color = '#22c55e' if closes[i] >= opens[i] else '#ef4444'
    h = (volumes[i] / vol_max) * VH
    y = VB - h
    sv(f'<rect x="{x-candle_w/2:.1f}" y="{y:.1f}" width="{candle_w:.1f}" height="{h:.1f}" fill="{color}" opacity="0.4" rx="0.5"/>')

# 成交量刻度
for pct in [0.25, 0.5, 0.75, 1.0]:
    v = vol_max * pct
    y = VB - pct * VH
    label = f'{v/1e6:.0f}M' if v >= 1e6 else f'{v/1e4:.0f}万'
    sv(f'<line x1="{ML}" y1="{y:.1f}" x2="{CW-MR}" y2="{y:.1f}" stroke="#1a1f2e" stroke-width="0.5"/>')
    sv(f'<text x="{ML-8}" y="{y+4:.1f}" fill="#555" font-size="9" text-anchor="end">{label}</text>')

# 标题 + 轴标签
sv(f'<text x="{ML}" y="{KT-2}" fill="#8b949e" font-size="10">贵州茅台 600519 | 对数坐标 | {dates[0].strftime("%Y-%m-%d")} ~ {dates[-1].strftime("%Y-%m-%d")}</text>')
mid_k = KT + KH/2
mid_v = VT + VH/2
sv(f'<text x="12" y="{mid_k:.1f}" fill="#555" font-size="9" text-anchor="middle" transform="rotate(-90,12,{mid_k:.1f})">价格 (对数)</text>')
sv(f'<text x="12" y="{mid_v:.1f}" fill="#555" font-size="9" text-anchor="middle" transform="rotate(-90,12,{mid_v:.1f})">成交量</text>')
sv('</svg>')

svg_str = '\n'.join(svg)

# ============================================================
# 5. 支撑/压力位 (成交量加权)
# ============================================================
def find_sr():
    peaks, troughs = [], []
    for i in range(1, n - 1):
        if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
            peaks.append((i, highs[i], volumes[i]))
        if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
            troughs.append((i, lows[i], volumes[i]))

    def merge(levels, dist=0.02):
        levels.sort(key=lambda x: -x[1])
        merged = []
        for idx, price, vol in levels:
            if not merged or abs(price - merged[-1][1]) / merged[-1][1] > dist:
                merged.append((idx, price, vol))
        return merged[:4]
    return merge(peaks), merge(troughs)

pressures, supports = find_sr()
avg_vol = np.mean(volumes)

# ============================================================
# 6. KPI
# ============================================================
chg = (closes[-1] - closes[0]) / closes[0] * 100
yh, yl = np.max(highs), np.min(lows)
dd = (yh - closes[-1]) / yh * 100
bounce = (closes[-1] - yl) / yl * 100
change_cls = 'dn' if chg < 0 else 'up'

# ============================================================
# 7. 趋势线文本
# ============================================================
tl_text = ''
if down_lines:
    for i, dl in enumerate(down_lines):
        s = dates[dl['start_idx']].strftime('%Y-%m-%d')
        e = dates[dl['end_idx']].strftime('%Y-%m-%d')
        note = '（最后一条，可能已被突破）' if i == len(down_lines) - 1 else ''
        tl_text += f'下降趋势线：{s}({highs[dl["start_idx"]]:.0f}) → {e}({highs[dl["end_idx"]]:.0f})，跨度{dl["length"]}天{note}； '
if up_lines:
    for i, ul in enumerate(up_lines):
        s = dates[ul['start_idx']].strftime('%Y-%m-%d')
        e = dates[ul['end_idx']].strftime('%Y-%m-%d')
        note = '（最后一条，可能已被跌破）' if i == len(up_lines) - 1 else ''
        tl_text += f'上升趋势线：{s}({lows[ul["start_idx"]]:.0f}) → {e}({lows[ul["end_idx"]]:.0f})，跨度{ul["length"]}天{note}； '
if not tl_text:
    tl_text = '当前无有效趋势线'

ma20_pos = '下方' if closes[-1] < ma20[-1] else '上方'
ma60_pos = '下方' if closes[-1] < ma60[-1] else '上方'

if closes[-1] < ma20[-1] and ma20[-1] < ma60[-1]:
    tech = '空头排列'
    tech_tag = 't-r'
elif abs(closes[-1] - ma20[-1]) / closes[-1] < 0.015:
    tech = '均线缠绕'
    tech_tag = 't-y'
else:
    tech = '偏多'
    tech_tag = 't-g'

zone_html = f'关键博弈区间 <span class="tag t-g">{yl:.0f}</span> ~ <span class="tag t-r">{yh:.0f}</span>。' if not down_lines else ''

# 压力位行
p_rows = []
for idx, price, vol in pressures:
    p_rows.append(f'<div class="level-row"><span class="dt">{dates[idx].strftime("%Y-%m-%d")}</span><span class="px">{price:.2f}</span><span class="vs">量比 {vol/avg_vol:.1f}x</span></div>')
if not p_rows:
    p_rows.append('<div class="level-row"><span class="dt">—</span><span class="px">无显著压力</span></div>')
s_rows = []
for idx, price, vol in supports:
    s_rows.append(f'<div class="level-row"><span class="dt">{dates[idx].strftime("%Y-%m-%d")}</span><span class="px">{price:.2f}</span><span class="vs">量比 {vol/avg_vol:.1f}x</span></div>')
if not s_rows:
    s_rows.append('<div class="level-row"><span class="dt">—</span><span class="px">无显著支撑</span></div>')

now_str = datetime.now().strftime('%Y-%m-%d %H:%M')

# ============================================================
# 8. HTML
# ============================================================
html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>贵州茅台 (600519) 技术分析 v2</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0d1117;color:#c9d1d9;font-family:-apple-system,BlinkMacSystemFont,"Microsoft YaHei",sans-serif;line-height:1.6}}
.container{{max-width:1160px;margin:0 auto;padding:30px 20px}}
.header{{background:linear-gradient(135deg,#1a1f35,#0d1117);border:1px solid #21262d;border-radius:14px;padding:28px 32px;margin-bottom:24px}}
.header h1{{font-size:26px;color:#f0f6fc}}
.header .meta{{color:#8b949e;font-size:13px;margin-top:6px;display:flex;gap:16px;flex-wrap:wrap}}
.header .meta span{{background:#21262d;padding:3px 10px;border-radius:12px}}
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:10px;margin-bottom:24px}}
.kpi{{background:#161b22;border:1px solid #21262d;border-radius:10px;padding:14px}}
.kpi .l{{font-size:11px;color:#8b949e;margin-bottom:4px}}
.kpi .v{{font-size:21px;font-weight:700;color:#f0f6fc}}
.kpi .s{{font-size:10px;color:#8b949e;margin-top:2px}}
.kpi.dn .v{{color:#ef4444}}
.kpi.up .v{{color:#22c55e}}
.chart-box{{background:#161b22;border:1px solid #21262d;border-radius:14px;padding:20px;margin-bottom:24px}}
.chart-box h2{{font-size:17px;color:#e6edf3;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid #21262d}}
.legend{{display:flex;gap:18px;flex-wrap:wrap;font-size:11px;color:#8b949e;margin-top:10px}}
.legend span{{display:flex;align-items:center;gap:4px}}
.legend .dot{{width:12px;height:3px;border-radius:2px}}
.levels{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px}}
.level{{background:#161b22;border:1px solid #21262d;border-radius:10px;padding:18px}}
.level h3{{font-size:14px;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid #21262d}}
.level.pressure h3{{color:#ef4444}}
.level.support h3{{color:#22c55e}}
.level-row{{display:flex;justify-content:space-between;align-items:center;padding:7px 0;font-size:13px;border-bottom:1px solid #1a1f2e}}
.level-row:last-child{{border:none}}
.level-row .dt{{color:#8b949e;font-size:11px}}
.level-row .px{{font-weight:600}}
.level.pressure .px{{color:#ef4444}}
.level.support .px{{color:#22c55e}}
.level-row .vs{{font-size:10px;padding:1px 6px;border-radius:8px}}
.level.pressure .vs{{background:rgba(239,68,68,0.15);color:#f87171}}
.level.support .vs{{background:rgba(34,197,94,0.15);color:#4ade80}}
.insight{{background:#161b22;border:1px solid #21262d;border-radius:10px;padding:20px;margin-bottom:24px}}
.insight h3{{font-size:14px;color:#e6edf3;margin-bottom:10px}}
.insight p{{font-size:13px;color:#8b949e;line-height:1.9}}
.tag{{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;margin:2px;font-weight:500}}
.t-r{{background:rgba(239,68,68,0.12);color:#ef4444}}
.t-g{{background:rgba(34,197,94,0.12);color:#22c55e}}
.t-b{{background:rgba(56,189,248,0.12);color:#38bdf8}}
.t-y{{background:rgba(245,158,11,0.12);color:#f59e0b}}
.footer{{text-align:center;color:#484f58;font-size:11px;margin-top:30px;padding-top:20px;border-top:1px solid #21262d}}
</style></head>
<body>
<div class="container">
<div class="header">
    <h1>贵州茅台 (600519) 技术分析</h1>
    <div class="meta">
        <span>{dates[0].strftime('%Y-%m-%d')} ~ {dates[-1].strftime('%Y-%m-%d')}</span>
        <span>对数坐标 · 极值起点趋势线</span>
        <span>{n}个交易日</span>
        <span>AllenTrader v2</span>
    </div>
</div>

<div class="kpi-grid">
    <div class="kpi"><div class="l">最新价</div><div class="v">{closes[-1]:.2f}</div><div class="s">距年高 -{dd:.1f}%</div></div>
    <div class="kpi {change_cls}"><div class="l">年涨跌</div><div class="v">{chg:+.1f}%</div><div class="s">对数趋势</div></div>
    <div class="kpi"><div class="l">MA20</div><div class="v" style="color:#f59e0b">{ma20[-1]:.2f}</div><div class="s">{ma20_pos}</div></div>
    <div class="kpi"><div class="l">MA60</div><div class="v" style="color:#8b5cf6">{ma60[-1]:.2f}</div><div class="s">{ma60_pos}</div></div>
    <div class="kpi"><div class="l">年高</div><div class="v">{yh:.0f}</div><div class="s">回调 -{dd:.1f}%</div></div>
    <div class="kpi"><div class="l">年低</div><div class="v">{yl:.0f}</div><div class="s">反弹 +{bounce:.1f}%</div></div>
</div>

<div class="chart-box">
    <h2>日K线图 — 趋势线从极值点出发 · 带成交量</h2>
    {svg_str}
    <div class="legend">
        <span><span class="dot" style="background:#f59e0b"></span> MA20</span>
        <span><span class="dot" style="background:#8b5cf6"></span> MA60</span>
        <span><span class="dot" style="background:#22c55e;height:1px;border:1px dashed #22c55e"></span> 上升（从最低点）</span>
        <span><span class="dot" style="background:#ef4444;height:1px;border:1px dashed #ef4444"></span> 下降（从最高点）</span>
    </div>
</div>

<div class="levels">
    <div class="level pressure">
        <h3>压力位（成交量加权）</h3>
        {''.join(p_rows)}
    </div>
    <div class="level support">
        <h3>支撑位（成交量加权）</h3>
        {''.join(s_rows)}
    </div>
</div>

<div class="insight">
    <h3>趋势线分析</h3>
    <p>{tl_text}</p>
    <br>
    <h3>技术研判</h3>
    <p>
    当前价 <span class="tag t-y">{closes[-1]:.2f}</span>，
    均线 <span class="tag {tech_tag}">{tech}</span>
    （MA20 {ma20[-1]:.2f} / MA60 {ma60[-1]:.2f}）。
    {zone_html}
    </p>
    <p>成交量分布显示主要换手集中在 {yl:.0f}-{yh:.0f} 区间。</p>
</div>

<div class="footer">AllenTrader v2 · {now_str} · 趋势线从区间极值点出发（起点=全区间最高/最低点）</div>
</div>
</body></html>'''

# ============================================================
# 9. 保存
# ============================================================
output_dir = '/home/admin/sites/allenqian.online/reports'
os.makedirs(output_dir, exist_ok=True)
filename = 'moutai_technical.html'
path = os.path.join(output_dir, filename)
with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'\n✅ 报告已保存: {path}')
print(f'   访问: http://allenqian.online/reports/{filename}')
print(f'   文件大小: {len(html):,} 字节')
