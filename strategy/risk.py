"""风控模块"""
from dataclasses import dataclass
from typing import Optional

from .base import Portfolio, Signal, SignalType


@dataclass
class RiskConfig:
    max_position_ratio: float = 0.6      # 最大仓位
    max_single_stock_ratio: float = 0.3  # 单票最大仓位
    stop_loss: float = -0.08             # 止损线
    stop_profit: float = 0.15            # 止盈线
    max_daily_trades: int = 10           # 每日最大交易次数
    max_daily_loss: float = -0.05        # 每日最大亏损比例


class RiskController:
    """风控控制器"""

    def __init__(self, config: RiskConfig = RiskConfig()):
        self.config = config
        self.daily_trades = 0
        self.daily_pnl = 0.0

    def check(self, signal: Signal, portfolio: Portfolio) -> bool:
        """检查信号是否通过风控"""

        # 日内交易次数限制
        if self.daily_trades >= self.config.max_daily_trades:
            signal.reason = '日内交易次数超限'
            return False

        # 日内亏损限制
        if self.daily_pnl < self.config.max_daily_loss:
            signal.reason = '日内亏损超限'
            return False

        if signal.type == SignalType.BUY:
            return self._check_buy(signal, portfolio)

        elif signal.type == SignalType.SELL:
            return self._check_sell(signal, portfolio)

        return True

    def _check_buy(self, signal: Signal, portfolio: Portfolio) -> bool:
        # 总仓位检查
        if portfolio.stock_ratio >= self.config.max_position_ratio:
            signal.reason = '总仓位已达上限'
            return False

        # 单票仓位检查
        existing = portfolio.positions.get(signal.symbol, {})
        existing_ratio = existing.get('market_value', 0) / portfolio.total_value \
            if portfolio.total_value > 0 else 0
        if existing_ratio >= self.config.max_single_stock_ratio:
            signal.reason = '单票仓位已达上限'
            return False

        return True

    def _check_sell(self, signal: Signal, portfolio: Portfolio) -> bool:
        pos = portfolio.positions.get(signal.symbol)
        if not pos or pos.get('amount', 0) <= 0:
            signal.reason = '无持仓可卖'
            return False

        # 止损止盈
        cost = pos.get('cost_price', 0)
        current = signal.price
        if cost > 0:
            pnl_pct = (current - cost) / cost
            if pnl_pct >= self.config.stop_profit:
                signal.reason = f'止盈触发 ({pnl_pct:.1%})'
            elif pnl_pct <= self.config.stop_loss:
                signal.reason = f'止损触发 ({pnl_pct:.1%})'

        return True

    def on_trade(self, pnl: float):
        self.daily_trades += 1
        self.daily_pnl += pnl

    def reset_daily(self):
        self.daily_trades = 0
        self.daily_pnl = 0.0
