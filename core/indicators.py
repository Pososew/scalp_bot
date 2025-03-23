import pandas as pd
import ta

def calculate_rsi(df, period=14):
    return ta.momentum.rsi(df['close'], window=period)

def calculate_bollinger_bands(df, period=20):
    bb = ta.volatility.BollingerBands(df['close'], window=period)
    return bb.bollinger_hband(), bb.bollinger_lband()

def calculate_macd(df):
    macd = ta.momentum.MACD(df['close'])
    return macd.macd(), macd.macd_signal()

def calculate_support_resistance(df):
    support = df['low'].rolling(window=20).min()
    resistance = df['high'].rolling(window=20).max()
    return support, resistance

def calculate_volume_trend(df):
    df['volume_ma'] = df['volume'].rolling(window=20).mean()
    return df['volume_ma']
