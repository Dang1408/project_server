import math
from datetime import timezone, timedelta

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
import json
from crawl_stock_data.dao.stock_data_dao import *
from crawl_stock_data.models.predicted_stock_value_model import PredictedStockValueModel
from crawl_stock_data.service.handle_data_service import *
from crawl_stock_data.service.predict_stock_service import *
from crawl_stock_data.service.yahooquery_service import get_stock_data_by_yahoo_finance
import pandas as pd
import pytz
from pandas_market_calendars import get_calendar
import crawl_stock_data.dao.predicted_stock_value_dao as predicted_stock_data_dao
from crawl_stock_data.utils.date_util import *
from crawl_stock_data.training.SVM import SVM_model
import pandas_ta as ta


# Create your views here.

# create a post request to get the stock data receive the symbol and the date from request body
# and return the stock data for that date and symbol

@csrf_exempt
@require_POST
def get_stock_value_by_date_drawl_chart(request):
    # print(request.body)
    data = json.loads(request.body)

    symbol = data.get('symbol', None)
    date_start = data.get('date_start', None)
    date_end = data.get('date_end', None)

    if symbol is None or date_start is None or date_end is None:
        return JsonResponse({'error': 'Invalid or missing parameter'}, status=400)

    if not check_exist_stock_data(symbol):
        return JsonResponse({'error': 'This stock symbol does not extinct or be invalid'}, status=400)

    stock_data_list = get_stock_data(symbol)
    stock_data_list = pd.DataFrame.from_records([s.to_dict() for s in stock_data_list])

    stock_data_list["Date"] = pd.to_datetime(stock_data_list["date"])
    # set date_time to index
    stock_data_list.set_index('Date', inplace=True)
    stock_data_list = stock_data_list.sort_index(ascending=True)

    # get all the value of stock_data_list dataframe and convert to json format.
    # Get the value of each row and the value of index (convert to JS timestamp)

    stock_data_list.ta.macd(fast=12, slow=26, signal=9, append=True)
    handle_stock_service = HandleStockDataService(stock_data_list)

    stock_data_list = handle_stock_service.add_buy_sell_signals()

    stock_data_list = stock_data_list[date_start:date_end]
    # convert to json format
    response_data = stock_data_list.to_dict('records')

    return JsonResponse(response_data, safe=False)


@csrf_exempt
@require_POST
def crawl_stock_data(request):
    # symbol = request.POST.get('symbol')
    # date_start = request.POST.get('date_start')
    # date_end = request.POST.get('date_end')
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
def predict_stock_value_on_the_next_date(request):
    prediction = None
    data = json.loads(request.body)

    symbol = data.get('symbol', None)
    model = data.get('model', None)
    market = data.get('market', None)

    if symbol is None or model is None or market is None:
        return JsonResponse({'error': 'Invalid or missing parameter'}, status=400)

    stock_data_list = get_stock_data(symbol)
    stock_data_list = pd.DataFrame.from_records([s.to_dict() for s in stock_data_list])
    predict_stock_service = PredictStockService(symbol, stock_data_list)
    date_start, date_end = get_the_time_of_n_week_ago(3)

    # get the data close from the database by the symbol and the date in 2023
    stock_data_list = get_stock_data_by_date_drawl_chart(symbol, date_start, date_end)

    actual_value = [{
        "timestamp": convert_to_GMT_timestamp(data.date_time),
        "close": data.close
    } for data in stock_data_list]

    the_next_date = get_the_next_date(stock_data_list[-1].date_time, market)

    if model == 'SVM':
        predicted_stock_value = predicted_stock_data_dao.get_predicted_stock_value_by_date(symbol, the_next_date, model)

        if predicted_stock_value is None:
            prediction = predict_stock_service.next_date_with_SVM_model()

            # save the predicted value to the database
            save_predicted_stock_value_log(symbol, model, prediction, the_next_date)
        else:
            prediction = predicted_stock_value.predicted_value
    else:
        return JsonResponse({'error': 'Invalid or missing parameter'}, status=400)

    if prediction is None:
        return JsonResponse({'error': 'Having error'}, status=400)

    predicted_stock_value_list = predicted_stock_data_dao.get_from_date_to_date(symbol, model, date_start)
    extracted_data = [{
        "timestamp": convert_to_GMT_timestamp(data.predicted_date_at),
        "close": data.predicted_value
    } for data in predicted_stock_value_list]

    return JsonResponse({'actual_data': actual_value, 'predicted_data': extracted_data}, safe=False)


@csrf_exempt
@require_POST
def test_training_model(request):
    data = json.loads(request.body)

    symbol = data.get('symbol', None)
    model = data.get('model', None)

    if symbol is None or model is None:
        return JsonResponse({'error': 'Invalid or missing parameter'}, status=400)


def save_predicted_stock_value_log(symbol, model, prediction_value, date):
    date_time = datetime.strptime(date, '%Y-%m-%d')
    predicted_stock_value_model = PredictedStockValueModel()

    predicted_stock_value_model.symbol = symbol
    predicted_stock_value_model.predicted_date_at = date
    predicted_stock_value_model.predicted_model = model
    predicted_stock_value_model.is_success = True
    predicted_stock_value_model.predicted_value = prediction_value
    predicted_stock_value_model.predicted_date_at_in_timestamp = int(date_time.timestamp() * 1000000)
    predicted_stock_value_model.created_at = int(datetime.now().timestamp() * 1000000)
    predicted_stock_value_model.save()
