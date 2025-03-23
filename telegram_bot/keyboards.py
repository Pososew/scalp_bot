from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    keyboard = [
        [InlineKeyboardButton("📈 Текущие позиции", callback_data='view_positions')],
        [InlineKeyboardButton("💰 Баланс", callback_data='balance'),
         InlineKeyboardButton("📜 История", callback_data='history')],
        [InlineKeyboardButton("➕ Добавить позицию", callback_data='add_position'),
         InlineKeyboardButton("➖ Удалить позицию", callback_data='delete_position')],
        [InlineKeyboardButton("⚙️ Установить баланс", callback_data='set_balance')]
    ]
    return InlineKeyboardMarkup(keyboard)
