import os
import random
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from database import get_all_products, get_last_posted_product, log_post

CHANNEL_ID = os.getenv("CHANNEL_ID")

def format_post(product):
    pid, name, description, price, photo_id, category, in_stock, added = product
    stock_line = "✅ В наличии" if in_stock else "❌ Нет в наличии"
    text = (
        f"<b>{name}</b>\n\n"
        f"{description}\n\n"
        f"💰 Цена: {price}\n"
        f"📦 {stock_line}\n"
    )
    return text, photo_id

async def publish_product(bot: Bot, product):
    text, photo_id = format_post(product)
    try:
        if photo_id:
            await bot.send_photo(CHANNEL_ID, photo_id, caption=text, parse_mode="HTML")
        else:
            await bot.send_message(CHANNEL_ID, text, parse_mode="HTML")
        await log_post(product[0])
        return True
    except Exception as e:
        print(f"Ошибка публикации: {e}")
        return False

async def daily_post(bot: Bot):
    products = await get_all_products()
    in_stock = [p for p in products if p[6] == 1]
    if not in_stock:
        print("Нет товаров в наличии")
        return
    last_id = await get_last_posted_product()
    candidates = [p for p in in_stock if p[0] != last_id] or in_stock
    product = random.choice(candidates)
    await publish_product(bot, product)

def setup_scheduler(bot: Bot, hour: int, minute: int):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(daily_post, "cron", hour=hour, minute=minute, args=[bot])
    scheduler.start()
    return scheduler
