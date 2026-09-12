from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="📦 Список товаров", callback_data="list_products")
    kb.button(text="🎲 Опубликовать сейчас (случайный)", callback_data="post_random")
    kb.button(text="➕ Добавить товар", callback_data="add_product")
    kb.adjust(1)
    return kb.as_markup()

def products_kb(products):
    kb = InlineKeyboardBuilder()
    for p in products:
        pid = p[0]
        name = p[1]
        in_stock = p[6]
        mark = "✅" if in_stock else "❌"
        kb.button(text=f"{mark} {name}", callback_data=f"select_{pid}")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1)
    return kb.as_markup()

def product_actions_kb(pid):
    kb = InlineKeyboardBuilder()
    kb.button(text="📤 Опубликовать в канал", callback_data=f"publish_{pid}")
    kb.button(text="🔄 Переключить наличие", callback_data=f"stock_{pid}")
    kb.button(text="🗑 Удалить", callback_data=f"del_{pid}")
    kb.button(text="⬅️ Назад", callback_data="list_products")
    kb.adjust(1)
    return kb.as_markup()
