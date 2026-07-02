"""
数据源适配层
- 封装原有 DataFeed（AkShare / 腾讯）
- 输出 backtrader 兼容的 PandasData
"""
import sys
import os
import pandas as pd
import backtrader as bt

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.feeds import DataFeed


def get_a_share_data(symbol: str, start: str = None, end: str = None
                     ) -> pd.DataFrame:
    """
    获取 A 股日线数据

    Returns:
        DataFrame 包含 open/high/low/close/volume，index 为 datetime
    """
    df = DataFeed.get_a_share_daily(symbol, start_date=start, end_date=end)
    df = df.rename(columns={
        'open': 'open', 'high': 'high', 'low': 'low',
        'close': 'close', 'volume': 'volume',
    })
    df.index.name = 'datetime'
    return df


def to_bt_feed(df: pd.DataFrame) -> bt.feeds.PandasData:
    """DataFrame → backtrader PandasData"""
    return bt.feeds.PandasData(
        dataname=df,
        datetime=None,          # 用 index
        open='open',
        high='high',
        low='low',
        close='close',
        volume='volume',
        openinterest=-1,        # A 股无持仓量
    )


def load_bt_data(symbol: str, start: str = None, end: str = '20260701'
                 ) -> bt.feeds.PandasData:
    """一步到位：获取数据并转成 backtrader feed"""
    df = get_a_share_data(symbol, start, end)
    return to_bt_feed(df)
