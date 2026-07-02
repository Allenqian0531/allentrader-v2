"""
趋势线识别模块 — 基于价格行为的真实趋势线

定义：
  上升趋势线: 连接至少2个连续抬高的低点，且后续价格不跌破该线
  下降趋势线: 连接至少2个连续降低的高点，且后续价格不突破该线

来源: 移植自 allentrader v1 model/index/trend.py
"""

import numpy as np
from scipy.signal import find_peaks
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class TrendLine:
    """趋势线"""
    start_idx: int       # 起点索引
    end_idx: int         # 终点索引
    slope: float         # 斜率
    intercept: float     # 截距
    is_up: bool          # True=上升趋势线(连接低点), False=下降趋势线(连接高点)
    is_log: bool         # 是否对数坐标
    touch_count: int     # 触及次数（越多越可靠）
    length: int          # 跨越的K线数（越长越可靠）

    def price_at(self, idx: int, is_log: bool = False) -> float:
        """获取该趋势线在指定索引处的价格"""
        val = self.slope * idx + self.intercept
        return np.exp(val) if is_log else val


def _merge_nearby_levels(indices: list, values: list, threshold_pct: float = 0.02) -> tuple:
    """合并过于接近的价位（价格差 < threshold_pct），保留成交量更大的"""
    if len(indices) <= 1:
        return indices, values

    merged_idx = []
    merged_val = []
    used = set()

    for i in range(len(indices)):
        if i in used:
            continue
        group_i = [i]
        for j in range(i + 1, len(indices)):
            if j in used:
                continue
            if abs(values[i] - values[j]) / values[i] < threshold_pct:
                group_i.append(j)
                used.add(j)
        # 保留第一个（按重要性排序后最靠前的）
        merged_idx.append(indices[group_i[0]])
        merged_val.append(values[group_i[0]])

    return merged_idx, merged_val


def find_trend_lines(
    highs: np.ndarray,
    lows: np.ndarray,
    volumes: np.ndarray = None,
    is_log: bool = True,
    min_length: int = 3,
) -> Tuple[List[TrendLine], List[TrendLine]]:
    """
    找出所有有效的趋势线

    Args:
        highs: 最高价序列
        lows: 最低价序列
        volumes: 成交量序列（用于加权，可选）
        is_log: 是否在对数空间计算
        min_length: 趋势线最少跨越K线数

    Returns:
        (up_lines, down_lines): 上升趋势线列表, 下降趋势线列表
    """
    n = len(highs)

    # 转换到对数空间（如果需要）
    if is_log:
        h = np.log(highs + 1e-10)
        l = np.log(lows + 1e-10)
    else:
        h = highs
        l = lows

    up_lines = _find_up_trend_lines(h, l, n, min_length)
    down_lines = _find_down_trend_lines(h, l, n, min_length)

    return up_lines, down_lines


def _find_up_trend_lines(h: np.ndarray, l: np.ndarray, n: int, min_len: int) -> List[TrendLine]:
    """
    找上升趋势线：连接连续抬高的低点

    算法：
    1. 遍历每个低点作为起点
    2. 找到后续所有比起点更高的低点
    3. 对每个候选终点，画线并验证无价格跌破
    4. 保留有效的最长趋势线
    """
    lines = []

    for start in range(n - min_len):
        start_low = l[start]

        for end in range(start + min_len, n):
            end_low = l[end]

            # 必须是抬高的低点
            if end_low <= start_low:
                continue

            # 计算趋势线
            slope = (end_low - start_low) / (end - start)
            intercept = start_low - slope * start

            # 验证：从起点到终点之间，所有低点都不能跌破该线
            valid = True
            touch_count = 2  # 起点+终点
            for i in range(start, end + 1):
                line_val = slope * i + intercept
                if l[i] < line_val - 0.005:  # 允许微小误差
                    valid = False
                    break
                if abs(l[i] - line_val) < 0.005:
                    touch_count += 1

            if valid:
                lines.append(TrendLine(
                    start_idx=start, end_idx=end,
                    slope=slope, intercept=intercept,
                    is_up=True, is_log=True,
                    touch_count=touch_count,
                    length=end - start
                ))

    # 去重：保留每个起点延伸最远的线
    lines.sort(key=lambda x: (x.start_idx, -x.length))
    filtered = []
    last_start = -1
    for line in lines:
        if line.start_idx != last_start:
            filtered.append(line)
            last_start = line.start_idx

    return filtered


def _find_down_trend_lines(h: np.ndarray, l: np.ndarray, n: int, min_len: int) -> List[TrendLine]:
    """
    找下降趋势线：连接连续降低的高点

    算法：
    1. 遍历每个高点作为起点
    2. 找到后续所有比起点更低的高点
    3. 对每个候选终点，画线并验证无价格突破
    4. 保留有效的最长趋势线
    """
    lines = []

    for start in range(n - min_len):
        start_high = h[start]

        for end in range(start + min_len, n):
            end_high = h[end]

            # 必须是降低的高点
            if end_high >= start_high:
                continue

            slope = (end_high - start_high) / (end - start)
            intercept = start_high - slope * start

            # 验证：从起点到终点之间，所有高点都不能突破该线
            valid = True
            touch_count = 2
            for i in range(start, end + 1):
                line_val = slope * i + intercept
                if h[i] > line_val + 0.005:
                    valid = False
                    break
                if abs(h[i] - line_val) < 0.005:
                    touch_count += 1

            if valid:
                lines.append(TrendLine(
                    start_idx=start, end_idx=end,
                    slope=slope, intercept=intercept,
                    is_up=False, is_log=True,
                    touch_count=touch_count,
                    length=end - start
                ))

    lines.sort(key=lambda x: (x.start_idx, -x.length))
    filtered = []
    last_start = -1
    for line in lines:
        if line.start_idx != last_start:
            filtered.append(line)
            last_start = line.start_idx

    return filtered


def get_active_trend_lines(
    up_lines: List[TrendLine],
    down_lines: List[TrendLine],
    current_idx: int,
    highs: np.ndarray = None,
    lows: np.ndarray = None,
    top_n: int = 2,
) -> Tuple[List[TrendLine], List[TrendLine]]:
    """
    获取当前有效的趋势线

    有效条件：
    - 上升趋势线：从 end_idx 到 current_idx，所有低点都不跌破该线
    - 下降趋势线：从 end_idx 到 current_idx，所有高点都不突破该线

    Returns:
        (active_up, active_down)
    """
    if highs is None or lows is None:
        raise ValueError("highs and lows are required for forward validation")

    # 对数空间
    log_highs = np.log(highs + 1e-10)
    log_lows = np.log(lows + 1e-10)

    active_up = []
    for line in up_lines:
        # 前向验证：从终点之后到今天，是否有低点跌破该线
        valid = True
        for i in range(line.end_idx + 1, current_idx + 1):
            line_val = line.slope * i + line.intercept
            if log_lows[i] < line_val - 0.005:  # 跌破了
                valid = False
                break
        if valid:
            active_up.append(line)

    active_down = []
    for line in down_lines:
        # 前向验证：从终点之后到今天，是否有高点突破该线
        valid = True
        for i in range(line.end_idx + 1, current_idx + 1):
            line_val = line.slope * i + line.intercept
            if log_highs[i] > line_val + 0.005:  # 突破了
                valid = False
                break
        if valid:
            active_down.append(line)
            continue
        active_down.append(line)

    # 按可靠性排序：长度 * 触及次数
    active_up.sort(key=lambda x: x.length * x.touch_count, reverse=True)
    active_down.sort(key=lambda x: x.length * x.touch_count, reverse=True)

    return active_up[:top_n], active_down[:top_n]
