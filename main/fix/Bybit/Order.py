from fix.Bybit.bybitAPI import Client


class Order:
    roundationMap = {
        "XRPUSDT": 0,
        "DOGEUSDT": 0,
        "BTCUSDT": 3,
        "ETHUSDT": 2,
        "ADAUSDT": 0,
        "LINKUSDT": 1,
        "XLMUSDT": 0,
        "DASHUSDT": 2,
        "NEOUSDT": 2,
        "TRXUSDT": 0,
        "EOSUSDT": 1,
        "LTCUSDT": 1,
        "APTUSDT": 2,
        "ATOMUSDT": 0
    }

    positionIdxMap = {'Buy': 1, 'Sell': 2}
    
    def __init__(self, cl: Client, symbol: str) -> None:
        self.cl = cl
        self.symbol = symbol
        self.orderId = None
        self.status = None
        self.price = None
        self.qty = None
        self.roundation = self.roundationMap[self.symbol]
        self.group = None

    def __repr__(self) -> str:
        return f'Order type: {type(self)} {self.orderId}, qty: {self.qty}, status: {self.status}, price: {self.price}'

    def open(self, resp):
        self.status = resp['status']
        if self.status:
            self.orderId = resp['orderId']
        self.Update() 


    def Update(self):
        resp = self.cl.order_price(self.orderId)
        self.status = resp['orderStatus']
        try:
            self.qty = float(resp['qty'])
        except ValueError:
            pass
        try:
            self.price = float(resp['price'])
        except ValueError:
            pass

class MarketOrder(Order):
    def __init__(self, cl, symbol) -> None:
        super().__init__(cl, symbol)

    def open(self, qty, side):
        qty = round(qty, self.roundation)
        resp = self.cl.market_open_order(symbol=self.symbol,
                                  side=side,
                                  qty=qty)
        super().open(resp)

class ShortMarketOrder(MarketOrder):
    def open(self, qty):
        return super().open(qty, 'Sell')
    

class LongMarketOrder(MarketOrder):
    def open(self, qty):
        return super().open(qty, 'Buy')
        

class LimitOrder(Order):
    def __init__(self, cl: Client, symbol: str) -> None:
        super().__init__(cl, symbol)

    def open(self, qty, side, price):
        qty = round(qty, self.roundation)
        resp = self.cl.limit_open_order(symbol=self.symbol,
                                        side=side,
                                        qty=qty,
                                        price=price)
        super().open(resp)
        self.price = price

    def find(self, side) -> list:
        positionidx = self.positionIdxMap[side]
        resp = self.cl.all_orders(self.symbol)
        orders = []
        for order in resp:
            if order['orderType'] == 'Limit' and order['side'] == side and order['positionIdx'] == positionidx and order['orderStatus'] == 'New':
                orders.append(order)
        return orders
    
    def cancel(self):
        resp = self.cl.cancel_order(self.symbol, self.orderId)
        self.Update()

    def partional_orders(self, side):
        resp = self.cl.get_all_partionally_filled_orders(self.symbol, side)
        qty = 0
        for i in resp:
            qty += float(i['cumExecValue'])
            self.cl.cancel_order(self.symbol, i['orderId'])
        return qty
    
    # def findncancel(self, side):
    #     positionidx = self.positionIdxMap[side]
    #     resp = self.cl.all_orders(self.symbol)
    #     orders = []
    #     for order in resp:
    #         if order['orderType'] == 'Limit' and order['side'] == side and order['positionIdx'] == positionidx and order['orderStatus'] == 'New':
    #             resp = self.cl.cancel_order(self.symbol, order['orderId'])
    #     self.Update()

    def findncancel(self, side):
        resp = self.cl.cancel_all_limit_orders(self.symbol, side)
        self.Update
        return resp


class ShortLimitOrder(LimitOrder):
    def __init__(self, cl: Client, symbol: str) -> None:
        super().__init__(cl, symbol)

    def open(self, qty, price):
        return super().open(qty, 'Sell', price)
    
    def findncancel(self):
        return super().findncancel('Sell')
    
    def partional_orders(self):
        return super().partional_orders('Sell')
    

class LongLimitOrder(LimitOrder):
    def __init__(self, cl: Client, symbol: str) -> None:
        super().__init__(cl, symbol)

    def open(self, qty, price):
        return super().open(qty, 'Buy', price)
    
    def findncancel(self):
        return super().findncancel('Buy')
    
    def partional_orders(self):
        return super().partional_orders('Buy')
    
    