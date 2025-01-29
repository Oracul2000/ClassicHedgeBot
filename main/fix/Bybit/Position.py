from fix.Bybit.bybitAPI import Client
from fix.Bybit.ErrorMessages import *


class Position:
    positionIdxMap = {'Buy': 1, 'Sell': 2}

    def __init__(self, cl: Client, symbol: str, side: str, leverage: int, max_loss_rel: float, bal: float, uid=-1) -> None:
        self.cl = cl
        self.symbol = symbol
        self.side = side
        self.leverage = leverage
        self.uid = uid
        self.price = None
        self.qty = None
        self.tp = None
        self.pnl = None
        self.unrealisedPnl = None
        self.max_loss_rel = max_loss_rel
        self.bal = bal

    def Update(self):
        positionIdx = self.positionIdxMap[self.side]
        resp = self.cl.position_price(symbol=self.symbol,
                                      positionIdx=positionIdx)
        for position in resp:
            if position['positionIdx'] == positionIdx:
                self.price = float(position['avgPrice'])
                self.tp = position['takeProfit']
                self.pnl = float(position['cumRealisedPnl'])
                if position['unrealisedPnl']:
                    self.unrealisedPnl = float(position['unrealisedPnl'])
                else:
                    self.unrealisedPnl = 0
                print(
                    f'\n{self.side}, {self.unrealisedPnl} \t {self.bal}, {self.max_loss_rel}, {self.bal * self.max_loss_rel}, \t{self.unrealisedPnl < - self.bal * abs(self.max_loss_rel)}\n')
                if self.unrealisedPnl < 0 and self.unrealisedPnl < - self.bal * abs(self.max_loss_rel):
                    # if True:
                    t = time.time()
                    import json
                    with open('main/tgmsgs/' + 'MaxLoss' + str(t), "w") as fp:
                        json.dump({
                            'Type': 'Max Loss',
                            'uid': self.uid,
                            'side': self.side,
                            'unPnL': self.unrealisedPnl
                        }, fp)
                try:
                    self.qty = float(position['positionValue'])
                except ValueError:
                    self.qty = 0

    def takeProfit(self, price, side):
        positionIdx = self.positionIdxMap[side]
        resp = self.cl.market_tp(symbol=self.symbol,
                                 price=price,
                                 positionIdx=positionIdx)
        self.tp = price

    def __repr__(self) -> str:
        return f'Position type: {type(self)}, price: {self.price}'


class ShortPosition(Position):
    def __init__(self, cl: Client, symbol: str, leverage: int, max_loss_rel: float, bal: float, uid=-1) -> None:
        super().__init__(cl, symbol, 'Sell', leverage, max_loss_rel, bal, uid)

    def Update(self):
        return super().Update()

    def takeProfit(self):
        super().Update()
        price = self.price * (1 - 0.1 / self.leverage)
        emsg = TPError(self.uid, {
            'symbol': self.symbol,
            'side': self.side,
            'position price': self.price,
            'tp price': price,
            'tp': self.tp,
            'pnl': self.pnl
        })
        emsg.publish()
        try:
            return super().takeProfit(price, 'Sell')
        except:
            emsg = TPError(self.uid, {
                'symbol': self.symbol,
                'side': self.side,
                'position price': self.price,
                'tp price': price,
                'tp': self.tp,
                'pnl': self.pnl
            })
            emsg.publish()
            if self.pnl > 0 and self.cl.kline_price(self.symbol)['price'] < self.price:
                return 0
                # return self.cl.market_close_short(self.symbol, str(self.qty / self.price))

    def takeProfit80(self):
        super().Update()
        price = self.price * (1 - 0.8 / self.leverage)
        return super().takeProfit(price, 'Sell')


class LongPosition(Position):
    def __init__(self, cl: Client, symbol: str, leverage: int, max_loss_rel: float, bal: float, uid=-1) -> None:
        super().__init__(cl, symbol, 'Buy', leverage, max_loss_rel, bal, uid)

    def Update(self):
        return super().Update()

    def takeProfit(self):
        super().Update()
        price = self.price * (1 + 0.1 / self.leverage)
        emsg = TPError(self.uid, {
            'symbol': self.symbol,
            'side': self.side,
            'position price': self.price,
            'tp price': price,
            'tp': self.tp,
            'pnl': self.pnl
        })
        emsg.publish()
        try:
            return super().takeProfit(price, 'Buy')
        except:
            emsg = TPError(self.uid, {
                'symbol': self.symbol,
                'side': self.side,
                'position price': self.price,
                'tp price': price,
                'tp': self.tp,
                'pnl': self.pnl
            })
            emsg.publish()
            if self.pnl > 0 and self.cl.kline_price(self.symbol)['price'] > self.price:
                return 0
                # return self.cl.market_close_long(self.symbol, str(self.qty / self.price))

    def takeProfit80(self):
        super().Update()
        price = self.price * (1 + 0.8 / self.leverage)
        return super().takeProfit(price, 'Buy')
