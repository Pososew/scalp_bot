from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from telegram_bot.keyboards import main_menu
from config.config import ALLOWED_USERS
from core.database import Session, Position, Account
from core.exchange import get_current_price
from telegram_bot.keyboards import main_menu 
from config.config import PROFIT_TARGET, STOP_LOSS
from core.signals import check_signals_for_all_symbols
from telegram import Bot
from config.config import ALLOWED_USERS, TELEGRAM_BOT_TOKEN

allowed_filter = filters.User(ALLOWED_USERS)

SET_BALANCE, DELETE_POSITION, ADD_SYMBOL, ADD_PRICE, ADD_AMOUNT, ADD_LEVERAGE = range(6)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def start(update, context):
    await update.message.reply_text("Меню управления ботом:", reply_markup=main_menu())

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == 'set_balance':
        await query.edit_message_text("Введите новый баланс:", reply_markup=main_menu())
        return SET_BALANCE

    elif query.data == 'delete_position':
        session = Session()
        positions = session.query(Position).all()

        if not positions:
            await query.edit_message_text("У тебя нет открытых позиций.", reply_markup=main_menu())
            return ConversationHandler.END
        else:
            msg = "📌 Выбери ID позиции, чтобы удалить:\n\n"
            for p in positions:
                msg += (f"ID: {p.id} | {p.symbol} по {p.entry_price}\n")

            await query.edit_message_text(msg)
            await query.message.reply_text("Отправь ID позиции для удаления:")
            return DELETE_POSITION

    
    elif query.data == 'add_position':
        await query.edit_message_text("Введите символ монеты (например BTC/USDT):")
        return ADD_SYMBOL
    
    elif query.data == 'balance':
        session = Session()
        account = session.query(Account).first()
        balance = account.balance if account else 0
        await query.edit_message_text(f"Ваш текущий баланс: {balance:.2f}$", reply_markup=main_menu())

    elif query.data == 'view_positions':
        session = Session()
        positions = session.query(Position).all()
        if not positions:
            await query.edit_message_text("Нет открытых позиций.", reply_markup=main_menu())
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
            await query.edit_message_text(msg, reply_markup=main_menu())

    elif query.data == 'signals':
        signals = check_signals_for_all_symbols()
        msg = "📌 Текущие сигналы:\n\n"
        for signal in signals:
            msg += (
                f"{'📗' if signal['signal']=='LONG' else '📕' if signal['signal']=='SHORT' else '📍'} "
                f"{signal['symbol']}: {signal['signal']}\n"
                f"Цена: {signal['close']}\n"
                f"RSI: {signal['rsi']:.2f}, MACD: {signal['macd']:.4f}\n"
                f"TP: {signal['bb_upper']:.2f}, SL: {signal['bb_lower']:.2f}\n\n"
            )
        await query.message.reply_text(msg, reply_markup=main_menu())

    elif query.data == 'history':
        await query.edit_message_text("Функция истории ещё не реализована.", reply_markup=main_menu())

async def add_symbol(update, context):
    context.user_data['symbol'] = update.message.text.upper()
    await update.message.reply_text("Введите цену входа:")
    return ADD_PRICE

async def add_price(update, context):
    try:
        context.user_data['entry_price'] = float(update.message.text)
        await update.message.reply_text("Введите сумму (в USDT), которую ставите в сделку:")
        return ADD_AMOUNT
    except ValueError:
        await update.message.reply_text("Введите корректную цену!")
        return ADD_PRICE

async def add_amount(update, context):
    try:
        context.user_data['trade_amount_usdt'] = float(update.message.text)
        await update.message.reply_text("Введите плечо (например 3 для 3x):")
        return ADD_LEVERAGE
    except ValueError:
        await update.message.reply_text("Введите корректную сумму!")
        return ADD_AMOUNT

async def add_leverage(update, context):
    try:
        leverage = float(update.message.text)
        symbol = context.user_data['symbol']
        entry_price = context.user_data['entry_price']
        trade_amount_usdt = context.user_data['trade_amount_usdt']

        # Рассчитываем объем
        amount = (trade_amount_usdt * leverage) / entry_price

        # TP и SL из конфига
        take_profit = entry_price * (1 + PROFIT_TARGET)
        stop_loss = entry_price * (1 - STOP_LOSS)

        session = Session()
        position = Position(
            symbol=symbol,
            entry_price=entry_price,
            amount=amount,
            take_profit=take_profit,
            stop_loss=stop_loss
        )
        session.add(position)
        session.commit()

        await update.message.reply_text(
            f"✅ Позиция добавлена:\n"
            f"{symbol}, цена: {entry_price}, плечо: {leverage}x\n"
            f"Сумма: {trade_amount_usdt} USDT\n"
            f"Объем позиции: {amount:.6f} {symbol.split('/')[0]}\n"
            f"TP: {take_profit:.2f}, SL: {stop_loss:.2f}",
            reply_markup=main_menu()
        )

        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Введите корректное плечо!")
        return ADD_LEVERAGE



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
    await update.message.reply_text(f"Баланс установлен: {balance:.2f}$", reply_markup=main_menu())
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

        await update.message.reply_text(f"Позиция удалена. PnL: {pnl:.2f}$. Баланс обновлен: {account.balance:.2f}$", reply_markup=main_menu())
    else:
        await update.message.reply_text("Позиция не найдена.", reply_markup=main_menu())

    return ConversationHandler.END

async def auto_signals_check(application):
    signals = check_signals_for_all_symbols()

    general_msg = "📌 Общий обзор сигналов:\n\n"
    good_signals = []

    for signal in signals:
        if signal['signal'] in ('LONG', 'SHORT'):
            good_signals.append(signal)

        general_msg += (
            f"{'📗' if signal['signal']=='LONG' else '📕' if signal['signal']=='SHORT' else '📍'} "
            f"{signal['symbol']}: {signal['signal']}\n"
            f"Цена: {signal['close']}, RSI: {signal['rsi']:.2f}\n\n"
        )

    for user_id in ALLOWED_USERS:
        await bot.send_message(chat_id=user_id, text=general_msg)

    for signal in good_signals:
        msg = (
            f"{'📗' if signal['signal']=='LONG' else '📕'} Новый сигнал: {signal['signal']}!\n\n"
            f"{signal['symbol']}\nЦена: {signal['close']}\n"
            f"RSI: {signal['rsi']:.2f}, MACD: {signal['macd']:.4f}\n"
            f"TP: {signal['bb_upper']:.2f}, SL: {signal['bb_lower']:.2f}"
        )
        for user_id in ALLOWED_USERS:
            await bot.send_message(chat_id=user_id, text=msg)

def setup_handlers(app):
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(button_handler, pattern="^(set_balance|delete_position|add_position)$")
        ],
        states={
        SET_BALANCE: [MessageHandler(filters.TEXT & allowed_filter, set_balance)],
        DELETE_POSITION: [MessageHandler(filters.TEXT & allowed_filter, delete_position)],
        ADD_SYMBOL: [MessageHandler(filters.TEXT & allowed_filter, add_symbol)],
        ADD_PRICE: [MessageHandler(filters.TEXT & allowed_filter, add_price)],
        ADD_AMOUNT: [MessageHandler(filters.TEXT & allowed_filter, add_amount)],
        ADD_LEVERAGE: [MessageHandler(filters.TEXT & allowed_filter, add_leverage)]  # должно быть!
        },

        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start, allowed_filter))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(balance|view_positions|history)$"))
    app.add_handler(conv_handler)

