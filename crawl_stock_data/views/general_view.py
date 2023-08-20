import math
from datetime import timezone

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
import json
from crawl_stock_data.dao import *
from crawl_stock_data.service.handle_data_service import *
from crawl_stock_data.service.predict_stock_service import *
from crawl_stock_data.service.yahooquery_service import get_stock_data_by_yahoo_finance
import pandas as pd
import pytz
from pandas_market_calendars import get_calendar


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

    stock_data_list = get_stock_data_by_date(symbol, date_start, date_end)

    # get all the value of stock_data_list dataframe and convert to json format.
    # Get the value of each row and the value of index (convert to JS timestamp)

    response_data = []
    for row in stock_data_list:
        date_object = datetime.strptime(row.date_time, '%Y-%m-%d')
        utc_timezone = pytz.timezone('UTC')
        date_object_utc = utc_timezone.localize(date_object)

        temp_dic = {
            "date": int(date_object_utc.timestamp()) * 1000,
            "open": row.open,
            "high": row.high,
            "low": row.low,
            "close": row.close,
            "volume": row.volume,
        }
        response_data.append(temp_dic)

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


def get_the_next_date(the_next_date_timestamp, exchange='NYSE'):
    # Create a trading calendar for the specified exchange
    trading_calendar = get_calendar(exchange)

    # Convert the timestamp to a Python datetime object
    the_next_date = datetime.fromtimestamp(the_next_date_timestamp / 1000)

    # Convert the offset-naive datetime to an offset-aware datetime using UTC timezone
    the_next_date = pytz.utc.localize(the_next_date)

    # Get the next trading date after the given date
    next_trading_dates = trading_calendar.valid_days(start_date=the_next_date,
                                                     end_date=the_next_date + pd.Timedelta(days=365))
    # Find the first trading date after the given date
    for date in next_trading_dates:
        if date > the_next_date:
            next_trading_date = date
            break
    else:
        # If no trading date is found within the next year, return the last date in the list
        next_trading_date = next_trading_dates[-1]

    # Access the next trading date and get its timestamp
    next_trading_date_timestamp = int(next_trading_date.timestamp() * 1000)

    return next_trading_date_timestamp


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

    if model == 'SVM':
        prediction = predict_stock_service.next_date_with_SVM_model()
    elif model == 'LSTM':
        # prediction, rmse, mape = predicted_stock_by_LSTM_model(symbol, int(the_number_date))
        # TODO
        None
    else:
        return JsonResponse({'error': 'Invalid or missing parameter'}, status=400)

    if prediction is None:
        return JsonResponse({'error': 'Having error'}, status=400)

    # get the data close from the database by the symbol and the date in 2023
    stock_data_list = get_stock_data_by_date_drawl_chart(symbol, '2023-07-25', '2023-12-31')
    actual_value = [{
        "timestamp": convert_to_UTC_timespamp(data.timestamp),
        "close": data.close
    } for data in stock_data_list]

    extracted_data = []

    the_next_date_timestamp = actual_value[-1]['timestamp']

    # Get the last record in actual_value and add it into extracted_data
    extracted_data.append({"timestamp": the_next_date_timestamp, "close": actual_value[-1]['close']})
    the_next_date_timestamp = get_the_next_date(the_next_date_timestamp, market)
    # finally, add the predicted value into extracted_data
    extracted_data.append({"timestamp": the_next_date_timestamp, "close": prediction})

    return JsonResponse({'actual_data': actual_value, 'predicted_data': extracted_data}, safe=False)


# @csrf_exempt
# @require_GET
# def test_training_model(request):
#     training_model()
#     return JsonResponse({'message': 'successfully'})


def convert_to_UTC_timespamp(timestamp):
    UTC_timestamp = datetime.fromtimestamp(int(timestamp) / 1000, timezone.utc)
    return int(UTC_timestamp.timestamp() * 1000)
