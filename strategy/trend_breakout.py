"""
趋势线突破策略
- 买入：收盘价突破非最后一条下降趋势线
- 卖出：收盘价跌回所有趋势线下方
"""
import numpy as np
from .base import BaseStrategy
from core.trendline import find_trendlines, price_at


class TrendBreakout(BaseStrategy):
    """
    趋势线突破策略

    参数:
        direction: 'down' 下降趋势线突破 / 'up' 上升趋势线跌破
        min_bars: 最少K线数
        confirm_bars: 连续站上/跌破确认天数
    """
    params = (
        ('direction', 'down'),
        ('min_bars', 30),
        ('confirm_bars', 1),
    )

    def __init__(self):
        self._confirm_count = 0
        self.init_indicators()

    def init_indicators(self):
        # 趋势线策略无需预计算指标
        pass

    def on_bar(self) -> dict:
        n = len(self.data)
        if n < self.p.min_bars:
            return None

        # 获取当前能看到的所有数据（无未来函数）
        highs = np.array(list(self.data.high.get(size=n))[::-1])
        lows = np.array(list(self.data.low.get(size=n))[::-1])
        close = self.data.close[0]
        idx = n - 1

        lines = find_trendlines(highs, lows, direction=self.p.direction)
        if not lines:
            return None

        if self.p.direction == 'down':
            # 检查突破：价格站上非最后一条下降趋势线
            for i, line in enumerate(lines):
                if i == len(lines) - 1:
                    continue  # 最后一条不交易
                line_price = price_at(line, idx)
                if close > line_price:
                    self._confirm_count += 1
                    if self._confirm_count >= self.p.confirm_bars:
                        self._confirm_count = 0
                        return {
                            'action': 'buy',
                            'reason': f'突破趋势线{i+1} {close:.1f}>{line_price:.1f}'
                        }
                    return None

        self._confirm_count = 0

        # 出场：跌回所有线下
        if self.position:
            below_all = True
            for line in lines:
                if close > price_at(line, idx):
                    below_all = False
                    break
            if below_all:
                return {
                    'action': 'sell',
                    'reason': f'跌回所有线下 {close:.1f}'
                }

        return None
