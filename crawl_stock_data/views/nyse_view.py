import json
import math

import pandas as pd
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from crawl_stock_data.dao.stock_data_dao import check_exist_stock_data, delete_stock_data, get_stock_data_by_date
from crawl_stock_data.service.handle_data_service import HandleStockDataService
from crawl_stock_data.service.yahooquery_service import get_stock_data_by_yahoo_finance


def nyse_view(request):
    return render(request, 'index.html')


@csrf_exempt
@require_POST
def crawl_stock_data(request):
    data = json.loads(request.body)

    symbol = data.get('symbol', None)

    if symbol is None:
        return JsonResponse({'error': 'Invalid or missing parameter'}, status=400)

    if check_exist_stock_data(symbol):
        delete_stock_data(symbol)

    list_of_models = get_stock_data_by_yahoo_finance(symbol)

    # save the data to the database using the model save method

    for model in list_of_models:
        model.save()

    return JsonResponse({'message': 'successfully'})


@csrf_exempt
@require_POST
def compare_buy_sell(request):
    data = json.loads(request.body)

    symbol = data.get('symbol', None)

    if symbol is None:
        return JsonResponse({'error': 'Invalid or missing parameter'}, status=400)

    data = get_stock_data_by_date(symbol, '2023-01-01', '2023-12-31')
    data = pd.DataFrame.from_records([s.to_dict() for s in data])

    handle_stock_data_service = HandleStockDataService(data)
    stock_data_list = handle_stock_data_service.add_buy_or_sell_signal()

    # caculate the profit
    profit = 0
    for index, row in stock_data_list.iterrows():
        if not math.isnan(row['MACD_Buy_Signal_price']):
            profit -= row['close']
        elif not math.isnan(row['MACD_Sell_Signal_price']):
            profit += row['close']

    return JsonResponse({'profit_actual': profit, 'profit_model': profit, "symbol": symbol}, safe=False)
