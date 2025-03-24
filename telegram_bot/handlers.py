from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from telegram_bot.keyboards import main_menu
from config.config import ALLOWED_USERS, TELEGRAM_BOT_TOKEN, PROFIT_TARGET, STOP_LOSS
from telegram import Bot
from core.database import Session, Position, Account, Trade
from core.exchange import get_current_price
from core.signals import check_signals_for_all_symbols

allowed_filter = filters.User(ALLOWED_USERS)

SET_BALANCE, DELETE_POSITION, ADD_SYMBOL, ADD_PRICE, ADD_AMOUNT, ADD_LEVERAGE, ADD_DIRECTION = range(7)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def start(update, context):
    await update.message.reply_text("Меню управления ботом:", reply_markup=main_menu())

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'set_balance':
        if query.message.text != "Введите новый баланс:":
            await query.edit_message_text("Введите новый баланс:", reply_markup=main_menu())
        return SET_BALANCE

    elif query.data == 'delete_position':
        session = Session()
        positions = session.query(Position).filter(Position.user_id == user_id).all()

        if not positions:
            if query.message.text != "У тебя нет открытых позиций.":
                await query.edit_message_text("У тебя нет открытых позиций.", reply_markup=main_menu())
            return ConversationHandler.END
        else:
            msg = "📌 Выбери ID позиции, чтобы удалить:\n\n"
            for p in positions:
                msg += f"ID: {p.id} | {p.symbol} по {p.entry_price}\n"

            if query.message.text != msg:
                await query.edit_message_text(msg)
            await query.message.reply_text("Отправь ID позиции для удаления:")
            context.user_data['awaiting_delete'] = True
            return DELETE_POSITION

    elif query.data == 'add_position':
        if query.message.text != "Введите символ монеты (например BTC/USDT):":
            await query.edit_message_text("Введите символ монеты (например BTC/USDT):")
        return ADD_SYMBOL

    elif query.data == 'balance':
        session = Session()
        account = session.query(Account).filter(Account.user_id == user_id).first()
        balance = account.balance if account else 0
        if query.message.text != f"Ваш текущий баланс: {balance:.2f}$":
            await query.edit_message_text(f"Ваш текущий баланс: {balance:.2f}$", reply_markup=main_menu())

    elif query.data == 'view_positions':
        session = Session()
        positions = session.query(Position).filter(Position.user_id == user_id).all()
        if not positions:
            if query.message.text != "Нет открытых позиций.":
                await query.edit_message_text("Нет открытых позиций.", reply_markup=main_menu())
        else:
            msg = "📈 Открытые позиции:\n"
            for p in positions:
                current_price = get_current_price(p.symbol)
                if p.direction == 'BUY':
                    pnl_percent = ((current_price - p.entry_price) / p.entry_price) * 100
                else:
                    pnl_percent = ((p.entry_price - current_price) / p.entry_price) * 100
                msg += (
                    f"\nID: {p.id}\n"
                    f"Монета: {p.symbol}\n"
                    f"Тип: {p.direction}\n"
                    f"Цена входа: {p.entry_price}\n"
                    f"Текущая цена: {current_price}\n"
                    f"Прибыль: {pnl_percent:.2f}%\n"
                )
            if query.message.text != msg:
                await query.edit_message_text(msg, reply_markup=main_menu())

    elif query.data == 'history':
        session = Session()
        trades = session.query(Trade).filter(Trade.user_id == user_id).order_by(Trade.id.desc()).limit(10).all()
        if not trades:
            if query.message.text != "История пуста.":
                await query.edit_message_text("История пуста.", reply_markup=main_menu())
        else:
            msg = "📜 История сделок:\n"
            for trade in trades:
                msg += f"{trade.symbol}: {'🟢' if trade.pnl >= 0 else '🔴'} {trade.pnl:.2f}$\n"
            if query.message.text != msg:
                await query.edit_message_text(msg, reply_markup=main_menu())

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
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    try:
        context.user_data['leverage'] = float(update.message.text)
        reply_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📈 LONG (BUY)", callback_data="BUY"),
                InlineKeyboardButton("📉 SHORT (SELL)", callback_data="SELL")
            ]
        ])
        await update.message.reply_text("Выберите направление позиции:", reply_markup=reply_markup)
        return ADD_DIRECTION
    except ValueError:
        await update.message.reply_text("Введите корректное плечо!")
        return ADD_LEVERAGE

async def set_balance(update, context):
    session = Session()
    balance = float(update.message.text)
    user_id = update.effective_user.id
    account = session.query(Account).filter(Account.user_id == user_id).first()
    if not account:
        account = Account(user_id=user_id, balance=balance)
        session.add(account)
    else:
        account.balance = balance
    session.commit()
    await update.message.reply_text(f"Баланс установлен: {balance:.2f}$", reply_markup=main_menu())
    return ConversationHandler.END

async def handle_delete_position(update, context):
    session = Session()
    user_id = update.effective_user.id
    try:
        position_id = int(update.message.text)
        position = session.query(Position).filter(Position.id == position_id, Position.user_id == user_id).first()
        if not position:
            await update.message.reply_text("Позиция не найдена.", reply_markup=main_menu())
            return ConversationHandler.END

        current_price = get_current_price(position.symbol)
        if position.direction == 'BUY':
            pnl = (current_price - position.entry_price) * position.amount
        else:
            pnl = (position.entry_price - current_price) * position.amount

        account = session.query(Account).filter(Account.user_id == user_id).first()
        if not account:
            account = Account(user_id=user_id, balance=0)
            session.add(account)
        account.balance += pnl

        trade = Trade(user_id=user_id, symbol=position.symbol, pnl=pnl)
        session.add(trade)

        session.delete(position)
        session.commit()

        # Переназначаем ID позиций
        session.execute("DELETE FROM sqlite_sequence WHERE name='positions'")
        positions = session.query(Position).filter(Position.user_id == user_id).order_by(Position.id).all()
        for idx, p in enumerate(positions, start=1):
            p.id = idx
        session.commit()

        await update.message.reply_text(
            f"Позиция закрыта. PnL: {'🟢' if pnl >= 0 else '🔴'} {pnl:.2f}$\nБаланс обновлён: {account.balance:.2f}$",
            reply_markup=main_menu()
        )
    except Exception as e:
        await update.message.reply_text(f"Ошибка удаления позиции: {e}", reply_markup=main_menu())
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

async def add_direction(update, context):
    query = update.callback_query
    await query.answer()
    direction = query.data
    user_id = query.from_user.id

    symbol = context.user_data['symbol']
    entry_price = context.user_data['entry_price']
    trade_amount_usdt = context.user_data['trade_amount_usdt']
    leverage = context.user_data['leverage']

    amount = (trade_amount_usdt * leverage) / entry_price
    take_profit = entry_price * (1 + PROFIT_TARGET)
    stop_loss = entry_price * (1 - STOP_LOSS)

    session = Session()
    position = Position(
        user_id=user_id,
        symbol=symbol,
        entry_price=entry_price,
        amount=amount,
        take_profit=take_profit,
        stop_loss=stop_loss,
        direction=direction
    )
    session.add(position)
    session.commit()

    msg = (
        f"✅ Позиция добавлена:\n"
        f"{symbol}, цена: {entry_price}, плечо: {leverage}x\n"
        f"Тип: {direction}\n"
        f"Сумма: {trade_amount_usdt} USDT\n"
        f"Объем позиции: {amount:.6f} {symbol.split('/')[0]}\n"
        f"TP: {take_profit:.2f}, SL: {stop_loss:.2f}"
    )

    if query.message.text != msg:
        await query.edit_message_text(msg, reply_markup=main_menu())
    return ConversationHandler.END

def setup_handlers(app):
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(button_handler, pattern="^(set_balance|delete_position|add_position)$")
        ],
        states={
            ADD_DIRECTION: [CallbackQueryHandler(add_direction)],
            SET_BALANCE: [MessageHandler(filters.TEXT & allowed_filter, set_balance)],
            DELETE_POSITION: [MessageHandler(filters.TEXT & allowed_filter, handle_delete_position)],
            ADD_SYMBOL: [MessageHandler(filters.TEXT & allowed_filter, add_symbol)],
            ADD_PRICE: [MessageHandler(filters.TEXT & allowed_filter, add_price)],
            ADD_AMOUNT: [MessageHandler(filters.TEXT & allowed_filter, add_amount)],
            ADD_LEVERAGE: [MessageHandler(filters.TEXT & allowed_filter, add_leverage)]
        },
        fallbacks=[]
    )
    app.add_handler(CommandHandler("start", start, allowed_filter))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(balance|view_positions|history)$"))
    app.add_handler(conv_handler)
