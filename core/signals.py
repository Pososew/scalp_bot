from core.exchange import fetch_ohlcv
from core.indicators import calculate_rsi, calculate_bollinger_bands, calculate_macd, calculate_support_resistance, calculate_volume_trend
from config.config import SYMBOLS

def generate_signal(symbol):
    df = fetch_ohlcv(symbol)

    df['rsi'] = calculate_rsi(df)
    df['bb_upper'], df['bb_lower'] = calculate_bollinger_bands(df)
    df['macd'], df['macd_signal'] = calculate_macd(df)
    df['support'], df['resistance'] = calculate_support_resistance(df)
    df['volume_trend'] = calculate_volume_trend(df)

    last_row = df.iloc[-1]

    if (
        last_row['rsi'] < 30 and
        last_row['close'] < last_row['bb_lower'] and
        last_row['macd'] > last_row['macd_signal'] and
        last_row['close'] > last_row['support'] and
        last_row['volume'] > last_row['volume_trend']
    ):
        signal_type = 'LONG'
    elif (
        last_row['rsi'] > 70 and
        last_row['close'] > last_row['bb_upper'] and
        last_row['macd'] < last_row['macd_signal'] and
        last_row['close'] < last_row['resistance'] and
        last_row['volume'] > last_row['volume_trend']
    ):
        signal_type = 'SHORT'
    else:
        signal_type = 'NEUTRAL'

    return {
        'symbol': symbol,
        'signal': signal_type,
        'close': last_row['close'],
        'rsi': last_row['rsi'],
        'bb_upper': last_row['bb_upper'],
        'bb_lower': last_row['bb_lower'],
        'macd': last_row['macd'],
        'macd_signal': last_row['macd_signal'],
        'support': last_row['support'],
        'resistance': last_row['resistance'],
        'volume': last_row['volume'],
        'volume_trend': last_row['volume_trend']
    }

def check_signals_for_all_symbols():
    signals = []
    for symbol in SYMBOLS:
        signal = generate_signal(symbol)
        signals.append(signal)
    return signals
