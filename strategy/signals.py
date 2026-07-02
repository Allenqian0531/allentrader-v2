"""信号生成器 - 技术指标信号"""
import numpy as np
from typing import List
from .base import Signal, SignalType


class SignalGenerator:
    """技术信号生成器"""

    @staticmethod
    def ma_cross(short: np.ndarray, long: np.ndarray) -> int:
        """
        MA金叉死叉
        Returns: 1=金叉, -1=死叉, 0=无信号
        """
        if len(short) < 2 or len(long) < 2:
            return 0
        if short[-2] <= long[-2] and short[-1] > long[-1]:
            return 1
        if short[-2] >= long[-2] and short[-1] < long[-1]:
            return -1
        return 0

    @staticmethod
    def volume_break(volume: np.ndarray, ma_period: int = 20, multiplier: float = 1.5) -> bool:
        """放量突破"""
        if len(volume) < ma_period:
            return False
        vol_ma = np.mean(volume[-ma_period:])
        return volume[-1] > vol_ma * multiplier

    @staticmethod
    def rsi_signal(rsi: float, oversold: float = 30, overbought: float = 70) -> int:
        """RSI超买超卖"""
        if rsi < oversold:
            return 1   # 买入信号
        if rsi > overbought:
            return -1  # 卖出信号
        return 0

    @staticmethod
    def calc_rsi(closes: np.ndarray, period: int = 14) -> float:
        """计算RSI"""
        if len(closes) < period + 1:
            return 50.0
        deltas = np.diff(closes)
        gains = np.maximum(deltas, 0)
        losses = np.abs(np.minimum(deltas, 0))
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
