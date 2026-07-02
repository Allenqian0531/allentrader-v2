"""
趋势跟踪策略
- 多周期压力/支撑位识别
- 趋势线拟合与突破判断
- 量价配合信号
"""

import numpy as np
from scipy.signal import find_peaks
from typing import Tuple, List, Optional

from .base import BaseStrategy, Signal, SignalType


class TrendStrategy(BaseStrategy):
    """
    多周期趋势策略

    参数:
        lookback_days: 回看天数
        volume_confirm: 是否需要成交量确认
        trend_strength: 趋势强度阈值 (0-1)
    """

    def __init__(self, lookback_days: int = 60, volume_confirm: bool = True,
                 trend_strength: float = 0.3):
        super().__init__(name='trend')
        self.lookback = lookback_days
        self.volume_confirm = volume_confirm
        self.trend_strength = trend_strength

    def on_bar(self, symbol: str, data: dict) -> Signal:
        return Signal(symbol=symbol, type=SignalType.HOLD, price=data.get('close', 0))

    @staticmethod
    def find_pressure_levels(highs: np.ndarray, distance: int = 5,
                             prominence: float = 1.0) -> List[int]:
        """找出压力位"""
        peaks, _ = find_peaks(highs, distance=distance, prominence=prominence)
        return peaks.tolist()

    @staticmethod
    def find_support_levels(lows: np.ndarray, distance: int = 5,
                            prominence: float = 1.0) -> List[int]:
        """找出支撑位"""
        troughs, _ = find_peaks(-lows, distance=distance, prominence=prominence)
        return troughs.tolist()

    @staticmethod
    def fit_trend_line(points: List[int], values: np.ndarray) -> Tuple[float, float, bool]:
        """
        拟合趋势线
        Returns: (斜率, 截距, 是否为上升趋势)
        """
        if len(points) < 2:
            return 0, 0, False
        slope, intercept = np.polyfit(points, values[points], 1)
        return slope, intercept, slope > 0

    @staticmethod
    def calc_ma(data: np.ndarray, period: int) -> np.ndarray:
        """计算移动均线"""
        return np.convolve(data, np.ones(period) / period, mode='valid')
