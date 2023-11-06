from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message, CallbackQuery

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from aiogram.types import(
    ReplyKeyboardMarkup as km,
    KeyboardButton as kb,
    InlineKeyboardMarkup as im,
    InlineKeyboardButton as ib
)

from sqlite3 import connect as con
from datetime import datetime as dt
from hashlib import md5

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

class DataBase:
    def check(self, id:int):
        with con('main.db') as c:
            res = c.execute(f'select * from user where id={id}')
            return True if len([*res]) > 0 else False

    def get_orders(self, id:int):
        with con('main.db') as c:
            res = c.execute(f'select * from orders where id={id}')
            keys = ['id', 'name', 'phone', 'date', 'address', 'type', 'payed']
            # [*res]
            data = {}
            for order in [*res]:
                data[order[7]] = {keys[i]:order[i] for i in range(7)}

            return data

    def create_user(self, id:int, name:str, phone:str):
        with con('main.db') as c:
            c.execute(f'insert into user values({id}, "{name}", "{phone}")')

    def create_order(self, id:int, phone:str, date:str, name:str, address:str, type:str):
        token = md5(str(phone+date+name+address+type).encode()).hexdigest()
        with con('main.db') as c:
            c.execute(
                f'insert into orders values({id}, "{name}", "{phone}", "{date}", "{address}", "{type}", "False", "{token}")'
            )

    def order(self, token:str):
        with con('main.db') as c:
            res = c.execute(f'select * from orders where token="{token}"')
            order = [*res][0]
            data = {
                'id': order[0],
                'token': order[7],
                'phone': order[2],
                'date': order[3],
                'address': order[4],
                'type': order[5],
                'name': order[1],
            }

            return data

class Menu:
    main = km(
        resize_keyboard=True,
        keyboard=[
            [kb("Order")],
            [kb("Profile")],
        ]
    )

class UserData(StatesGroup):
    name = State()
    phone = State()

class OrderData(StatesGroup):
    phone = State()
    date = State()
    name = State()
    address = State()
    type = State()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

storage = MemoryStorage()
group = -1001614007138

db = DataBase()
menu = Menu()

bot = Bot("6810286004:AAGTxiuf7L08vdnOouR5GEH8QUsz2y8Io_w", parse_mode="html")
dp = Dispatcher(bot, storage=storage)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

'''
функция старт
елси это пользователь:
    если не в системе:
        ввести имя
    иначе:
        текст "здрасьте" и главное меню
'''
@dp.message_handler(commands=['start'], state=None)
async def start(msg: Message):
    chat = msg.chat
    if chat.id > 0:
        if not db.check(chat.id):
            await UserData.name.set()
            await msg.reply("Введите ваше имя")
        else:
            await msg.answer(text="здрасьте", reply_markup=menu.main)


'''
функция "получить имя"
если это пользователь:
    ввод имени
    текст "введте номер по примеру"
'''
@dp.message_handler(state=UserData.name)
async def get_user_name(msg: Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = msg.text

    await UserData().next()
    await msg.reply("Пример: +998972402609\nВведите ваш номер")


'''
функция "получить номер"
если это пользователь:
    проверка (длины, первого символа "+", все цифры":
        текст "добро пожаловать"
    иначе:
        текст "/start для регистрации"
        
    попытка:
        сохранение данных пользователя
    провал:
        вывод на экран "провал"
'''
@dp.message_handler(state=UserData.phone)
async def get_user_phone(msg: Message, state: FSMContext):
    chat = msg.chat
    if chat.id > 0:
        true = 0
        dataset = []
        dataset.extend(msg.text)
        for i in dataset:
            true += 1 if i in [str(i) for i in range(10)] else 0

        async with state.proxy() as data:
            if len(msg.text) == 13 and msg.text[0] == '+' and true == 12:
                data['phone'] = msg.text

                await msg.answer("Добро пожаловать")

            else:
                await msg.answer("Номер введен неправильно\nНажмите /start для регистрации")

        async with state.proxy() as data:
            try:
                db.create_user(chat.id, data['name'], data['phone'])
            except: print("провал")

        await state.finish()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

'''
функция заказ
если это пользователь:
    если он в системе:
        получить номер
'''
@dp.message_handler(text='Order', state=None)
async def get_order(msg: Message):
    chat = msg.chat
    if chat.id > 0 and db.check(chat.id):
        await OrderData.phone.set()
        await msg.reply("Введите номер")


'''
функция "получить номер"
если пользователь:
    если он в системе:
        проверка (длины, первого символа "+", все цифры":
            ввод номера
            текст "введите дату по примеру"
        иначе:
            текст "Order для заказа"         
'''
@dp.message_handler(state=OrderData.phone)
async def get_order_phone(msg: Message, state: FSMContext):
    chat = msg.chat
    if chat.id > 0 and db.check(chat.id):
        true = 0
        dataset = []
        dataset.extend(msg.text)
        for i in dataset:
            true += 1 if i in [str(i) for i in range(10)] else 0

        async with state.proxy() as data:
            if len(msg.text) == 13 and msg.text[0] == '+' and true == 12:
                data['phone'] = msg.text

                await OrderData().next()
                await msg.reply("Пример 2023-1-1\nВведите дату")

            else:
                await msg.answer("Номер введен неправильно\nКнопка 'Order' для заказа")
                state.finish()


'''
функция "получить дату"
если это пользователь:
    если он в системе:
        попытка:
            получить корректную дату
            ввод имени
        провал:
            текст "некорректная дата"
'''
@dp.message_handler(state=OrderData.date)
async def get_order_date(msg: Message, state: FSMContext):
    chat = msg.chat
    if chat.id > 0 and db.check(chat.id):
        year = dt.now().year
        month = dt.now().month
        day = dt.now().day

        try:
            date = msg.text.split('-')
            y = int(date[0])
            m = int(date[1])
            d = int(date[2])

            if len(date) != 3 or ((y < year) or (y==year and m<month) or (y==year and m==month and d<day)):
                await state.finish()
                await msg.answer("Некорректная дата\nКнопка 'Order' для заказa")
            else:
                async with state.proxy() as data:
                    data['date'] = msg.text

                await OrderData().next()
                await msg.reply("Введите имя")

        except Exception as e:
            await state.finish()
            await msg.answer("Некорректная дата\nКнопка 'Order' для заказa")


'''
функция "получить имя"
получить имя
ввод адреса
'''
@dp.message_handler(state=OrderData.name)
async def get_order_name(msg: Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = msg.text

    await OrderData().next()
    await msg.reply("Введите адрес")


'''
функция "получить адрес"
получить адрес
ввод типа
'''
@dp.message_handler(state=OrderData.address)
async def get_order_address(msg: Message, state: FSMContext):
    async with state.proxy() as data:
        data['address'] = msg.text

    await OrderData().next()
    await msg.reply("Введите тип")


'''
функция "получить тип"
получить адрес
сохранение данных заказа
'''
@dp.message_handler(state=OrderData.type)
async def get_order_address(msg: Message, state: FSMContext):
    chat = msg.chat
    if chat.id > 0:
        async with state.proxy() as data:
            data['type'] = msg.text

        await msg.answer("Заказ подан. Ждите")

        async with state.proxy() as order:
            db.create_order(
                chat.id, order['phone'],
                order['date'], order['name'],
                order['address'], order['type']
            )

            order_token = md5(str(order['phone']+order['date']+order['name']+order['address']+order['type']).encode()).hexdigest()

            await bot.send_message(
                group, f"new order: {order_token}\n\nphone: {order['phone']}\n\ndate: {order['date']}\nname: {order['name']}\naddress: {order['address']}\ntype: {order['type']}"
            )

        await state.finish()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

@dp.message_handler(text='Profile')
async def profile(msg: Message):
    chat = msg.chat
    if chat.id > 0 and db.check(chat.id):
        orders = db.get_orders(920747145)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)