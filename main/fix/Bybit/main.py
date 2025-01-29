from fix.Bybit.Order import *
from fix.Bybit.bybitAPI import *
from fix.Bybit.config import *
from fix.Bybit.Dispatcher2 import Dispatcher
import asyncio


def start(apikey, secretkey, symbol, deposit, max_loss, uid=None, coef=None):
    cl = Client(apikey, secretkey)

    leverage = 20

    dp = Dispatcher(cl=cl, symbol=symbol, leverage=leverage,
                    depo=deposit, uid=uid, max_loss=max_loss)
    if coef:
        for i in dp.stepMap:
            dp.valueMap[i] *= float(coef)
    print(f'main.py max_loss = {max_loss}')
    asyncio.run(dp.asyncEngineStart())