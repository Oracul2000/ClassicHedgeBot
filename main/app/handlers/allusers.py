import asyncio
from typing import Text
from aiogram import Dispatcher, types
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardMarkup
from app.keyboards.simple_row import make_row_keyboard, make_inline_keyboard
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards import buttons

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
# from ..database.models import user
from database.models import user
from msgs import msgs
from app.keyboards import buttons
from fix.Bybit import Dispatcher, TradeInfo

from multiprocessing import Process
import psutil


engine = create_engine("sqlite:///Data.db", echo=True)


router = Router()

coins = ['ADA', 'LINK', 'XRP', 'XLM', 'DASH', 'NEO', 'TRX',
         'EOS', 'LTC', 'DOGE', 'APT', 'ATOM', 'BTC', 'ETH']
tasks = {}


class ByBitStart(StatesGroup):
    uid = State()
    symbol = State()
    deposit = State()
    stop = State()
    uservalue = State()
    gofromadding = State()
    beforedate = State()
    afterdate = State()
    statistics = State()


@router.message(Command("monitoring"))
@router.callback_query(F.data == "monitoring")
async def monitoring(callback: types.CallbackQuery, state: FSMContext):
    with Session(engine) as session:
        all_users = session.query(user.User).all()
        textanswer = ""
        for u in all_users:
            textanswer += msgs.useroutput(u) + '\n'
            for a in u.apis:
                ti = TradeInfo.SmallBybit(a.bybitapi, a.bybitsecret)
                ti.update(a)
                textanswer += msgs.apimonitoringoutput(a, ti)

        try:
            await callback.message.answer(
                text=textanswer,
            )
            await callback.message.answer(
                text="Введите порядковый номер пользователя"
            )
        except Exception:
            await callback.answer(
                text=textanswer,
            )
            await callback.answer(
                text="Введите порядковый номер пользователя"
            )
    await state.set_state(ByBitStart.uid.state)


@router.message(Command("user"))
@router.callback_query(F.data == "user")
async def user_by_id(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer(
        text="Введите порядковый номер пользователя"
    )
    await state.set_state(ByBitStart.uid.state)


@router.message(Command("all_users"))
@router.callback_query(F.data == "all_users")
async def allusers(callback: types.CallbackQuery, state: FSMContext):
    with Session(engine) as session:
        all_users = session.query(user.User).all()
        textanswer = ""
        for u in all_users:
            textanswer += msgs.useroutput(u) + '\n'

        try:
            await callback.message.answer(
                text=textanswer,
            )
            await callback.message.answer(
                text="Введите порядковый номер пользователя"
            )
        except Exception:
            await callback.answer(
                text=textanswer,
            )
            await callback.answer(
                text="Введите порядковый номер пользователя"
            )
    await state.set_state(ByBitStart.uid.state)


@router.callback_query(F.data.startswith("delete_user_"))
async def delete_user(callback: types.CallbackQuery, state: FSMContext):
    uid = int(callback.data.split('_')[2])
    with Session(engine) as session:
        session.query(user.User).filter(user.User.id == uid).delete()
        session.commit()
    await callback.message.answer("Пользователь удален")


@router.callback_query(F.data.startswith("delete_api_"))
async def delete_api(callback: types.CallbackQuery, state: FSMContext):
    aid = int(callback.data.split('_')[2])
    with Session(engine) as session:
        session.query(user.API).filter(user.API.id == aid).delete()
        session.commit()
    await callback.message.answer("Монета удалена")


@router.message(ByBitStart.uid)
async def bybitdeposiot(message: types.Message, state: FSMContext):
    await state.update_data(uid=int(message.text.lower()))
    user_data = await state.get_data()
    with Session(engine) as session:
        u = session.query(user.User).filter(
            user.User.id == int(user_data["uid"])).all()[0]
        text = f'Параметры пользователя {u.name}#{u.id}\n'
        for a in u.apis:
            ti = TradeInfo.SmallBybit(a.bybitapi, a.bybitsecret)
            ti.update(a)
            text += msgs.userbigouput(a, ti)
        builder = InlineKeyboardBuilder()
        builder.add(buttons.TRAIDING_PAIRS(u.id))
        builder.add(buttons.DELETEUSER(u.id))
        builder.add(buttons.STATISTIS)
        await message.answer(text=text,
                             reply_markup=builder.as_markup())


async def bybitdeposiotclone(message: types.Message, state: FSMContext):
    # await state.update_data(uid=int(uid))
    await asyncio.sleep(20)
    user_data = await state.get_data()
    with Session(engine) as session:
        u = session.query(user.User).filter(
            user.User.id == int(user_data["uid"])).all()[0]
        text = f'Параметры пользователя {u.name}#{u.id}\n'
        for a in u.apis:
            ti = TradeInfo.SmallBybit(a.bybitapi, a.bybitsecret)
            ti.update(a)
            text += msgs.userbigouput(a, ti)
        builder = InlineKeyboardBuilder()
        builder.add(buttons.TRAIDING_PAIRS(u.id))
        builder.add(buttons.STATISTIS)
        await message.answer(text=text,
                             reply_markup=builder.as_markup())


async def bybitdeposiotcloneCB(callback: types.CallbackQuery, state: FSMContext):
    # await state.update_data(uid=int(uid))
    await asyncio.sleep(20)
    user_data = await state.get_data()
    with Session(engine) as session:
        u = session.query(user.User).filter(
            user.User.id == int(user_data["uid"])).all()[0]
        text = f'Параметры пользователя {u.name}#{u.id}\n'
        for a in u.apis:
            ti = TradeInfo.SmallBybit(a.bybitapi, a.bybitsecret)
            ti.update(a)
            text += msgs.userbigouput(a, ti)
        builder = InlineKeyboardBuilder()
        builder.add(buttons.TRAIDING_PAIRS(u.id))
        builder.add(buttons.STATISTIS)
        await callback.message.answer(text=text,
                                      reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("traiding_pairs_"))
async def traidingpairs2(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    with Session(engine) as session:
        u = session.query(user.User).filter(
            user.User.id == int(callback.data.split('_')[2])).all()[0]
        text = 'Торговые пары\n\nАктивные пары: '
        for a in u.apis:
            text += str(a.symbol) + 'USDT, '
        text += '\nВыберите пару для торговли'
        builder = InlineKeyboardBuilder()
        builder.add(buttons.ACTIVE_PAIRS(u.id))
        builder.add(buttons.ADD_TRAIDINGPAIR(u.id))

        await callback.message.answer(text=text,
                                      reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("addtraiding_pairs_"))
async def addtraidingpairs(callback: types.CallbackQuery, state: FSMContext):
    uid = int(callback.data.split('_')[2])
    with Session(engine) as session:
        u = session.query(user.User).all()[0]
    from app.handlers.adduser import namechosenclone
    await namechosenclone(u.name, callback, state)


@router.callback_query(F.data.startswith("active_pairs_"))
async def activepairs(callback: types.CallbackQuery, state: FSMContext):
    uid = int(callback.data.split('_')[2])
    with Session(engine) as session:
        builder = InlineKeyboardBuilder()
        u = session.query(user.User).filter(user.User.id == uid).all()[0]
        for a in u.apis:
            builder.add(buttons.COINAPI(a.id, a.symbol))
        #     builder.add(buttons.COIN1(a.symbol))
        await state.set_state(ByBitStart.symbol)
        await callback.message.answer(text="Выберите активную пару",
                                      reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("bybit_choosestrat_"))
async def choose_strat(callback: types.CallbackQuery, state: FSMContext):
    uid = int(callback.data.split('_')[2])
    builder = InlineKeyboardBuilder()
    builder.add(buttons.STRATEGY_CONSERVO())
    builder.add(buttons.STRATEGY_AGRESSIVE())
    builder.add(buttons.STRATEGY_PROF())
    await callback.message.answer(text="Выберите активную пару",
                                  reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("strategy_"))
async def strat(callback: types.CallbackQuery, state: FSMContext):
    strat = callback.data.split('_')[1]
    if strat == 'conservo':
        await start_wrapper(state, callback, 0.2)
        await bybitdeposiotcloneCB(callback, state)
    if strat == 'agressive':
        await start_wrapper(state, callback, 0.4)
        await bybitdeposiotcloneCB(callback, state)
    if strat == 'prof':
        await callback.message.answer(text='Введите % первого ордера')
        await state.set_state(ByBitStart.uservalue)


@router.message(ByBitStart.uservalue)
async def uservalue(message: types.Message, state: FSMContext):
    await state.update_data(multiplier=message.text)

    multiplier = float(message.text)
    await start_wrapper(state, coef=multiplier)
    await bybitdeposiotclone(message, state)


async def start_wrapper(state, callback=None, coef=1):
    user_data = await state.get_data()
    with Session(engine) as session:
        u = session.query(user.API).filter(
            user.API.id == int(user_data["aid"])).all()[0]

        from fix.Bybit.main import start
        nc = coef / 0.2
        p = Process(target=start, args=(str(u.bybitapi), str(u.bybitsecret),
                    user_data["symbol"] + 'USDT', float(u.deposit), float(u.max_loss), user_data["uid"], nc))
        p.daemon = True
        # args=(str(apikey), str(secretkey), symbol.upper() + 'USDT', float(deposit))
        p.start()
        u.pid = str(p.pid)
        session.commit()
        tasks[u.id] = p

        await asyncio.sleep(20)


@router.callback_query(F.data.startswith("bybit_start_"))
async def allusers(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(uid=callback.data.split('_')[2])
    await start_wrapper(state, callback)

    from app.handlers.allusers import bybitdeposiotclone
    await bybitdeposiotcloneCB(callback, state)


@router.callback_query(F.data.startswith("bybit_stop_"))
async def stopany(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    aid = int(user_data['aid'])
    tasks[aid].kill()
    try:
        with Session(engine) as session:
            a = session.query(user.API).filter(
                user.API.id == int(user_data["aid"])).all()[0]
            p = psutil.Process(int(a.pid))
            p.terminate()
    except BaseException:
        print("Error")
    await callback.message.answer("ByBit останвлен")


@router.callback_query(F.data.startswith("bybit_stopclose_"))
async def stopclose(callback: types.CallbackQuery, state: FSMContext):
    uid = int(callback.data.split('_')[2])
    user_data = await state.get_data()
    aid = int(user_data['aid'])
    try:
        tasks[aid].kill()
    except BaseException as e:
        print("Cannot terminate process\n\n", e)
    try:
        with Session(engine) as session:
            a = session.query(user.API).filter(
                user.API.id == int(user_data["aid"])).all()[0]
            p = psutil.Process(int(a.pid))
            p.terminate()
    except BaseException:
        print("Error")
    with Session(engine) as session:
        u = session.query(user.API).filter(user.API.id == aid).all()[0]
        ti = TradeInfo.SmallBybit(u.bybitapi, u.bybitsecret)
        ti.endnclose(u.symbol + 'USDT')
    await callback.message.answer("ByBit останвлен. Позиции закрыты")


@router.callback_query(F.data == "get_stat")
async def aaa(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text="Введите дату ОТ"
    )
    await state.set_state(ByBitStart.beforedate)


@router.message(ByBitStart.beforedate)
async def namechoosen(message: types.Message, state: FSMContext):
    await state.update_data(startTime=message.text)

    await state.set_state(ByBitStart.afterdate.state)
    await message.answer("Введите дату ДО")


@router.message(ByBitStart.afterdate)
async def namechoosen(message: types.Message, state: FSMContext):
    await state.update_data(stopTime=message.text)
    user_data = await state.get_data()
    uid = int(user_data['uid'])
    with Session(engine) as session:
        u = session.query(user.User).filter(user.User.id == uid).all()[0]
        for a in u.apis:
            ti = TradeInfo.SmallBybit(a.bybitapi, a.bybitsecret)
            ti.statistics(
                a.symbol + 'USDT', startTime=user_data["startTime"], stopTime=user_data["stopTime"])
            from aiogram.types import FSInputFile

            doc = FSInputFile(path='./out.csv', filename=f'{a.symbol}.csv')
            await message.answer_document(document=doc)


@router.callback_query(F.data.startswith("bybit_start_"))
async def allusers(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(uid=callback.data.split('_')[2])

    await callback.message.answer("Введите торговую пару", reply_markup=make_inline_keyboard(coins))
    await state.set_state(ByBitStart.symbol.state)


@router.message(ByBitStart.symbol)
@router.callback_query(F.data.startswith("bybit_change2_"))
async def bybitsymbol(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(symbol=callback.data.split('_')[2].split('$')[0])
    await state.update_data(aid=callback.data.split('_')[2].split('$')[1])

    user_data = await state.get_data()
    builder = InlineKeyboardBuilder()
    row = [[buttons.STARTBYBIT(user_data["uid"])],
           [buttons.STOPBYBIT(user_data["uid"]),
            buttons.STOPCLOSEBYBIT(user_data["uid"])],
           [buttons.CHANGE_API, buttons.CHANGE_DEPOSIT],
           [buttons.DELETEAPI(user_data["aid"])], ]
    kb = InlineKeyboardMarkup(inline_keyboard=row, resize_keyboard=True)

    # await state.set_state(ByBitStart.deposit.state)
    await callback.message.answer(
        text=f"""
Торговые пары
Выбрана торговая пара: {user_data["symbol"]}
""",
        reply_markup=kb
    )


@router.message(Command("change_api"))
@router.callback_query(F.data == "change_api")
async def change_api(callback: types.CallbackQuery, state: FSMContext):
    from app.handlers.adduser import namechosenclone
    with Session(engine) as session:
        user_data = await state.get_data()
        u = session.query(user.User).filter(
            user.User.id == int(user_data["uid"])).all()[0]
        await namechosenclone(u.name, callback, state)


@router.message(Command("change_deposit"))
@router.callback_query(F.data == "change_deposit")
async def change_api(callback: types.CallbackQuery, state: FSMContext):
    from app.handlers.adduser import bybitsymbolclone
    with Session(engine) as session:
        user_data = await state.get_data()
        # u = session.query(user.User).filter(user.User.id == int(user_data["uid"])).all()[0]
        await bybitsymbolclone(callback, state)


@router.message(ByBitStart.deposit)
async def bybitdeposiot(message: types.Message, state: FSMContext):
    from multiprocessing import Process
    from fix.Bybit.main import start

    await state.update_data(deposit=message.text.lower())

    user_data = await state.get_data()

    # uid, symbol, deposit = user_data.values()
    uid = user_data["uid"]
    symbol = user_data["symbol"]
    deposit = user_data["deposit"]
    with Session(engine) as session:
        u = session.query(user.User).filter(user.User.id == int(uid)).all()[0]
        apikey, secretkey = u.bybitapi, u.bybitsecret
        max_loss = u.max_loss
        print(f'allusers.py, max_loss = {max_loss}')
        p = Process(target=start, args=(str(apikey), str(
            secretkey), symbol.upper() + 'USDT', float(deposit), max_loss))
        p.daemon = True
        p.start()
        u.pid = str(p.pid)
        session.commit()
        tasks[uid] = p
        await message.reply("BybBit запущен")


def register_handlers_bybit_start(dp: Dispatcher):
    dp.register_message_handler(allusers, commands="/all_users", state="*")
    # dp.register_message_handler(bybitstart, state=ByBitStart.uid)
    # dp.register_message_handler(aaa, sta)
    dp.register_message_handler(allusers_alt, State=ByBitStart.gofromadding)
    dp.register_message_handler(bybitsymbol, state=ByBitStart.symbol)
    dp.register_message_handler(bybitdeposiot, state=ByBitStart.deposit)
    # dp.register_message_handler(bybit_symbol_chosen, state=BybitAuthData.waiting_for_symbol)
    # dp.register_message_handler(bybit_deposiot_chosen, state=BybitAuthData.waiting_for_deposit)
