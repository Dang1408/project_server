import json
import math

import pandas as pd
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

from crawl_stock_data.dao.compare_profit_dao import get_compare_profit_result
from crawl_stock_data.dao.stock_data_dao import check_exist_stock_data, delete_stock_data, get_stock_data_by_date, \
    get_stock_data
from crawl_stock_data.service.handle_data_service import HandleStockDataService
from crawl_stock_data.service.predict_stock_service import PredictStockService
from crawl_stock_data.service.yahooquery_service import get_stock_data_by_yahoo_finance
from crawl_stock_data.utils.read_file_util import read_file_export_list_of_symbol


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

    result = get_compare_profit_result(symbol)

    # fix two decimal places
    result.actual_profit = math.floor(result.actual_profit * 100) / 100
    result.predicted_profit = math.floor(result.predicted_profit * 100) / 100

    return JsonResponse({
        'profit_actual': result.actual_profit,
        'profit_model': result.predicted_profit,
        "symbol": symbol
    }, safe=False)


@csrf_exempt
@require_GET
def get_stock_symbols(request):
    list_of_company_and_symbol = read_file_export_list_of_symbol()

    return JsonResponse({'message': 'successfully', 'data': list_of_company_and_symbol}, safe=False)
