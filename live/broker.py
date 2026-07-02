"""
实盘 Broker — backtrader 兼容

待对接银河证券 QMT 后，填入 xt_trader API 调用。
当前版本：继承 backtrader.backend，占位模拟。
"""
import backtrader as bt


class LiveBroker(bt.BackBroker):
    """
    实盘 Broker 骨架

    继承 bt.BackBroker，实现券商接口。
    切换回测/实盘只需改一行：
        cerebro.setbroker(SimBroker())  →  cerebro.setbroker(LiveBroker())
    """

    params = (
        ('host', '127.0.0.1'),
        ('port', 58610),           # QMT 默认端口
    )

    def __init__(self):
        super().__init__()
        self._connected = False
        self._xt = None            # xt_trader 实例（待对接）

    def connect(self) -> bool:
        """连接券商"""
        # TODO: from xtquant import xtdata, xttrader
        # self._xt = xttrader.XtQuantTrader(self.p.host, self.p.port)
        # self._connected = self._xt.start() == 0
        print(f'[LiveBroker] QMT 待对接 ({self.p.host}:{self.p.port})')
        return False

    def buy(self, owner, data, size, price=None, exectype=None, **kwargs):
        """市价买入"""
        # TODO: self._xt.order_stock(code, xtconstant.STOCK_BUY, size, ...)
        print(f'[LiveBroker] BUY {data._name} {size}股')
        return super().buy(owner, data, size, price, exectype, **kwargs)

    def sell(self, owner, data, size, price=None, exectype=None, **kwargs):
        """市价卖出"""
        # TODO: self._xt.order_stock(code, xtconstant.STOCK_SELL, size, ...)
        print(f'[LiveBroker] SELL {data._name} {size}股')
        return super().sell(owner, data, size, price, exectype, **kwargs)

    def getposition(self, data):
        """查询持仓"""
        # TODO: self._xt.query_stock_position(code)
        return super().getposition(data)


def get_live_broker() -> LiveBroker:
    """创建实盘 Broker 实例"""
    return LiveBroker()
