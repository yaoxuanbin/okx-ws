import asyncio
import json
from okxWebSocketPrice import get_prices, get_price
from okxTradingAPI import OKXTradingAPI

# 读取交易对配置
with open('TradingPairs.json', 'r', encoding='utf-8') as f:
    trading_pairs = json.load(f)

# 读取API配置
with open('OkxSettings.json', 'r', encoding='utf-8') as f:
    settings = json.load(f)

api = OKXTradingAPI(
    api_key=settings['ApiKey'],
    secret_key=settings['SecretKey'],
    passphrase=settings['Passphrase'],
    demo=settings.get('IsSimulated', False),
    proxy_url=settings.get('ProxyUrl')
)

async def main_loop():
    # 获取所有需要订阅的交易对
    symbols = [pair['Spot'] for pair in trading_pairs] + [pair['Swap'] for pair in trading_pairs]
    # 启动WebSocket价格订阅（只启动一次）
    price_task = asyncio.create_task(get_prices(symbols, demo=settings.get('IsSimulated', False)))
    await asyncio.sleep(2)  # 等待价格初始化
    # 获取初始账户余额
    balance = await api.get_balance()
    # 构建持仓状态字典，spot>1且swap>=0.0001为True，否则为False
    position_dict = {}
    for pair in trading_pairs:
        spot = pair['Spot'].split('-')[0]  # 现货币种
        swap = pair['Swap'].split('-')[0]  # 合约币种
        spot_amt = 0
        swap_amt = 0
        # 解析余额数据
        if 'data' in balance and balance['data']:
            for acc in balance['data'][0].get('details', []):
                if acc['ccy'] == spot:
                    spot_amt = float(acc.get('availBal', 0))
                if acc['ccy'] == swap:
                    swap_amt = float(acc.get('availBal', 0))
        key = f"{pair['Spot']}_{pair['Swap']}"
        position_dict[key] = spot_amt > 1 and swap_amt >= 0.0001
    print("初始持仓状态:", position_dict)
    while True:
        for pair in trading_pairs:
            spot = pair['Spot']
            swap = pair['Swap']
            key = f"{spot}_{swap}"
            open_th = pair['OpenThreshold']
            close_th = pair['CloseThreshold']
            sell_level = pair['SellLevel']
            spot_qty = pair['SpotQuantity']
            swap_qty = pair['SwapQuantity']
            spot_price = get_price(spot)
            swap_price = get_price(swap)
            if not spot_price or not swap_price:
                continue
            # 计算价差，确保价格为float类型
            spot_val = float(spot_price['price'])
            swap_val = float(swap_price['price'])
            spread = (swap_val - spot_val) / spot_val
            # 开仓逻辑
            if not position_dict[key] and spread >= open_th:
                print(f"开仓: {spot} 买入 {spot_qty}, {swap} 卖出 {swap_qty}")
                await api.place_order(
                    inst_id=spot,
                    trade_mode='cash',
                    side='buy',
                    order_type='market',
                    size=str(spot_qty)
                )
                await api.place_order(
                    inst_id=swap,
                    trade_mode='cross',
                    side='sell',
                    order_type='market',
                    size=str(swap_qty),
                    pos_side='short'
                )
                position_dict[key] = True
            # 平仓逻辑
            elif position_dict[key] and spread <= close_th:
                print(f"平仓: {spot} 卖出 {spot_qty}, {swap} 买入 {swap_qty}")
                await api.place_order(
                    inst_id=spot,
                    trade_mode='cash',
                    side='sell',
                    order_type='market',
                    size=str(spot_qty)
                )
                await api.place_order(
                    inst_id=swap,
                    trade_mode='cross',
                    side='buy',
                    order_type='market',
                    size=str(swap_qty),
                    pos_side='short'
                )
                position_dict[key] = False
        await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(main_loop())
