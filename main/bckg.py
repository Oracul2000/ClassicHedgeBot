import asyncio
import os
import json
import psutil

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fix.Bybit import TradeInfo

from database.models import user


engine = create_engine("sqlite:///Data.db", echo=True)


allowed_users = [348691698, 540862463, 925216062]


async def newreports(bot):
    while True:
        await asyncio.sleep(1)
        reports = os.listdir('./main/tgmsgs/')
        for report in reports:
            d = {}
            with open('./main/tgmsgs/' + report, 'rt') as f:
                d = json.loads(f.read())
            for u in allowed_users:
                try:
                    if d['Type'] == 'PnL':
                        await bot.send_message(str(u), PnLReport(d))
                    if d['Type'] == 'TakeProfit':
                        await bot.send_message(str(u), TakeProfitReport(d))
                    if d['Type'] == 'Limit':
                        await bot.send_message(str(u), LimitReport(d))
                    if d['Type'] == 'Max Loss':
                        await bot.send_message(str(u), str(d))

                        try:
                            with Session(engine) as session:
                                a = session.query(user.API).filter(
                                    user.API.id == int(d["uid"])).all()[0]
                                p = psutil.Process(int(a.pid))
                                p.terminate()
                        except BaseException:
                            print("Error")

                        with Session(engine) as session:
                            print(d)
                            print(type(d))
                            print(d['uid'])
                            u = session.query(user.API).filter(
                                user.API.id == d['uid']).all()[0]
                            ti = TradeInfo.SmallBybit(
                                u.bybitapi, u.bybitsecret)
                            ti.endnequal(u.symbol + 'USDT')
                    else:
                        await bot.send_message(str(u), str(d))
                except Exception as e:
                    print(f'async def newreports(bot): {e}', d, report)
                    pass
            os.remove('./main/tgmsgs/' + report)


def PnLReport(d):
    return f'Внимание! Отрицательный PnL!\nПользователь: {d["User Id"]}\nМонета: {d["symbol"]}\nPnL: {d["PnL"]}'


def LimitReport(d):
    return f'Внимание. Лимитный ордер восстановлен.\nПользователь: {d["User Id"]}\nМонета: {d["symbol"]}'


def TakeProfitReport(d):
    return f'Внимание. Take Profit ордер восстановлен.\nПользователь: {d["User Id"]}\nМонета: {d["symbol"]}'
