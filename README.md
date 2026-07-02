# AllenTrader v2

模块化量化交易系统。服务端策略引擎 + 多数据源 + 报告自动发布。

## 架构

```
服务端 (阿里云)                    客户端 (Windows PC)
┌──────────────────────┐         ┌──────────────────┐
│ strategy/  策略引擎   │  信号   │ execution/        │
│ data/      数据采集   │  ───→  │   QMT / 同花顺OCR │
│ backtest/  回测验证   │  回报  │                   │
│ reports/   报告生成   │  ←───  │                   │
│ web/       Web展示    │        └──────────────────┘
└──────────────────────┘
         │
    allenqian.online
```

## 模块

| 模块 | 说明 | 状态 |
|------|------|------|
| `data/` | 多源数据采集 (AkShare/腾讯/Yahoo) | ✅ |
| `strategy/` | 策略引擎 (趋势/风控/信号) | 🏗 |
| `backtest/` | 回测引擎 | 🏗 |
| `execution/` | 执行层 (QMT/OCR) | ⏳ |
| `reports/` | HTML/PDF报告生成 | ✅ |
| `web/` | Web服务 (allenqian.online) | ✅ |

## 安装

```bash
pip install -r requirements.txt
```

## 使用

```bash
# 拉取行情
python main.py fetch --stock 600519

# 运行回测
python main.py backtest --strategy trend --start 20260101

# 生成报告
python main.py report --stock 600519

# 启动Web
python main.py serve
```
