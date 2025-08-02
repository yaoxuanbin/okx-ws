import asyncio
import json
import websockets

# OKX WebSocket公共地址
REAL_WS_URL = "wss://ws.okx.com:8443/ws/v5/public"
DEMO_WS_URL = "wss://wspap.okx.com:8443/ws/v5/public"  # 模拟盘

async def get_prices(symbols, is_future=False, demo=False):
    ws_url = DEMO_WS_URL if demo else REAL_WS_URL
    async with websockets.connect(ws_url) as ws:
        subs = []
        for symbol in symbols:
            if is_future:
                # 合约频道
                subs.append({
                    "channel": "tickers",
                    "instId": symbol,
                })
            else:
                # 现货频道
                subs.append({
                    "channel": "tickers",
                    "instId": symbol,
                })
        # 订阅请求
        sub_msg = {
            "op": "subscribe",
            "args": subs
        }
        await ws.send(json.dumps(sub_msg))

        # 循环接收消息
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if 'data' in data:
                for ticker in data['data']:
                    print(f"{ticker['instId']} 最新价: {ticker['last']} ({'合约' if is_future else '现货'})")

if __name__ == '__main__':
    # 示例：BTC-USDT 和 ETH-USDT 现货，demo=True为模拟交易环境
    asyncio.run(get_prices(['BTC-USDT', 'ETH-USDT'], is_future=False, demo=True))
    # 示例：BTC-USD-240830 合约，demo=False为正式环境
    # asyncio.run(get_prices(['BTC-USD-240830'], is_future=True, demo=False))
