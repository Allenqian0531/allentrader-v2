"""
趋势线识别 — 唯一版本

规则:
- 从极值点出发（下降=最高点，上升=最低点）
- 首尾相连，链式延伸
- 最后一条允许被突破/跌破
- 不要求触及次数
"""
import numpy as np
from typing import List, Dict


def find_trendlines(highs: np.ndarray, lows: np.ndarray,
                    direction: str = 'down') -> List[Dict]:
    """
    找出趋势线链

    Args:
        highs: 最高价序列
        lows:  最低价序列
        direction: 'down' 下降趋势线 / 'up' 上升趋势线

    Returns:
        [{start_idx, end_idx, slope, intercept, length}, ...]
        按时间排序，首尾相连
    """
    n = len(highs)
    if n < 6:
        return []

    log_h = np.log(highs + 1e-10)
    log_l = np.log(lows + 1e-10)

    if direction == 'down':
        start_idx = int(np.argmax(highs))
        log_vals = log_h
        is_higher = lambda cur, cand: cand >= cur
        is_break = lambda val, line: val > line + 0.005
    else:
        start_idx = int(np.argmin(lows))
        log_vals = log_l
        is_higher = lambda cur, cand: cand <= cur
        is_break = lambda val, line: val < line - 0.005

    if start_idx >= n - 3:
        return []

    result = []
    cur = start_idx

    while cur < n - 3:
        best = None
        for end in range(cur + 3, n):
            if is_higher(log_vals[cur], log_vals[end]):
                continue
            slope = (log_vals[end] - log_vals[cur]) / (end - cur)
            intercept = log_vals[cur] - slope * cur

            ok = True
            for i in range(cur, end + 1):
                line_val = slope * i + intercept
                if is_break(log_vals[i], line_val):
                    ok = False
                    break
            if ok:
                span = end - cur
                if best is None or span > (best['end_idx'] - cur):
                    best = {
                        'start_idx': cur, 'end_idx': end,
                        'slope': slope, 'intercept': intercept,
                        'length': span
                    }
        if best is None:
            break
        result.append(best)
        cur = best['end_idx']

    return result


def get_active_lines(lines: List[Dict], current_idx: int,
                     highs: np.ndarray = None, lows: np.ndarray = None
                     ) -> List[Dict]:
    """
    筛选当前有效的趋势线（前向验证）

    最后一条允许被突破，其余必须通过验证。

    Args:
        lines: find_trendlines 的结果
        current_idx: 当前 bar 索引
        highs, lows: 用于前向验证（若为 None 则只做区间内验证）

    Returns:
        通过验证的线列表
    """
    if not lines:
        return []

    active = []
    last = len(lines) - 1
    log_h = np.log(highs + 1e-10) if highs is not None else None
    log_l = np.log(lows + 1e-10) if lows is not None else None

    for i, line in enumerate(lines):
        if i == last:
            active.append(line)
            continue

        ok = True
        for j in range(line['end_idx'] + 1, current_idx + 1):
            line_val = line['slope'] * j + line['intercept']
            if line['slope'] < 0:  # 下降趋势线
                if log_h is not None and log_h[j] > line_val + 0.005:
                    ok = False
                    break
            else:  # 上升趋势线
                if log_l is not None and log_l[j] < line_val - 0.005:
                    ok = False
                    break
        if ok:
            active.append(line)

    return active


def price_at(line: Dict, idx: int) -> float:
    """趋势线在指定索引处的价格"""
    return np.exp(line['slope'] * idx + line['intercept'])
