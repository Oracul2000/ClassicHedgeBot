from fix.Bybit.bybitAPI import Client
from fix.Bybit.Order import *
from fix.Bybit.Position import *

import asyncio


class Dispatcher:
    valueMap = {1: 0.2,
                2: 0.2,
                3: 0.4,
                4: 0.8,
                5: 1.6,
                6: 3.2,
                7: 6.4,
                8: 12.8}

    stepMap = {1: 0,
               2: 0.3,
               3: 0.8,
               4: 1.8,
               5: 3.2,
               6: 6,
               7: 10,
               8: 15}

    def __init__(self, cl: Client, symbol: str, leverage: int, depo: float, uid=None, max_loss=20) -> None:
        self.cl = cl
        self.symbol = symbol
        self.leverage = leverage
        self.cl.set_leverage(self.symbol, self.leverage)
        self.depo = depo / (100 / self.leverage)
        self.uid = uid
        self.max_loss_rel = max_loss / 100
        print(
            f'Dispetcher 2, __init__, self.max_loss_rel = {self.max_loss_rel}')
        self.bal = 0

    def tokenPrice(self) -> float:
        return self.cl.kline_price(self.symbol)['price']

    async def shortAlgo(self):
        startPrice = self.tokenPrice()
        step = 1
        baseDepo = self.depo / startPrice

        position = ShortPosition(
            self.cl, self.symbol, self.leverage, self.max_loss_rel, self.bal, self.uid)
        position.Update()
        if position.price != 0:
            limitOrder = ShortLimitOrder(self.cl, self.symbol)
            limitOrder.findncancel()
            start_qty = baseDepo * self.valueMap[1]
            startValueUsdt = start_qty * startPrice
            ratio = position.qty / startValueUsdt
            from math import log
            step = round(log(ratio, 2), 0) + 1
            if step <= 7:
                position.takeProfit()

            marketOrder = ShortMarketOrder(self.cl, self.symbol)
            marketOrder.price = position.price
        else:
            qty = baseDepo * self.valueMap[1]
            marketOrder = ShortMarketOrder(self.cl, self.symbol)
            marketOrder.open(qty)
            position = ShortPosition(
                self.cl, self.symbol, self.leverage, self.max_loss_rel, self.bal, self.uid)
            position.Update()
            position.takeProfit()

        limitQty = baseDepo * self.valueMap[step + 1]

        limitPrice = marketOrder.price * (1 + self.stepMap[step + 1] / 100)
        limitOrder = ShortLimitOrder(self.cl, self.symbol)
        limitOrder.open(position.qty / limitPrice, limitPrice)
        await asyncio.sleep(1)

        while True:
            limitOrder.Update()
            position.Update()
            if position.price == 0:
                limitOrder.findncancel()
                return
            if not position.tp:
                position.takeProfit()
                self.tprecoveryMSG()
            if limitOrder.status == 'Cancelled' and step < 7:
                self.limitrecoveryMSG()
                limitPrice = limitOrder.price
                limitQty = limitOrder.qty
                limitOrder = ShortLimitOrder(self.cl, self.symbol)
                limitOrder.open(limitQty, limitPrice)
                limitOrder.Update()

            if limitOrder.status == 'Filled' and step < 7:
                position.Update()
                position.takeProfit()
                limitOrder.findncancel()
                step += 1

                limitQty = baseDepo * self.valueMap[step + 1]
                limitPrice = marketOrder.price * \
                    (1 + self.stepMap[step + 1] / 100)
                limitOrder = ShortLimitOrder(self.cl, self.symbol)
                limitOrder.open(position.qty / limitPrice, limitPrice)
                limitOrder.Update()
            if limitOrder.status == 'Filled' and step == 7:
                position.takeProfit80()
                step += 1
                continue
            await asyncio.sleep(1)

    async def longAlgo(self):
        startPrice = self.tokenPrice()
        step = 1
        baseDepo = self.depo / startPrice

        position = LongPosition(
            self.cl, self.symbol, self.leverage, self.max_loss_rel, self.bal, self.uid)
        position.Update()
        if position.price != 0:
            position.takeProfit()
            limitOrder = LongLimitOrder(self.cl, self.symbol)
            limitOrder.findncancel()
            start_qty = baseDepo * self.valueMap[1]
            startValueUsdt = start_qty * startPrice
            ratio = position.qty / startValueUsdt
            from math import log
            step = round(log(ratio, 2), 0) + 1
            marketOrder = LongMarketOrder(self.cl, self.symbol)
            marketOrder.price = position.price
        else:
            qty = baseDepo * self.valueMap[1]
            marketOrder = LongMarketOrder(self.cl, self.symbol)
            marketOrder.open(qty)
            position = LongPosition(
                self.cl, self.symbol, self.leverage, self.max_loss_rel, self.bal, self.uid)
            position.Update()
            position.takeProfit()

        limitQty = baseDepo * self.valueMap[step + 1]
        limitPrice = marketOrder.price * (1 - self.stepMap[step + 1] / 100)
        limitOrder = LongLimitOrder(self.cl, self.symbol)
        limitOrder.open((position.qty) / limitPrice, limitPrice)
        await asyncio.sleep(1)

        while True:
            limitOrder.Update()
            position.Update()
            if position.price == 0:
                limitOrder.findncancel()
                return
            if not position.tp:
                position.takeProfit()
                self.tprecoveryMSG()
            if limitOrder.status == 'Cancelled' and step < 7:
                self.limitrecoveryMSG()

                limitPrice = limitOrder.price
                limitQty = limitOrder.qty
                limitOrder = LongLimitOrder(self.cl, self.symbol)
                limitOrder.open(limitQty, limitPrice)
                limitOrder.Update()
                print('\n', position, '\n', limitOrder)

            if limitOrder.status == 'Filled' and step < 7:
                position.Update()
                position.takeProfit()
                limitOrder.findncancel()
                step += 1

                limitQty = baseDepo * self.valueMap[step + 1]
                limitPrice = marketOrder.price * \
                    (1 - self.stepMap[step + 1] / 100)
                limitOrder = LongLimitOrder(self.cl, self.symbol)
                limitOrder.open(position.qty / limitPrice, limitPrice)
                limitOrder.Update()
            if limitOrder.status == 'Filled' and step == 7:
                position.takeProfit80()
                step += 1
                continue
            await asyncio.sleep(1)

    async def shortLoop(self):
        while True:
            self.cl.cancel_all_limit_orders(self.symbol, 'Sell')
            try:
                await self.shortAlgo()
            except BaseException as e:
                pass
            await asyncio.sleep(1)

            self.checkPnL("Buy")

    async def longLoop(self):
        while True:
            self.cl.cancel_all_limit_orders(self.symbol, 'Buy')
            try:
                await self.longAlgo()
            except BaseException as e:
                print(e)
            await asyncio.sleep(1)

            self.checkPnL("Sell")

    def checkPnL(self, side):
        closedPnL = self.cl.get_closed_PnL_symbol(self.symbol)[
            'result']['list']
        for pos in closedPnL:
            if pos['side'] == side:
                pnlvalue = float(pos['closedPnl'])
                if pnlvalue < 0:
                    tgmsg = {
                        'Type': "PnL",
                        'User Id': self.uid,
                        'symbol': self.symbol,
                        'PnL': pnlvalue
                    }
                    import json
                    import time

                    t = time.time()
                    with open('main/tgmsgs/' + str(t), "w") as fp:
                        json.dump(tgmsg, fp)
                    break
                break

    def tprecoveryMSG(self):
        tgmsg = {
            'Type': "TakeProfit",
            'User Id': self.uid,
            'symbol': self.symbol,
        }
        import json
        import time

        t = time.time()
        with open('main/tgmsgs/' + str(t), "w") as fp:
            json.dump(tgmsg, fp)

    def limitrecoveryMSG(self):
        tgmsg = {
            'Type': "Limit",
            'User Id': self.uid,
            'symbol': self.symbol,
        }
        import json
        import time

        t = time.time()
        with open('main/tgmsgs/' + str(t), "w") as fp:
            json.dump(tgmsg, fp)

    def geventEngineStart(self):
        import gevent

        gevent.joinall([
            gevent.spawn(self.shortLoop),
            gevent.spawn(self.longAlgo)
        ])

    async def asyncEngineStart(self):
        self.cl.switch_position_mode(self.symbol, 3)

        self.bal = self.cl.get_balance_wrapped()
        # self.bal = 50
        print(f'asyncEngineStart, self.bal = {self.bal}')

        task1 = asyncio.create_task(self.longLoop())
        task2 = asyncio.create_task(self.shortLoop())

        await task1
        await task2
