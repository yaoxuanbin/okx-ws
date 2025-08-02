import asyncio
import json
import time
import hmac
import hashlib
import base64
import aiohttp
from datetime import datetime, timezone
from typing import Optional, Dict, Any

class OKXTradingAPI:
    """OKX交易API类，支持现货和合约交易"""
    
    def __init__(self, api_key: str, secret_key: str, passphrase: str, demo: bool = False, proxy_url: str = None):
        """
        初始化OKX交易API
        
        Args:
            api_key: API密钥
            secret_key: 密钥
            passphrase: 口令
            demo: 是否使用模拟盘环境
            proxy_url: 代理URL（可选）
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.demo = demo
        self.proxy_url = proxy_url
        
        # API基础URL
        if demo:
            self.base_url = "https://www.okx.com"  # 模拟盘
        else:
            self.base_url = "https://www.okx.com"  # 实盘
            
        # API端点
        self.endpoints = {
            'place_order': '/api/v5/trade/order',
            'cancel_order': '/api/v5/trade/cancel-order',
            'get_order': '/api/v5/trade/order',
            'get_orders': '/api/v5/trade/orders-pending',
            'get_balance': '/api/v5/account/balance',
            'get_positions': '/api/v5/account/positions'
        }
    
    def _sign(self, timestamp: str, method: str, request_path: str, body: str = '') -> str:
        """生成签名"""
        message = timestamp + method + request_path + body
        mac = hmac.new(
            bytes(self.secret_key, encoding='utf8'),
            bytes(message, encoding='utf-8'),
            digestmod='sha256'
        )
        return base64.b64encode(mac.digest()).decode()
    
    def _get_headers(self, method: str, request_path: str, body: str = '') -> Dict[str, str]:
        """获取请求头"""
        timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        signature = self._sign(timestamp, method, request_path, body)
        headers = {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
        if self.demo:
            headers['x-simulated-trading'] = '1'
        return headers
    
    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """发送API请求"""
        url = self.base_url + endpoint
        body = json.dumps(params) if params and method == 'POST' else ''
        headers = self._get_headers(method, endpoint, body)

        # 设置代理
        connector = None
        if self.proxy_url:
            connector = aiohttp.TCPConnector()

        async with aiohttp.ClientSession(connector=connector) as session:
            request_kwargs = {'headers': headers}
            if self.proxy_url:
                request_kwargs['proxy'] = self.proxy_url

            if method == 'GET':
                if params:
                    # 拼接查询字符串
                    from urllib.parse import urlencode
                    url += '?' + urlencode(params)
                async with session.get(url, **request_kwargs) as response:
                    return await response.json()
            elif method == 'POST':
                request_kwargs['data'] = body
                async with session.post(url, **request_kwargs) as response:
                    return await response.json()
    
    async def place_order(self, 
                         inst_id: str, 
                         trade_mode: str, 
                         side: str, 
                         order_type: str, 
                         size: str, 
                         price: Optional[str] = None,
                         reduce_only: bool = False,
                         pos_side: Optional[str] = None  # 新增
                         ) -> Dict[str, Any]:
        """
        下单
        
        Args:
            inst_id: 产品ID，如 BTC-USDT (现货) 或 BTC-USD-SWAP (合约)
            trade_mode: 交易模式 'cash'(现货) 'cross'(全仓) 'isolated'(逐仓)
            side: 订单方向 'buy' 或 'sell'
            order_type: 订单类型 'market'(市价) 'limit'(限价)
            size: 委托数量
            price: 委托价格（限价单必填）
            reduce_only: 是否只减仓（仅适用于合约）
        
        Returns:
            订单结果
        """
        params = {
            'instId': inst_id,
            'tdMode': trade_mode,
            'side': side,
            'ordType': order_type,
            'sz': size
        }
        
        if price:
            params['px'] = price
            
        if reduce_only:
            params['reduceOnly'] = 'true'
            
        if pos_side:
            params['posSide'] = pos_side  # 新增
            
        return await self._request('POST', self.endpoints['place_order'], params)
    
    async def cancel_order(self, inst_id: str, order_id: str) -> Dict[str, Any]:
        """
        撤销订单
        
        Args:
            inst_id: 产品ID
            order_id: 订单ID
            
        Returns:
            撤销结果
        """
        params = {
            'instId': inst_id,
            'ordId': order_id
        }
        
        return await self._request('POST', self.endpoints['cancel_order'], params)
    
    async def get_order(self, inst_id: str, order_id: str) -> Dict[str, Any]:
        """
        获取订单详情
        
        Args:
            inst_id: 产品ID
            order_id: 订单ID
            
        Returns:
            订单详情
        """
        params = {
            'instId': inst_id,
            'ordId': order_id
        }
        
        return await self._request('GET', self.endpoints['get_order'], params)
    
    async def get_pending_orders(self, inst_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取未成交订单
        
        Args:
            inst_id: 产品ID（可选）
            
        Returns:
            未成交订单列表
        """
        params = {}
        if inst_id:
            params['instId'] = inst_id
            
        return await self._request('GET', self.endpoints['get_orders'], params)
    
    async def get_balance(self) -> Dict[str, Any]:
        """
        获取账户余额
        
        Returns:
            账户余额信息
        """
        return await self._request('GET', self.endpoints['get_balance'])
    
    async def get_positions(self, inst_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取持仓信息
        
        Args:
            inst_id: 产品ID（可选）
            
        Returns:
            持仓信息
        """
        params = {}
        if inst_id:
            params['instId'] = inst_id
            
        return await self._request('GET', self.endpoints['get_positions'], params)
    
    # 便捷方法
    async def buy_spot(self, symbol: str, amount: str, price: Optional[str] = None) -> Dict[str, Any]:
        """
        现货买入
        
        Args:
            symbol: 交易对，如 'BTC-USDT'
            amount: 买入数量
            price: 买入价格（不填则市价买入）
            
        Returns:
            订单结果
        """
        return await self.place_order(
            inst_id=symbol,
            trade_mode='cash',
            side='buy',
            order_type='market',
            size=amount,
            price=price,
            tgtCcy="base_ccy"
        )
    
    async def sell_spot(self, symbol: str, amount: str, price: Optional[str] = None) -> Dict[str, Any]:
        """
        现货卖出
        
        Args:
            symbol: 交易对，如 'BTC-USDT'
            amount: 卖出数量
            price: 卖出价格（不填则市价卖出）
            
        Returns:
            订单结果
        """
        return await self.place_order(
            inst_id=symbol,
            trade_mode='cash',
            side='sell',
            order_type='market',
            size=amount,
            price=price,
            tgtCcy="base_ccy"
        )
    
    async def open_long(self, symbol: str, amount: str, price: Optional[str] = None, margin_mode: str = 'cross') -> Dict[str, Any]:
        """
        开多仓（合约）
        
        Args:
            symbol: 合约ID，如 'BTC-USD-SWAP'
            amount: 开仓数量
            price: 开仓价格（不填则市价开仓）
            margin_mode: 保证金模式 'cross'(全仓) 'isolated'(逐仓)
            
        Returns:
            订单结果
        """
        return await self.place_order(
            inst_id=symbol,
            trade_mode=margin_mode,
            side='buy',
            order_type='market',
            size=amount,
            price=price,
            pos_side='long'  # 新增
        )
    
    async def open_short(self, symbol: str, amount: str, price: Optional[str] = None, margin_mode: str = 'cross') -> Dict[str, Any]:
        """
        开空仓（合约）
        
        Args:
            symbol: 合约ID，如 'BTC-USD-SWAP'
            amount: 开仓数量
            price: 开仓价格（不填则市价开仓）
            margin_mode: 保证金模式 'cross'(全仓) 'isolated'(逐仓)
            
        Returns:
            订单结果
        """
        return await self.place_order(
            inst_id=symbol,
            trade_mode=margin_mode,
            side='sell',
            order_type='market',
            size=amount,
            price=price,
            pos_side='short'  # 新增
        )
    
    async def close_long(self, symbol: str, amount: str, price: Optional[str] = None, margin_mode: str = 'cross') -> Dict[str, Any]:
        """
        平多仓（合约）
        
        Args:
            symbol: 合约ID，如 'BTC-USD-SWAP'
            amount: 平仓数量
            price: 平仓价格（不填则市价平仓）
            margin_mode: 保证金模式 'cross'(全仓) 'isolated'(逐仓)
            
        Returns:
            订单结果
        """
        return await self.place_order(
            inst_id=symbol,
            trade_mode=margin_mode,
            side='sell',
            order_type='market',
            size=amount,
            price=price,
            reduce_only=True
        )
    
    async def close_short(self, symbol: str, amount: str, price: Optional[str] = None, margin_mode: str = 'cross') -> Dict[str, Any]:
        """
        平空仓（合约）
        
        Args:
            symbol: 合约ID，如 'BTC-USD-SWAP'
            amount: 平仓数量
            price: 平仓价格（不填则市价平仓）
            margin_mode: 保证金模式 'cross'(全仓) 'isolated'(逐仓)
            
        Returns:
            订单结果
        """
        return await self.place_order(
            inst_id=symbol,
            trade_mode=margin_mode,
            side='buy',
            order_type='market',
            size=amount,
            price=price,
            reduce_only=True
        )


# 使用示例
async def example_usage():
    """使用示例"""
    # 从配置文件加载API设置
    with open('OkxSettings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
    api_key = settings.get("ApiKey", "")
    secret_key = settings.get("SecretKey", "")
    passphrase = settings.get("Passphrase", "")
    demo = settings.get("IsSimulated", True)
    proxy_url=settings.get("ProxyUrl", None)
    
    # 初始化API
    api = OKXTradingAPI(
        api_key = api_key,
        secret_key = secret_key,
        passphrase = passphrase,
        demo = demo,
        proxy_url = proxy_url
    )
    
    try:
        # 获取账户余额
        # balance = await api.get_balance()
        # print("账户余额:", balance)
        
        # 现货买入BTC
        # buy_result = await api.buy_spot('DOGE-USDT', '100')
        # print("现货买入结果:", buy_result)
        
        # 合约开空仓
        short_result = await api.open_short('DOGE-USDT-SWAP', '0.1')
        print("开空仓结果:", short_result)
        
        # 获取持仓信息
        positions = await api.get_positions()
        print("持仓信息:", positions)
        
    except Exception as e:
        print(f"交易错误: {e}")


if __name__ == '__main__':
    # 运行示例
    asyncio.run(example_usage())
