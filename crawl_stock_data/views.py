from datetime import timezone

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
import json
from .dao import *
from .service.handle_stock_data import add_buy_or_sell_signal
from .service.predict_stock import predict_stock_by_SARIMAX_model, predicted_stock_by_SVM_model, \
    predicted_stock_by_LSTM_model, predict_stock_by_SARIMAX_model_only_next_date
from .service.yahooquery_service import get_stock_data_by_yahoo_finance
from .training.SARIMAX_apple import training_model
from pandas_market_calendars import get_calendar
import pandas as pd
import pytz


# Create your views here.

@require_GET
def get_stock_value(request, symbol):
    # Replace this with your stock data retrieval logic using pandas_ta
    # For demonstration purposes, we will use sample data
    stock_data_list = get_stock_data_by_date(symbol)

    # Convert the list of model class objects to JSON and return as API response
    response_data = [{
        "date_time": data.date_time,
        "open": data.open,
        "high": data.high,
        "low": data.low,
        "volume": data.volume,
        "close": data.close
    } for data in stock_data_list]

    return JsonResponse(response_data, safe=False)


# create a post request to get the stock data receive the symbol and the date from request body
# and return the stock data for that date and symbol

@csrf_exempt
@require_POST
def get_stock_value_by_date(request):
    # symbol = request.POST.get('symbol')
    # date_start = request.POST.get('date_start')
    # date_end = request.POST.get('date_end')
    data = json.loads(request.body)

    symbol = data.get('symbol', None)
    date_start = data.get('date_start', None)
    date_end = data.get('date_end', None)

    if symbol is None or date_start is None or date_end is None:
        return JsonResponse({'error': 'Invalid or missing parameter'}, status=400)

    stock_data_list = get_stock_data_by_date(symbol, date_start, date_end)

    response_data = [{
        "date_time": data.date_time,
        "open": data.open,
        "high": data.high,
        "low": data.low,
        "volume": data.volume,
        "close": data.close
    } for data in stock_data_list]

    return JsonResponse(response_data, safe=False)


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

    stock_data_list = add_buy_or_sell_signal(symbol, date_start, date_end)

    response_data = [{
        "timestamp": data.timestamp,
        "close": data.close,
        "open": data.open,
        "high": data.high,
        "low": data.low,
        "volume": data.volume
    } for data in stock_data_list]

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
    ##save the data to the database using the model save method
    for model in list_of_models:
        model.save()

    return JsonResponse({'message': 'successfully'})


@csrf_exempt
@require_POST
def predict_stock_value_by_the_number_date(request):
    # symbol = request.POST.get('symbol')
    # date_start = request.POST.get('date_start')
    # date_end = request.POST.get('date_end')
    data = json.loads(request.body)
    the_number_date = data.get('the_number_date', None)
    symbol = data.get('symbol', None)
    model = data.get('model', None)

    if the_number_date is None or symbol is None:
        return JsonResponse({'error': 'Invalid or missing parameter'}, status=400)

    if model == 'SARIMAX':
        prediction, rmse, mape = predict_stock_by_SARIMAX_model(symbol, int(the_number_date))
    elif model == 'SVM':
        prediction, rmse, mape = predicted_stock_by_SVM_model(symbol, int(the_number_date))
    elif model == 'LSTM':
        prediction, rmse, mape = predicted_stock_by_LSTM_model(symbol, int(the_number_date))
    else:
        return JsonResponse({'error': 'Invalid or missing parameter'}, status=400)
    # get the data close from the database by the symbol and the date in 2023
    stock_data_list = get_stock_data_by_date_drawl_chart(symbol, '2023-07-01', '2023-12-31')
    actual_value = [{
        "timestamp": convert_to_UTC_timespamp(data.timestamp),
        "close": data.close
    } for data in stock_data_list]

    extracted_data = []

    # Iterate through the DataFrame rows and save the timestamp and predicted_mean value into the dictionary
    for index in range(int(the_number_date)):
        row = prediction.iloc[index]
        # get the timestamp in each 3 last records (same direction with the prediction) in the actual_value
        # for example the last record in the prediction is 2023-07-19
        # and the last record in the actual_value is 2023-07-19

        timestamp_milliseconds = actual_value[index - int(the_number_date)]['timestamp']
        predicted_mean_value = row['predicted_mean']
        extracted_data_item = {"timestamp": timestamp_milliseconds, "close": predicted_mean_value}
        extracted_data.append(extracted_data_item)

    # add first into extracted_data
    extracted_data.insert(0, {"timestamp": actual_value[-(int(the_number_date) + 1)]['timestamp'],
                              "close": actual_value[-(int(the_number_date) + 1)]['close']})

    return JsonResponse({'actual_data': actual_value, 'predicted_data': extracted_data, 'rmse': rmse, 'mape': mape},
                        safe=False)


from pandas_market_calendars import get_calendar


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
    # symbol = request.POST.get('symbol')
    # date_start = request.POST.get('date_start')
    # date_end = request.POST.get('date_end')
    prediction = None
    data = json.loads(request.body)

    symbol = data.get('symbol', None)
    model = data.get('model', None)

    if symbol is None:
        return JsonResponse({'error': 'Invalid or missing parameter'}, status=400)

    if model == 'SARIMAX':
        prediction = predict_stock_by_SARIMAX_model_only_next_date(symbol)
    elif model == 'SVM':
        # prediction, rmse, mape = predicted_stock_by_SVM_model(symbol, int(the_number_date))
        # TO DO
        None
    elif model == 'LSTM':
        # prediction, rmse, mape = predicted_stock_by_LSTM_model(symbol, int(the_number_date))
        # TO DO
        None
    else:
        return JsonResponse({'error': 'Invalid or missing parameter'}, status=400)

    if prediction is None:
        return JsonResponse({'error': 'Having error'}, status=400)

    # get the data close from the database by the symbol and the date in 2023
    stock_data_list = get_stock_data_by_date_drawl_chart(symbol, '2023-07-01', '2023-12-31')
    actual_value = [{
        "timestamp": convert_to_UTC_timespamp(data.timestamp),
        "close": data.close
    } for data in stock_data_list]

    extracted_data = []

    the_next_date_timestamp = actual_value[-1]['timestamp']

    # Get the last record in actual_value and add it into extracted_data
    extracted_data.append({"timestamp": the_next_date_timestamp, "close": actual_value[-1]['close']})
    the_next_date_timestamp = get_the_next_date(the_next_date_timestamp)
    # finally, add the predicted value into extracted_data
    extracted_data.append({"timestamp": the_next_date_timestamp, "close": prediction})


    return JsonResponse({'actual_data': actual_value, 'predicted_data': extracted_data}, safe=False)


@csrf_exempt
@require_GET
def test_training_model(request):
    training_model()
    return JsonResponse({'message': 'successfully'})


def home_view(request):
    return render(request, 'index.html')


def convert_to_UTC_timespamp(timestamp):
    UTC_timestamp = datetime.fromtimestamp(int(timestamp) / 1000, timezone.utc)
    return int(UTC_timestamp.timestamp() * 1000)
