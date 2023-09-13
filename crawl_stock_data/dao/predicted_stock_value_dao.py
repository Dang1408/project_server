from datetime import datetime

from django.db import connection

from crawl_stock_data.models.predicted_stock_value_model import PredictedStockValueModel


def get_predicted_stock_value_by_date(symbol, date, model):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT symbol, predicted_date_at, predicted_value, predicted_model, predicted_date_at_in_timestamp "
            "FROM predicted_stock_value "
            "WHERE symbol = %s AND predicted_date_at = %s and predicted_model = %s and is_success = True",
            [symbol.upper(), date, model.upper()]
        )
        data = cursor.fetchall()

    if len(data) == 0:
        return None
    # convert data to predicted_stock_value_model
    predicted_stock_value_list = []

    for row in data:
        predicted_stock_value_obj = PredictedStockValueModel(
            symbol=row[0],
            predicted_date_at=row[1],
            predicted_value=row[2],
            predicted_model=row[3],
            predicted_date_at_in_timestamp=row[4],
        )
        predicted_stock_value_list.append(predicted_stock_value_obj)

    return predicted_stock_value_list[0]


def get_from_date_to_date(symbol, model, date_start):
    # convert the date to timestamp
    date_start = int(datetime.strptime(date_start, '%Y-%m-%d').timestamp()) * 1000000

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT symbol, predicted_date_at, predicted_value, predicted_model, predicted_date_at_in_timestamp "
            "FROM predicted_stock_value "
            "WHERE symbol = %s AND predicted_date_at_in_timestamp >= %s "
            "and predicted_model = %s and is_success = True order by predicted_date_at_in_timestamp asc",
            [symbol.upper(), date_start, model.upper()]
        )
        data = cursor.fetchall()

    # convert data to predicted_stock_value_model
    predicted_stock_value_list = []

    for row in data:
        predicted_stock_value_obj = PredictedStockValueModel(
            symbol=row[0],
            predicted_date_at=row[1],
            predicted_value=row[2],
            predicted_model=row[3],
            predicted_date_at_in_timestamp=row[4],
        )
        predicted_stock_value_list.append(predicted_stock_value_obj)

    return predicted_stock_value_list
