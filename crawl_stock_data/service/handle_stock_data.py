import pandas as pd
import pandas_ta as ta
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import date

from crawl_stock_data.service.predict_stock import set_index
import crawl_stock_data.dao as dao

def MACD_Strategy(df, risk):
    MACD_Buy = []
    MACD_Sell = []
    position = False

    for i in range(0, len(df)):
        if df['MACD_12_26_9'][i] > df['MACDs_12_26_9'][i]:
            MACD_Sell.append(np.nan)
            if position == False:
                MACD_Buy.append(df['adj_close'][i])
                position = True
            else:
                MACD_Buy.append(np.nan)
        elif df['MACD_12_26_9'][i] < df['adj_close'][i]:
            MACD_Buy.append(np.nan)
            if position == True:
                MACD_Sell.append(df['adj_close'][i])
                position = False
            else:
                MACD_Sell.append(np.nan)
        elif position == True and df['adj_close'][i] < MACD_Buy[-1] * (1 - risk):
            MACD_Sell.append(df["adj_close"][i])
            MACD_Buy.append(np.nan)
            position = False
        elif position == True and df['adj_close'][i] < df['adj_close'][i - 1] * (1 - risk):
            MACD_Sell.append(df["adj_close"][i])
            MACD_Buy.append(np.nan)
            position = False
        else:
            MACD_Buy.append(np.nan)
            MACD_Sell.append(np.nan)

    df['MACD_Buy_Signal_price'] = MACD_Buy
    df['MACD_Sell_Signal_price'] = MACD_Sell

    return df


def MACD_color(data):
    MACD_color = []
    for i in range(0, len(data)):
        if data['MACDh_12_26_9'][i] > data['MACDh_12_26_9'][i - 1]:
            MACD_color.append(True)
        else:
            MACD_color.append(False)
    return MACD_color

def add_buy_or_sell_signal(symbol, date_start, date_end):
    # check the data is dataframe or not
    data = dao.get_stock_data_by_date(symbol, date_start, date_end)

    data = set_index(data)

    # calculate the macd
    macd = ta.macd(data['close'])

    data = pd.concat([data, macd], axis=1).reindex(data.index)

    data = MACD_Strategy(data, 0.025)
    data['positive'] = MACD_color(data)

    return data