from datetime import datetime

from django.db import connection

from crawl_stock_data.models.stock_data_model import StockData


def get_stock_data(symbol):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT symbol, date_time, open, high, low, volume, close FROM stock_data WHERE symbol = %s",
            [symbol.upper()]
        )
        data = cursor.fetchall()

    # Create a list to store the model class objects
    stock_data_list = []

    # Loop through the fetched data and create model class objects
    for row in data:
        stock_data_obj = StockData(
            symbol=row[0],
            date_time=row[1],
            open=row[2],
            high=row[3],
            low=row[4],
            volume=row[5],
            close=row[6],
        )
        stock_data_list.append(stock_data_obj)

    return stock_data_list


def get_stock_data_by_date(symbol, date_start, date_end):
    ##convert the date to timestamp
    date_start = int(datetime.strptime(date_start, '%Y-%m-%d').timestamp()) * 1000
    date_end = int(datetime.strptime(date_end, '%Y-%m-%d').timestamp()) * 1000

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT symbol, date_time, open, high, low, volume, close "
            "FROM stock_data "
            "WHERE symbol = %s AND timestamp between %s AND %s",
            [symbol.upper(), date_start, date_end]
        )
        data = cursor.fetchall()

    # Create a list to store the model class objects
    stock_data_list = []

    # Loop through the fetched data and create model class objects
    for row in data:
        stock_data_obj = StockData(
            symbol=row[0],
            date_time=row[1],
            open=row[2],
            high=row[3],
            low=row[4],
            volume=row[5],
            close=row[6]
        )
        stock_data_list.append(stock_data_obj)

    return stock_data_list


def get_stock_data_by_date_drawl_chart(symbol, date_start, date_end):
    ##convert the date to timestamp
    date_start = int(datetime.strptime(date_start, '%Y-%m-%d').timestamp()) * 1000
    date_end = int(datetime.strptime(date_end, '%Y-%m-%d').timestamp()) * 1000

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT symbol, timestamp, open, high, low, volume, close, date_time "
            "FROM stock_data "
            "WHERE symbol = %s AND timestamp between %s AND %s order by timestamp asc",
            [symbol.upper(), date_start, date_end]
        )
        data = cursor.fetchall()

    # Create a list to store the model class objects
    stock_data_list = []

    # Loop through the fetched data and create model class objects
    for row in data:
        stock_data_obj = StockData(
            symbol=row[0],
            timestamp=row[1],
            open=row[2],
            high=row[3],
            low=row[4],
            volume=row[5],
            close=row[6],
            date_time=row[7]
        )
        stock_data_list.append(stock_data_obj)

    return stock_data_list


def check_exist_stock_data(symbol):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT symbol FROM stock_data WHERE symbol = %s",
            [symbol.upper()]
        )
        data = cursor.fetchall()

    if len(data) > 0:
        return True
    else:
        return False


def delete_stock_data(symbol):
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM stock_data WHERE symbol = %s",
            [symbol.upper()]
        )
    # commit
    connection.commit()
    return None


# insert data
def insert(model: StockData):
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO stock_data (symbol, date_time, timestamp, open, high, low, volume, close) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            [model.symbol, model.date_time, model.timestamp,
             model.open, model.high, model.low, model.volume, model.close]
        )
    # commit
    connection.commit()
    return None
