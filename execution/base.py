"""
执行层 - 交易执行抽象
将来对接 QMT / 同花顺OCR / 券商API
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class Order:
    symbol: str
    side: str          # 'buy' / 'sell'
    price: float
    amount: int
    order_type: str = 'limit'  # 'limit' / 'market'


@dataclass
class OrderResult:
    success: bool
    order_id: Optional[str] = None
    message: str = ''


class BaseBroker(ABC):
    """券商接口基类"""

    @abstractmethod
    def connect(self) -> bool:
        """连接券商"""
        ...

    @abstractmethod
    def buy(self, symbol: str, price: float, amount: int) -> OrderResult:
        """买入"""
        ...

    @abstractmethod
    def sell(self, symbol: str, price: float, amount: int) -> OrderResult:
        """卖出"""
        ...

    @abstractmethod
    def cancel(self, order_id: str) -> OrderResult:
        """撤单"""
        ...

    @abstractmethod
    def get_balance(self) -> dict:
        """获取账户资金"""
        ...

    @abstractmethod
    def get_positions(self) -> dict:
        """获取持仓"""
        ...

    @abstractmethod
    def disconnect(self):
        """断开连接"""
        ...


class DummyBroker(BaseBroker):
    """模拟券商 - 用于测试"""

    def __init__(self, initial_cash: float = 100000):
        self.cash = initial_cash
        self.positions = {}
        self._connected = False

    def connect(self) -> bool:
        self._connected = True
        return True

    def buy(self, symbol: str, price: float, amount: int) -> OrderResult:
        cost = amount * price
        if cost > self.cash:
            return OrderResult(False, message='资金不足')
        self.cash -= cost
        self.positions[symbol] = self.positions.get(symbol, 0) + amount
        return OrderResult(True, order_id='mock_buy', message='success')

    def sell(self, symbol: str, price: float, amount: int) -> OrderResult:
        if symbol not in self.positions or self.positions[symbol] < amount:
            return OrderResult(False, message='持仓不足')
        self.positions[symbol] -= amount
        self.cash += amount * price
        if self.positions[symbol] == 0:
            del self.positions[symbol]
        return OrderResult(True, order_id='mock_sell', message='success')

    def cancel(self, order_id: str) -> OrderResult:
        return OrderResult(True, message='已撤单')

    def get_balance(self) -> dict:
        return {'available': self.cash, 'total': self.cash}

    def get_positions(self) -> dict:
        return self.positions

    def disconnect(self):
        self._connected = False
