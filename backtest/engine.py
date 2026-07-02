"""回测引擎"""
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

from strategy.base import Signal, SignalType, Portfolio


@dataclass
class BacktestResult:
    """回测结果"""
    initial_cash: float
    final_value: float
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    trades: List[dict] = field(default_factory=list)
    equity_curve: pd.Series = None

    def summary(self) -> str:
        return (
            f"初始资金: ¥{self.initial_cash:,.0f}\n"
            f"最终价值: ¥{self.final_value:,.0f}\n"
            f"总收益率: {self.total_return:.2%}\n"
            f"年化收益: {self.annual_return:.2%}\n"
            f"最大回撤: {self.max_drawdown:.2%}\n"
            f"夏普比率: {self.sharpe_ratio:.2f}\n"
            f"胜率: {self.win_rate:.2%}\n"
            f"交易次数: {self.total_trades}"
        )


class BacktestEngine:
    """简易回测引擎"""

    def __init__(self, initial_cash: float = 100000, commission: float = 0.0003):
        self.initial_cash = initial_cash
        self.commission = commission
        self.portfolio = Portfolio(cash=initial_cash, total_value=initial_cash)

    def run(self, data: pd.DataFrame, strategy) -> BacktestResult:
        """
        运行回测

        Args:
            data: OHLCV DataFrame, index=datetime
            strategy: 策略对象，需要有 on_bar 方法
        """
        trades = []
        equity = [self.initial_cash]

        for i, (idx, bar) in enumerate(data.iterrows()):
            bar_dict = bar.to_dict()
            bar_dict['date'] = idx

            signal = strategy.on_bar('test', bar_dict)

            if signal.type == SignalType.BUY:
                price = bar['close']
                amount = int(self.portfolio.cash * 0.3 / price / 100) * 100
                if amount > 0:
                    cost = amount * price * (1 + self.commission)
                    if cost <= self.portfolio.cash:
                        self.portfolio.cash -= cost
                        self.portfolio.positions[signal.symbol] = {
                            'amount': amount,
                            'cost_price': price,
                            'market_value': amount * price
                        }
                        trades.append({
                            'date': idx,
                            'type': 'buy',
                            'price': price,
                            'amount': amount,
                            'cost': cost
                        })

            elif signal.type == SignalType.SELL:
                pos = self.portfolio.positions.get(signal.symbol, {})
                amount = pos.get('amount', 0)
                if amount > 0:
                    price = bar['close']
                    revenue = amount * price * (1 - self.commission)
                    self.portfolio.cash += revenue
                    del self.portfolio.positions[signal.symbol]
                    trades.append({
                        'date': idx,
                        'type': 'sell',
                        'price': price,
                        'amount': amount,
                        'revenue': revenue
                    })

            # 更新市值
            stock_value = 0
            for sym, pos in self.portfolio.positions.items():
                pos['market_value'] = pos['amount'] * bar['close']
                stock_value += pos['market_value']
            self.portfolio.total_value = self.portfolio.cash + stock_value
            equity.append(self.portfolio.total_value)

        return self._calc_metrics(equity, trades)

    def _calc_metrics(self, equity: list, trades: list) -> BacktestResult:
        equity_s = pd.Series(equity)

        returns = equity_s.pct_change().dropna()
        total_return = (equity_s.iloc[-1] / equity_s.iloc[0]) - 1
        n_days = len(equity_s)
        annual_return = (1 + total_return) ** (252 / n_days) - 1 if n_days > 0 else 0
        max_dd = ((equity_s / equity_s.cummax()) - 1).min()

        # 夏普比率
        risk_free = 0.02
        excess = returns.mean() * 252 - risk_free
        sharpe = excess / (returns.std() * np.sqrt(252)) if returns.std() > 0 else 0

        # 胜率
        wins = sum(1 for t in trades if t.get('revenue', 0) > t.get('cost', 0))
        win_rate = wins / len(trades) if trades else 0

        return BacktestResult(
            initial_cash=self.initial_cash,
            final_value=equity_s.iloc[-1],
            total_return=total_return,
            annual_return=annual_return,
            max_drawdown=max_dd,
            sharpe_ratio=sharpe,
            win_rate=win_rate,
            total_trades=len(trades),
            trades=trades,
            equity_curve=equity_s
        )
