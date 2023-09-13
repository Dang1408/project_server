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

    def add_buy_sell_signals(self):
        # Create a copy of the DataFrame to avoid modifying the original data
        df_copy = self.data.copy()

        if ('MACD_12_26_9' not in df_copy.columns
                and 'MACDs_12_26_9' not in df_copy.columns
                and 'MACDh_12_26_9' not in df_copy.columns):
            df_copy.ta.macd(fast=12, slow=26, signal=9, append=True)

        # Define conditions for buy and sell signals
        buy_condition = (df_copy['MACD_12_26_9'] > df_copy['MACDs_12_26_9']) & (
                    df_copy['MACD_12_26_9'].shift(1) <= df_copy['MACDs_12_26_9'].shift(1))
        sell_condition = (df_copy['MACD_12_26_9'] < df_copy['MACDs_12_26_9']) & (
                    df_copy['MACD_12_26_9'].shift(1) >= df_copy['MACDs_12_26_9'].shift(1))

        # Create columns for buy and sell signals
        df_copy['Buy_Signal'] = buy_condition
        df_copy['Sell_Signal'] = sell_condition

        return df_copy

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
