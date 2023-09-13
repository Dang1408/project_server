from django.db import connection

from crawl_stock_data.models.compare_profit_model import CompareProfitResultModel


def get_compare_profit_result(symbol):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT symbol, created_at, actual_profit, predicted_profit FROM compare_profit_result WHERE symbol = %s",
            [symbol.upper()]
        )
        data = cursor.fetchall()

    # Create a list to store the model class objects
    compare_profit_result_list = []

    # Loop through the fetched data and create model class objects
    for row in data:
        model = CompareProfitResultModel(
            symbol=row[0],
            created_at=row[1],
            actual_profit=row[2],
            predicted_profit=row[3],
        )

        compare_profit_result_list.append(model)

    return compare_profit_result_list[0]
