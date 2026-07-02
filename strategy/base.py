"""策略基类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SignalType(Enum):
    BUY = 'buy'
    SELL = 'sell'
    HOLD = 'hold'


@dataclass
class Signal:
    """交易信号"""
    symbol: str
    type: SignalType
    price: float
    amount: int = 0
    reason: str = ''
    confidence: float = 0.0
    timestamp: str = ''


@dataclass
class Portfolio:
    """投资组合"""
    cash: float = 0.0
    total_value: float = 0.0
    positions: dict = field(default_factory=dict)

    @property
    def stock_ratio(self) -> float:
        if self.total_value == 0:
            return 0.0
        stock_value = sum(
            p.get('market_value', 0) for p in self.positions.values()
        )
        return stock_value / self.total_value


class BaseStrategy(ABC):
    """策略基类"""

    def __init__(self, name: str = 'base'):
        self.name = name
        self.portfolio: Optional[Portfolio] = None

    @abstractmethod
    def on_bar(self, symbol: str, data: dict) -> Signal:
        """每个 Bar 调用，返回交易信号"""
        ...

    def on_order_filled(self, order: dict):
        """订单成交回调"""
        pass

    def update_portfolio(self, portfolio: Portfolio):
        """更新组合状态"""
        self.portfolio = portfolio
