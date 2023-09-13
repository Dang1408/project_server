import uuid
from typing import List

from pandas import DataFrame

from yahooquery import Ticker
import datetime

from crawl_stock_data.models.stock_data_model import StockData


def get_stock_data_by_yahoo_finance(symbol) -> list[StockData]:
    # https://pypi.org/project/yahooquery/

    try:
        ticker = Ticker(symbol, asynchronous=True)
    except Exception as e:
        raise e

    list_of_stock_data = []

    currency = "USD"

    # get stock price data
    data = ticker.history(period="max")
    list_index_date = data.index.to_list()

    for item in list_index_date:
        _, date_index = item

        if len(str(date_index)) == 25:
            try:
                date_index = datetime.datetime.strptime(date_index, '%Y-%m-%d %H:%M:%S%z')
                date_index = date_index.strptime('%Y-%m-%d')
            except ValueError:
                print(f"The date string '{date_index}' does not match the format.")

        data_row = data.loc[(symbol, date_index)]
        datetime_obj = datetime.datetime.combine(date_index, datetime.time())

        my_stock_data = StockData()
        my_stock_data.symbol = symbol
        my_stock_data.open = data_row['open']
        my_stock_data.high = data_row['high']
        my_stock_data.low = data_row['low']
        my_stock_data.close = data_row['close']
        my_stock_data.volume = data_row['volume']
        my_stock_data.adj_close = data_row['adjclose']
        my_stock_data.currency = currency
        my_stock_data.created_at = int(datetime.datetime.now().timestamp() * 1000000)
        my_stock_data.date_time = date_index
        my_stock_data.timestamp = int(datetime_obj.timestamp() * 1000)
        my_stock_data.type_profile = 1
        my_stock_data.symbol_id = str(uuid.uuid4())

        list_of_stock_data.append(my_stock_data)

    return list_of_stock_data
