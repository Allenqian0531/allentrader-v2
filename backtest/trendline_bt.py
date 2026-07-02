"""
茅台趋势线回测 — backtrader 验证
策略: 下降趋势线被突破（收盘站上）→ 买入；跌回趋势线下方 → 卖出
"""
import backtrader as bt
import numpy as np
from datetime import datetime

# ─── 趋势线计算（只看到当前bar为止的数据，无未来函数） ───
def compute_trendline_raw(highs, lows, is_downtrend=True):
    """返回从极值点出发、首尾相连的趋势线列表"""
    highs = np.array(highs)
    lows = np.array(lows)
    n = len(highs)
    if n < 6:
        return []
    log_h = np.log(highs + 1e-10)
    log_l = np.log(lows + 1e-10)

    if is_downtrend:
        peak = int(np.argmax(highs))
        if peak >= n - 3:
            return []
        result = []
        cur = peak
        while cur < n - 3:
            best = None
            for end in range(cur + 3, n):
                if log_h[end] >= log_h[cur]:
                    continue
                slope = (log_h[end] - log_h[cur]) / (end - cur)
                intercept = log_h[cur] - slope * cur
                ok = True
                for i in range(cur, end + 1):
                    if log_h[i] > slope * i + intercept + 0.005:
                        ok = False
                        break
                if ok and (best is None or end > best['end']):
                    best = {'start': cur, 'end': end, 'slope': slope, 'intercept': intercept}
            if best is None:
                break
            result.append(best)
            cur = best['end']
        return result
    else:
        trough = int(np.argmin(lows))
        if trough >= n - 3:
            return []
        result = []
        cur = trough
        while cur < n - 3:
            best = None
            for end in range(cur + 3, n):
                if log_l[end] <= log_l[cur]:
                    continue
                slope = (log_l[end] - log_l[cur]) / (end - cur)
                intercept = log_l[cur] - slope * cur
                ok = True
                for i in range(cur, end + 1):
                    if log_l[i] < slope * i + intercept - 0.005:
                        ok = False
                        break
                if ok and (best is None or end > best['end']):
                    best = {'start': cur, 'end': end, 'slope': slope, 'intercept': intercept}
            if best is None:
                break
            result.append(best)
            cur = best['end']
        return result


class TrendLineStrategy(bt.Strategy):
    params = (
        ('lookback_min', 30),
        ('breakout_bars', 1),     # 1日就确认（简化验证）
    )

    def __init__(self):
        self.crossed = 0

    def log(self, msg):
        dt = self.data.datetime.date(0)
        print(f'  [{dt}] {msg}')

    def next(self):
        n = len(self.data)
        if n < self.p.lookback_min:
            return

        highs = list(self.data.high.get(size=n))[::-1]
        lows  = list(self.data.low.get(size=n))[::-1]
        down_lines = compute_trendline_raw(highs, lows, is_downtrend=True)

        if not down_lines:
            return

        close = self.data.close[0]
        idx = n - 1
        dt = self.data.datetime.date(0)

        # 验证模式：打印趋势线信息
        if not self.position and len(down_lines) > 0:
            tl_lines = []
            for i, tl in enumerate(down_lines):
                val = np.exp(tl['slope'] * idx + tl['intercept'])
                tag = "最后" if i == len(down_lines) - 1 else "有效"
                tl_lines.append(f'线{i+1}={val:.1f}({tag})')
            first_val = np.exp(down_lines[0]['slope'] * idx + down_lines[0]['intercept'])
            if close > first_val:
                self.log(f'趋势线: {" ".join(tl_lines)} 收盘={close:.2f}')

        # 找第一个非最后一条的突破
        for i, tl in enumerate(down_lines):
            is_last = (i == len(down_lines) - 1)
            line_val = np.exp(tl['slope'] * idx + tl['intercept'])
            if not is_last and close > line_val:
                self.crossed += 1
                if self.crossed >= self.p.breakout_bars and not self.position:
                    self.log(f'🔵 突破趋势线{i+1} 收盘{close:.2f}>线{line_val:.2f} → 买入')
                    self.buy(size=100)
                    self.crossed = 0
                return

        self.crossed = 0

        # 出场
        if self.position:
            below_all = True
            for i, tl in enumerate(down_lines):
                line_val = np.exp(tl['slope'] * idx + tl['intercept'])
                if close > line_val:
                    below_all = False
                    break
            if below_all:
                self.log(f'🔴 跌回所有线下 收盘{close:.2f} → 卖出')
                self.close()


# ─── 跑回测 ───
if __name__ == '__main__':
    import sys
    sys.path.insert(0, '/home/admin/allentrader-v2')
    from data.feeds import DataFeed
    import pandas as pd

    print("📡 加载数据...")
    df = DataFeed.get_a_share_daily('600519', start_date='20250701', end_date='20260702')

    # 转成 backtrader 数据格式
    df_bt = df.rename(columns={
        'open': 'open', 'high': 'high', 'low': 'low',
        'close': 'close', 'volume': 'volume'
    })
    df_bt.index.name = 'datetime'
    data = bt.feeds.PandasData(dataname=df_bt)

    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.addstrategy(TrendLineStrategy)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.02)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.broker.setcash(1000000.0)
    cerebro.broker.setcommission(commission=0.0003)  # A股佣金

    start_val = cerebro.broker.getvalue()
    print(f"\n初始资金: ¥{start_val:,.0f}")
    print("运行回测...\n")

    results = cerebro.run()
    final_val = cerebro.broker.getvalue()

    # 结果
    ret = (final_val - start_val) / start_val * 100
    print(f"最终资金: ¥{final_val:,.0f}")
    print(f"策略收益: {ret:+.2f}%")

    # 对比 buy & hold
    bh_ret = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100
    print(f"买入持有: {bh_ret:+.2f}%")
    print(f"超额收益: {ret - bh_ret:+.2f}%")

    strat = results[0]
    print(f"\n📊 交易分析:")
    trades = strat.analyzers.trades.get_analysis()
    print(f"  总交易: {trades.get('total', {}).get('total', 0)} 笔")
    print(f"  盈利: {trades.get('won', {}).get('total', 0)} 笔 / 亏损: {trades.get('lost', {}).get('total', 0)} 笔")
    dd = strat.analyzers.drawdown.get_analysis()
    print(f"  最大回撤: {dd.get('max', {}).get('drawdown', 0):.2f}%")
