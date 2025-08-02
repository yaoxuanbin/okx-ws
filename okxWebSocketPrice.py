import asyncio
import json
import websockets
from datetime import datetime

# OKX WebSocket公共地址
REAL_WS_URL = "wss://ws.okx.com:8443/ws/v5/public"
DEMO_WS_URL = "wss://wspap.okx.com:8443/ws/v5/public"  # 模拟盘

async def get_prices(symbols, demo=False):
    ws_url = DEMO_WS_URL if demo else REAL_WS_URL
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
                    print(f"{now} | {ticker['instId']} 最新价: {ticker['last']}")

if __name__ == '__main__':
    # 示例：不区分现货或合约；demo=True 表示使用模拟盘环境
    asyncio.run(get_prices(['BTC-USDT', 'ETH-USDT', 'BTC-USD-240830'], demo=True))
