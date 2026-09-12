import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from database import init_db, add_product, get_all_products, get_product, delete_product, toggle_stock
from keyboards import main_menu, products_kb, product_actions_kb
from scheduler import setup_scheduler, publish_product, daily_post

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
POST_HOUR = int(os.getenv("POST_HOUR", 12))
POST_MINUTE = int(os.getenv("POST_MINUTE", 0))
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class AddProduct(StatesGroup):
    name = State()
    description = State()
    price = State()
    photo = State()
    category = State()

def is_admin(uid):
    return uid in ADMIN_IDS

def admin_only(func):
    async def wrapper(event, *args, **kwargs):
        uid = event.from_user.id
        if not is_admin(uid):
            if isinstance(event, Message):
                await event.answer("Нет доступа")
            else:
                await event.answer("Нет доступа", show_alert=True)
            return
        return await func(event, *args, **kwargs)
    return wrapper

@dp.message(CommandStart())
@admin_only
async def cmd_start(message: Message):
    await message.answer("Привет, админ! Управление товарами:", reply_markup=main_menu())

@dp.message(Command("cancel"))
@admin_only
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено", reply_markup=main_menu())

@dp.callback_query(F.data == "back_main")
@admin_only
async def back_main(cb: CallbackQuery):
    await cb.message.edit_text("Главное меню:", reply_markup=main_menu())

@dp.callback_query(F.data == "list_products")
@admin_only
async def list_products(cb: CallbackQuery):
    products = await get_all_products()
    if not products:
        await cb.message.edit_text("Список пуст. Добавь товар.", reply_markup=main_menu())
        return
    await cb.message.edit_text("Выбери товар:", reply_markup=products_kb(products))

@dp.callback_query(F.data.startswith("select_"))
@admin_only
async def select_product(cb: CallbackQuery):
    pid = int(cb.data.split("_")[1])
    p = await get_product(pid)
    if not p:
        await cb.answer("Товар не найден", show_alert=True)
        return
    name = p[1]
    desc = p[2]
    price = p[3]
    photo = p[4]
    stock = p[6]
    stock_text = "В наличии" if stock else "Нет в наличии"
    text = f"{name}\n{desc}\nЦена: {price}\n{stock_text}"
    if photo:
        try:
            await cb.message.delete()
        except Exception:
            pass
        await cb.message.answer_photo(photo, caption=text, reply_markup=product_actions_kb(pid))
    else:
        await cb.message.edit_text(text, reply_markup=product_actions_kb(pid))
    await cb.answer()

@dp.callback_query(F.data.startswith("publish_"))
@admin_only
async def publish_now(cb: CallbackQuery):
    pid = int(cb.data.split("_")[1])
    p = await get_product(pid)
    if not p:
        await cb.answer("Не найдено", show_alert=True)
        return
    ok = await publish_product(bot, p)
    if ok:
        await cb.answer("Опубликовано", show_alert=True)
    else:
        await cb.answer("Ошибка", show_alert=True)

@dp.callback_query(F.data.startswith("stock_"))
@admin_only
async def stock_toggle(cb: CallbackQuery):
    pid = int(cb.data.split("_")[1])
    await toggle_stock(pid)
    await cb.answer("Обновлено")
    p = await get_product(pid)
    name = p[1]
    stock = p[6]
    stock_text = "В наличии" if stock else "Нет в наличии"
    text = f"{name}\n{stock_text}"
    try:
        if cb.message.photo:
            await cb.message.edit_caption(caption=text, reply_markup=product_actions_kb(pid))
        else:
            await cb.message.edit_text(text, reply_markup=product_actions_kb(pid))
    except Exception:
        pass

  @dp.callback_query(F.data.startswith("del_"))
@admin_only
async def del_product(cb: CallbackQuery):
    pid = int(cb.data.split("_")[1])
    await delete_product(pid)
    await cb.answer("Удалено")
    products = await get_all_products()
    if not products:
        await cb.message.edit_text("Список пуст.", reply_markup=main_menu())
    else:
        await cb.message.edit_text("Выбери товар:", reply_markup=products_kb(products))

@dp.callback_query(F.data == "post_random")
@admin_only
async def post_random(cb: CallbackQuery):
    await daily_post(bot)
    await cb.answer("Опубликован случайный товар", show_alert=True)

@dp.callback_query(F.data == "add_product")
@admin_only
async def add_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AddProduct.name)
    await cb.message.edit_text("Введи название товара:")

@dp.message(AddProduct.name)
@admin_only
async def add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddProduct.description)
    await message.answer("Введи описание:")

@dp.message(AddProduct.description)
@admin_only
async def add_desc(message: Message, state: FSMContext):
    if message.text == "-":
        desc = ""
    else:
        desc = message.text
    await state.update_data(description=desc)
    await state.set_state(AddProduct.price)
    await message.answer("Введи цену:")

@dp.message(AddProduct.price)
@admin_only
async def add_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await state.set_state(AddProduct.photo)
    await message.answer("Отправь фото или напиши -")

@dp.message(AddProduct.photo, F.photo | F.text)
@admin_only
async def add_photo(message: Message, state: FSMContext):
    if message.photo:
        photo_id = message.photo[-1].file_id
    else:
        photo_id = ""
    await state.update_data(photo_id=photo_id)
    await state.set_state(AddProduct.category)
    await message.answer("Категория:")

@dp.message(AddProduct.category)
@admin_only
async def add_category(message: Message, state: FSMContext):
    data = await state.get_data()
    await add_product(data["name"], data["description"], data["price"], data["photo_id"], message.text, True)
    await state.clear()
    await message.answer("Товар добавлен!", reply_markup=main_menu())

async def main(): await init_db() setup_scheduler(bot, POST_HOUR, POST_MINUTE) print("Бот запущен") await dp.start_polling(bot)
if name == "main": asyncio.run(main())
