import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime
from crawl_stock_data.models.stock_data_model import StockData
import pytz

from crawl_stock_data.service.process_data_service import ProcessDataService


class HandleStockDataService:

    def __init__(self, data: pd.DataFrame):
        self.data = data

    @staticmethod
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

    @staticmethod
    def MACD_color(data: pd.DataFrame):
        MACD_color = []
        for i in range(0, len(data)):
            if data['MACDh_12_26_9'][i] > data['MACDh_12_26_9'][i - 1]:
                MACD_color.append(True)
            else:
                MACD_color.append(False)
        return MACD_color

    def add_buy_or_sell_signal(self):
        # check the data is dataframe or not

        process_data_service = ProcessDataService(self.data)

        data = process_data_service.rename_column_and_set_type(None)

        # calculate the macd
        macd = ta.macd(data['close'])

        data = pd.concat([data, macd], axis=1).reindex(data.index)

        data = self.MACD_Strategy(data, 0.025)
        data['positive'] = self.MACD_color(data)

        return data

    def parse_df_to_stock_data_model(self, name):
        stock_data_list = []

        for index, row in self.data.iterrows():
            utc_timezone = pytz.timezone('UTC')
            date_object_utc = utc_timezone.localize(index)

            stock_data_obj = StockData()
            stock_data_obj.symbol = name
            # convert datetime to string
            stock_data_obj.date_time = index
            stock_data_obj.timestamp = int(date_object_utc.timestamp()) * 1000
            stock_data_obj.open = row['open']
            stock_data_obj.high = row['high']
            stock_data_obj.low = row['low']
            stock_data_obj.volume = row['volume']
            stock_data_obj.close = row['close']
            stock_data_obj.currency = 'VND'
            stock_data_obj.created_at = int(datetime.now().timestamp() * 1000000)

            stock_data_list.append(stock_data_obj)

        return stock_data_list
