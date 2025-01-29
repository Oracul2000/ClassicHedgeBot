import asyncio
from typing import Text
from aiogram import Dispatcher, types
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardMarkup

from app.keyboards import buttons

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
# from ..database.models import user
from database.models import user


engine = create_engine("sqlite:///Data.db", echo=True)


router = Router()

coins = ['ADA', 'LINK', 'XRP', 'XLM', 'DASH', 'NEO', 'TRX',
         'EOS', 'LTC', 'DOGE', 'APT', 'ATOM', 'BTC', 'ETH']
bingx_tasks = {}


class AddNewUser(StatesGroup):
    name = State()
    bybitapi = State()
    bybitsecret = State()
    symbol = State()
    deposit = State()
    max_loss = State()


@router.message(Command("add_user"))
@router.callback_query(F.data == "add_user")
async def adduser(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text="Введите имя пользователя:"
    )
    await state.set_state(AddNewUser.name)


@router.message(AddNewUser.name)
async def namechoosen(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)

    await state.set_state(AddNewUser.bybitapi.state)
    await message.answer("Введите API key пользователя от ByBit")


async def namechosenclone(name, callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(name=name)

    await state.set_state(AddNewUser.bybitapi.state)
    await callback.message.answer("Введите API key пользователя от ByBit")


@router.message(AddNewUser.bybitapi)
async def bybitapichoosen(message: types.Message, state: FSMContext):
    await state.update_data(bybitapi=message.text)

    await state.set_state(AddNewUser.bybitsecret)
    await message.answer("Введите Secret key пользователя от ByBit")


@router.message(AddNewUser.bybitsecret)
async def bybitsecretchoosen(message: types.Message, state: FSMContext):
    await state.update_data(bybitsecret=message.text)
    user_data = await state.get_data()

    from app.keyboards.simple_row import make_row_keyboard, make_inline_keyboard
    await message.answer("Введите торговую пару", reply_markup=make_inline_keyboard(coins))
    await state.set_state(AddNewUser.symbol.state)


@router.message(AddNewUser.symbol)
@router.callback_query(F.data.startswith("bybit_change_"))
async def bybitsymbol(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(symbol=callback.data.split('_')[2])

    await state.set_state(AddNewUser.deposit.state)
    await callback.message.answer("Введите желаемый депозит в usdt")


async def bybitsymbolclone(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddNewUser.deposit.state)
    await callback.message.answer("Введите желаемый депозит в usdt")


@router.message(AddNewUser.deposit)
async def bybitdeposiot(message: types.Message, state: FSMContext):
    await state.update_data(deposit=message.text.lower())
    await state.set_state(AddNewUser.max_loss.state)
    await message.answer("Введите максимальный убыток с одной поизиции в % от балланса Единого Торгового Аккаунта")


@router.message(AddNewUser.max_loss)
async def bybitmaxloss(message: types.Message, state: FSMContext):
    await state.update_data(max_loss=message.text.lower())
    user_data = await state.get_data()

    with Session(engine) as session:
        if 'aid' not in user_data and 'uid' not in user_data:
            nu = user.User(name=user_data["name"])
            na = user.API(name=user_data["name"],
                          bybitapi=user_data["bybitapi"],
                          bybitsecret=user_data["bybitsecret"],
                          symbol=user_data["symbol"],
                          deposit=float(user_data["deposit"]),
                          max_loss=float(user_data["max_loss"]))
            session.add_all([nu, na])
            all_apis = session.query(user.API).all()
            all_users = session.query(user.User).all()
            all_users[-1].apis = [all_apis[-1]]
            await state.update_data(aid=all_apis[-1].id)
            await state.update_data(uid=all_users[-1].id)
        elif 'aid' not in user_data:
            na = user.API(name=user_data["name"],
                          bybitapi=user_data["bybitapi"],
                          bybitsecret=user_data["bybitsecret"],
                          symbol=user_data["symbol"],
                          deposit=float(user_data["deposit"]),
                          max_loss=float(user_data["max_loss"]))
            session.add_all([na])
            all_apis = session.query(user.API).all()
            u = session.query(user.User).filter(
                user.User.id == int(user_data["uid"])).all()[0]
            u.apis.append(all_apis[-1])
            await state.update_data(aid=all_apis[-1].id)
        else:
            a = session.query(user.API).filter(
                user.API.id == int(user_data["aid"])).all()[0]

            if "bybitapi" in user_data:
                a.bybitapi = user_data["bybitapi"]
                a.bybitsecret = user_data["bybitsecret"]
            if "symbol" in user_data:
                a.symbol = user_data["symbol"]
            if "deposit" in user_data:
                a.deposit = float(user_data["deposit"])

        session.commit()

        await message.answer("Данные успешно внесены")
        await message.answer("Подождите...")

        from app.handlers.allusers import bybitdeposiotclone
        await bybitdeposiotclone(message, state)


async def bybitdeposiotclone(message: types.Message, state: FSMContext):
    await state.update_data(deposit=message.text.lower())

    user_data = await state.get_data()

    with Session(engine) as session:
        nu = user.User(name=user_data["name"],
                       bybitapi=user_data["bybitapi"],
                       bybitsecret=user_data["bybitsecret"],
                       symbol=user_data["symbol"],
                       deposit=float(user_data["deposit"]),
                       max_loss=float(user_data["max_loss"]))
        session.add_all([nu,])
        session.commit()

        await message.answer("Данные успешно вынесены")


def register_handlers_bybit_auth(dp: Dispatcher):
    dp.register_message_handler(adduser, commands="/add_user", state="*")
    dp.register_message_handler(namechoosen, state=AddNewUser.name)
    dp.register_message_handler(bybitapichoosen, state=AddNewUser.bybitapi)
    dp.register_message_handler(
        bybitsecretchoosen, state=AddNewUser.bybitsecret)

    # from app.handlers import allusers
    # dp.register_message_handler(allusers.allusers_alt, state=allusers.ByBitStart.gofromadding)
