"""
多源数据采集
- AkShare: A股历史K线、财务数据
- 腾讯财经: 实时行情 (A股/港股/美股)
- Yahoo Finance: 美股历史K线
"""

import time
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Literal


class DataFeed:
    """统一数据接口"""

    @staticmethod
    def get_a_share_daily(symbol: str, start_date: str = None, end_date: str = None,
                          adjust: str = 'qfq') -> pd.DataFrame:
        """
        获取A股日线数据

        Args:
            symbol: 股票代码，如 'sh600519' 或 '600519'
            start_date: 开始日期 'YYYYMMDD'
            end_date: 结束日期 'YYYYMMDD'
            adjust: 复权类型 'qfq'(前复权) / 'hfq'(后复权) / ''(不复权)
        """
        import akshare as ak

        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')

        # 标准化代码格式
        if not symbol.startswith(('sh', 'sz')):
            # 自动判断交易所
            code = symbol.zfill(6)
            if code.startswith(('6', '9')):
                symbol = f'sh{code}'
            else:
                symbol = f'sz{code}'

        df = ak.stock_zh_a_daily(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df

    @staticmethod
    def get_index_daily(symbol: str = 'sh000001') -> pd.DataFrame:
        """获取指数日线数据"""
        import akshare as ak
        df = ak.stock_zh_index_daily(symbol=symbol)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df

    @staticmethod
    def get_realtime(symbol: str, market: Literal['a', 'hk', 'us'] = 'a') -> dict:
        """
        获取实时行情 (腾讯财经API)

        Returns:
            dict: {name, price, change_pct, high, low, volume, pe, ...}
        """
        import subprocess
        import re

        prefix = {'a': 'sh', 'hk': 'hk', 'us': 'us'}
        code_map = {
            'a': symbol.zfill(6) if symbol.isdigit() else symbol,
            'hk': symbol.zfill(5),
            'us': symbol.upper()
        }
        code = f"{prefix[market]}{code_map[market]}"

        result = subprocess.run(
            ['curl', '-s', f'https://qt.gtimg.cn/q={code}'],
            capture_output=True, text=True, timeout=10
        )

        raw = result.stdout
        raw = subprocess.run(['iconv', '-f', 'GBK', '-t', 'UTF-8'],
                             input=raw, capture_output=True, text=True).stdout

        fields = raw.split('~')
        if len(fields) < 40:
            return {}

        if market == 'us':
            return {
                'name': fields[1],
                'price': float(fields[3]),
                'prev_close': float(fields[4]),
                'change': float(fields[31]),
                'change_pct': float(fields[32]),
                'high': float(fields[33]),
                'low': float(fields[34]),
                'volume': int(fields[36]) if fields[36] else 0,
                'pe': float(fields[39]) if fields[39] else None,
                'high_52w': float(fields[48]) if fields[48] else None,
                'low_52w': float(fields[49]) if fields[49] else None,
                'currency': fields[35],
            }
        elif market == 'hk':
            return {
                'name': fields[1],
                'price': float(fields[3]),
                'prev_close': float(fields[4]),
                'change': float(fields[31]),
                'change_pct': float(fields[32]),
                'high': float(fields[33]),
                'low': float(fields[34]),
                'volume': int(float(fields[36])) if fields[36] else 0,
                'pe': float(fields[39]) if fields[39] else None,
                'high_52w': float(fields[48]) if fields[48] else None,
                'low_52w': float(fields[49]) if fields[49] else None,
                'currency': fields[75] if len(fields) > 75 else 'HKD',
            }
        return {}

    @staticmethod
    def get_us_daily(symbol: str, months: int = 6) -> pd.DataFrame:
        """获取美股日线数据 (Yahoo Finance)"""
        import json
        import subprocess
        from datetime import datetime

        end = int(datetime.now().timestamp())
        start = int((datetime.now() - timedelta(days=months * 30)).timestamp())

        url = (f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}'
               f'?period1={start}&period2={end}&interval=1d')

        result = subprocess.run(
            ['curl', '-s', '-H', 'User-Agent: Mozilla/5.0', url],
            capture_output=True, text=True, timeout=15
        )

        data = json.loads(result.stdout)
        result = data['chart']['result'][0]
        ts = result['timestamp']
        quotes = result['indicators']['quote'][0]

        df = pd.DataFrame({
            'date': pd.to_datetime(ts, unit='s'),
            'open': quotes['open'],
            'high': quotes['high'],
            'low': quotes['low'],
            'close': quotes['close'],
            'volume': quotes['volume']
        })
        df.set_index('date', inplace=True)
        return df.dropna()
