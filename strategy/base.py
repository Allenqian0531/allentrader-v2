"""
策略基类 — 继承 backtrader.Strategy
所有策略从此派生
"""
import backtrader as bt
from abc import abstractmethod


class BaseStrategy(bt.Strategy):
    """
    策略基类

    子类只需实现:
        on_bar(data)  → 返回信号 (buy/sell/None)
        init_indicators() → 初始化指标（可选）

    内置功能:
        - 资金管理（仓位上限于 params.risk_pct）
        - 日志
        - 自动添加分析器
    """
    params = (
        ('risk_pct', 0.2),       # 单笔最大仓位（总资金%）
        ('log_level', 'info'),   # debug / info / silent
    )

    def log(self, msg: str, level: str = 'info'):
        if self.p.log_level == 'silent':
            return
        if self.p.log_level == 'debug' or level != 'debug':
            dt = self.data.datetime.date(0)
            print(f'  [{dt}] {msg}')

    def size_for_risk(self, price: float = None) -> int:
        """计算可买股数（按风险仓位）"""
        cash = self.broker.getcash()
        if price is None:
            price = self.data.close[0]
        max_value = cash * self.p.risk_pct
        return int(max_value / price / 100) * 100  # A股100股整倍数

    @abstractmethod
    def init_indicators(self):
        """初始化技术指标（在 __init__ 中调用）"""
        pass

    @abstractmethod
    def on_bar(self) -> dict:
        """
        每根 bar 的决策逻辑

        Returns:
            {'action': 'buy'/'sell'/None, 'size': int, 'reason': str}
        """
        pass

    def next(self):
        signal = self.on_bar()
        if signal is None:
            return

        action = signal.get('action')
        size = signal.get('size')

        if action == 'buy' and not self.position:
            if size is None:
                size = self.size_for_risk()
            self.log(f'买入 {size}股 (原因: {signal.get("reason","")})')
            self.buy(size=size)

        elif action == 'sell' and self.position:
            self.log(f'卖出 (原因: {signal.get("reason","")})')
            self.close()
