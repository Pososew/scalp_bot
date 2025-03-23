from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from telegram_bot.keyboards import main_menu
from config.config import ALLOWED_USERS
from core.database import Session, Position, Account
from core.exchange import get_current_price

allowed_filter = filters.User(ALLOWED_USERS)

SET_BALANCE, DELETE_POSITION = range(2)

async def start(update, context):
    await update.message.reply_text("Меню управления ботом:", reply_markup=main_menu())

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == 'set_balance':
        await query.edit_message_text("Введите новый баланс:")
        return SET_BALANCE

    elif query.data == 'delete_position':
        await query.edit_message_text("Введите ID позиции для удаления:")
        return DELETE_POSITION
    
    elif query.data == 'balance':
        session = Session()
        account = session.query(Account).first()
        balance = account.balance if account else 0
        await query.edit_message_text(f"Ваш текущий баланс: {balance:.2f}$")

    elif query.data == 'view_positions':
        session = Session()
        positions = session.query(Position).all()
        if not positions:
            await query.edit_message_text("Нет открытых позиций.")
        else:
            msg = "📈 Открытые позиции:\n"
            for p in positions:
                current_price = get_current_price(p.symbol)
                pnl_percent = ((current_price - p.entry_price) / p.entry_price) * 100
                msg += (f"\nID: {p.id}\n"
                        f"Монета: {p.symbol}\n"
                        f"Цена входа: {p.entry_price}\n"
                        f"Текущая цена: {current_price}\n"
                        f"Прибыль: {pnl_percent:.2f}%\n")
            await query.edit_message_text(msg)

    elif query.data == 'history':
        await query.edit_message_text("Функция истории ещё не реализована.")

async def set_balance(update, context):
    session = Session()
    balance = float(update.message.text)
    account = session.query(Account).first()
    if not account:
        account = Account(balance=balance)
        session.add(account)
    else:
        account.balance = balance
    session.commit()
    await update.message.reply_text(f"Баланс установлен: {balance:.2f}$")
    return ConversationHandler.END

async def delete_position(update, context):
    session = Session()
    position_id = int(update.message.text)
    position = session.query(Position).filter(Position.id == position_id).first()

    if position:
        current_price = get_current_price(position.symbol)
        pnl = (current_price - position.entry_price) * position.amount

        account = session.query(Account).first()
        account.balance += pnl

        session.delete(position)
        session.commit()

        await update.message.reply_text(f"Позиция удалена. PnL: {pnl:.2f}$. Баланс обновлен: {account.balance:.2f}$")
    else:
        await update.message.reply_text("Позиция не найдена.")

    return ConversationHandler.END

def setup_handlers(app):
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, allowed_filter)],
        states={
            SET_BALANCE: [MessageHandler(filters.TEXT & allowed_filter, set_balance)],
            DELETE_POSITION: [MessageHandler(filters.TEXT & allowed_filter, delete_position)]
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start, allowed_filter))
    app.add_handler(conv_handler)
