# OKX WebSocket 价格监控与交易API

这个项目包含了OKX交易所的WebSocket价格监控和REST API交易功能。

## 功能特性

### 价格监控 (okxWebSocketPrice.py)
- 实时监控OKX交易所的现货和合约价格
- 支持实盘和模拟盘环境
- 价格数据存储在全局字典中，方便其他程序调用
- 提供便捷的价格查询函数

### 交易API (okxTradingAPI.py)
- 支持现货和合约交易
- 支持买入、卖出、开仓、平仓等操作
- 支持限价单和市价单
- 支持全仓和逐仓模式
- 完整的账户信息查询功能


## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

项目会自动从 `OkxSettings.json` 文件中读取API配置信息。请确保该文件包含以下字段：

```json
{
  "ApiKey": "your_api_key_here",
  "SecretKey": "your_secret_key_here",
  "Passphrase": "your_passphrase_here",
  "IsSimulated": true,
  "ProxyUrl": "http://127.0.0.1:29290"
}
```

字段说明：
- `ApiKey`: OKX API密钥
- `SecretKey`: OKX API私钥
- `Passphrase`: OKX API口令
- `IsSimulated`: 是否使用模拟盘（true=模拟盘，false=实盘）
- `ProxyUrl`: 代理服务器地址（可选）

## 使用方法

### 1. 价格监控

```python
import asyncio
from okxWebSocketPrice import get_prices, get_price, priceDict

# 启动价格监控
asyncio.run(get_prices(['BTC-USDT', 'ETH-USDT'], demo=True))

# 在其他程序中获取价格
btc_price = get_price('BTC-USDT')
print(f"BTC价格: {btc_price}")

# 获取所有价格
all_prices = priceDict
```

### 2. 交易API

```python
import asyncio
from okxTradingAPI import OKXTradingAPI

async def trading_example():
    api = OKXTradingAPI(api_key, secret_key, passphrase, demo=True)
    
    # 现货买入
    result = await api.buy_spot('BTC-USDT', '0.001', '50000')
    
    # 合约开多仓
    result = await api.open_long('BTC-USD-SWAP', '1')
    
    # 获取余额
    balance = await api.get_balance()

asyncio.run(trading_example())
```


### 3. 主交易逻辑 (okxMain.py)

自动轮询所有配置交易对，每秒从WebSocket获取最新价格，判断开仓/平仓条件自动交易。
持仓状态自动根据账户余额判定，开仓后不会重复开仓，平仓后才允许再次开仓。
WebSocket行情断线自动3秒重连。

运行主交易逻辑：
```bash
python okxMain.py
```

主参数和交易对配置均在 `OkxSettings.json` 和 `TradingPairs.json` 文件中管理。

---
原有交互式交易机器人：
```bash
python tradingBot.py
```

## API接口说明

### 现货交易
- `buy_spot(symbol, amount, price=None)` - 现货买入
- `sell_spot(symbol, amount, price=None)` - 现货卖出

### 合约交易
- `open_long(symbol, amount, price=None)` - 开多仓
- `open_short(symbol, amount, price=None)` - 开空仓
- `close_long(symbol, amount, price=None)` - 平多仓
- `close_short(symbol, amount, price=None)` - 平空仓

### 账户查询
- `get_balance()` - 获取账户余额
- `get_positions()` - 获取持仓信息
- `get_pending_orders()` - 获取未成交订单

### 订单管理
- `place_order()` - 通用下单接口
- `cancel_order()` - 撤销订单
- `get_order()` - 获取订单详情

## 注意事项

⚠️ **风险提示**
1. 请在模拟盘环境下充分测试后再使用实盘
2. 妥善保管你的API密钥，不要泄露给他人
3. 建议设置合理的止损止盈策略
4. 量化交易存在风险，请谨慎操作

## 许可证

MIT License