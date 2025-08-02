import asyncio
import json
import websockets
from datetime import datetime

# OKX WebSocket公共地址
REAL_WS_URL = "wss://ws.okx.com:8443/ws/v5/public"
DEMO_WS_URL = "wss://wspap.okx.com:8443/ws/v5/public"  # 模拟盘

# 公共价格字典，存储最新价格数据
priceDict = {}

async def get_prices(symbols, demo=False):
    ws_url = DEMO_WS_URL if demo else REAL_WS_URL
    while True:
        try:
            async with websockets.connect(ws_url) as ws:
                subs = [
                    {"channel": "tickers", "instId": symbol}
                    for symbol in symbols
                ]
                sub_msg = {
                    "op": "subscribe",
                    "args": subs
                }
                await ws.send(json.dumps(sub_msg))

                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    if 'data' in data:
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        for ticker in data['data']:
                            # 更新价格字典
                            priceDict[ticker['instId']] = {
                                'price': ticker['last'],
                                'timestamp': now
                            }
                            print(f"{now} | {ticker['instId']} 最新价: {ticker['last']}")
        except Exception as e:
            print(f"WebSocket断开，3秒后重连: {e}")
            await asyncio.sleep(3)

def get_price(symbol):
    """获取指定交易对的最新价格
    
    Args:
        symbol (str): 交易对名称，如 'BTC-USDT'
        
    Returns:
        dict: 包含价格和时间戳的字典，如果没有数据则返回 None
    """
    return priceDict.get(symbol)

def get_all_prices():
    """获取所有交易对的最新价格
    
    Returns:
        dict: 包含所有价格数据的字典
    """
    return priceDict.copy()

if __name__ == '__main__':
    # 示例：不区分现货或合约；demo=True 表示使用模拟盘环境
    asyncio.run(get_prices(['BTC-USDT', 'ETH-USDT', 'BTC-USD-SWAP'], demo=True))
