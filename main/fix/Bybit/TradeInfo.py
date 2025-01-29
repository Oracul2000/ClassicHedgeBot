from fix.Bybit.bybitAPI import *


coins = ['ADA', 'LINK', 'XRP', 'XLM', 'DASH', 'NEO',
         'TRX', 'EOS', 'LTC', 'DOGE', 'APT', 'ATOM']


class SmallPosition():
    symbol = ''
    positions = 0
    orders = 0
    tps = 0

    def __repr__(self) -> str:
        return f'{self.symbol}: Позиций: {self.positions}, Ордеров: {self.orders}, ТП: {self.tps}'


class SmallBybit():
    def __init__(self, apikey, secretkey) -> None:
        self.apikey = apikey
        self.secretkey = secretkey
        self.pairs = {}  # symbol: SmallPosition
        self.cl = Client(apikey, secretkey)

        self.coinControl = {}

        self.balance = 0
        self.apiStatus = None

    def get_balance(self):
        response = self.cl.get_balance()
        self.balance = float(response['result']['list'][0]['totalEquity'])

    def get_positions(self, symbol):
        response = self.cl.position_price(symbol, 1)
        sp = SmallPosition()
        sp.symbol = symbol
        for pos in response:
            if pos['avgPrice'] and pos['avgPrice'] != '0':
                sp.positions += 1
            if pos['takeProfit']:
                sp.tps += 1
        self.coinControl[symbol] = sp

    def get_limits(self, symbol):
        response = self.cl.all_orders(symbol)
        if response:
            self.coinControl[symbol].orders = len(
                response) - self.coinControl[symbol].tps

    def endnclose(self, symbol):
        resp = self.cl.position_size_sell(symbol)
        status = 'Sell'
        d = {'Sell': 2, 'Buy': 1}
        for pos in resp['result']['list']:
            if pos['positionIdx'] == d[status]:
                psize = pos['size']
                if psize != "0":
                    self.cl.market_close_short(symbol, psize)

        status = 'Buy'
        for pos in resp['result']['list']:
            if pos['positionIdx'] == d[status]:
                psize = pos['size']
                if psize != "0":
                    self.cl.market_close_long(symbol, psize)
        self.cl.cancel_all_limit_orders(symbol, 'Buy')
        self.cl.cancel_all_limit_orders(symbol, 'Sell')

    def endnequal(self, symbol):
        resp = self.cl.position_size_sell(symbol)

        # {'Sell': 2, 'Buy': 1}[side]

        class SmallPos:
            def __init__(self, positionIdx, size):
                self.positionIdx = positionIdx
                self.size = size

        poses = {}

        for pos in resp['result']['list']:
            print(pos)
            print()
            poses[pos['positionIdx']] = SmallPos(
                int(pos['positionIdx']), float(pos['size']))
        print()

        print(poses[1].size, poses[2].size)

        if poses[1].size > poses[2].size:
            self.cl.market_open_order(
                symbol=symbol,
                side='Sell',
                qty=poses[1].size - poses[2].size
            )
        else:
            self.cl.market_open_order(
                symbol=symbol,
                side='Buy',
                qty=poses[2].size - poses[1].size
            )

    def update(self, a):
        # return 0
        try:
            self.get_balance()
            self.apiStatus = True

            self.get_positions(a.symbol + 'USDT')

            self.get_limits(a.symbol + 'USDT')
        except BaseException:
            self.apiStatus = False

    def monitoring(self):
        answer = ""
        for i in self.coinControl:
            if "Позиций: 0" not in str(self.coinControl[i]):
                answer += str(self.coinControl[i]) + '\n'
        return answer

    def statistics(self, symbol, startTime=None, stopTime=None):
        import time
        import datetime

        delta = 1070744400000 - 1070226000000
        startms = int(time.mktime(datetime.datetime.strptime(
            startTime, "%d.%m.%Y").timetuple())) * 1000
        stopms = int(time.mktime(datetime.datetime.strptime(
            stopTime, "%d.%m.%Y").timetuple())) * 1000
        tr = []
        for i in range(startms, stopms, delta):
            response = self.cl.get_closed_PnL(
                symbol, i, min(i + delta, stopms))['result']['list']
            tr += response

        import pandas as pd
        import datetime
        df = pd.DataFrame(tr)
        df["updatedTime"] = [datetime.datetime.fromtimestamp(
            int(i) / 1000.0) for i in df["updatedTime"]]
        df["createdTime"] = [datetime.datetime.fromtimestamp(
            int(i) / 1000.0) for i in df["createdTime"]]
        df["closedPnl"] = [i.replace('.', ',') for i in df["closedPnl"]]
        df.to_csv('out.csv', index=False)
