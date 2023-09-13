import json
import math
import os
import uuid
from datetime import datetime, timedelta
from uuid import UUID

import pandas as pd
import pytz
import crawl_stock_data.dao.training_log_dao as training_log_dao

from crawl_stock_data.dao.stock_data_dao import check_exist_stock_data, delete_stock_data, get_stock_data, \
    get_stock_data_by_date
from crawl_stock_data.models.compare_profit_model import CompareProfitResultModel
from crawl_stock_data.models.traning_log_model import TrainingLogModel
from crawl_stock_data.service.handle_data_service import HandleStockDataService
from crawl_stock_data.service.predict_stock_service import PredictStockService
from crawl_stock_data.service.yahooquery_service import get_stock_data_by_yahoo_finance
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from crawl_stock_data.training.SVM import SVM_model
from crawl_stock_data.utils.date_util import get_the_list_of_date_in_n_week_age, get_the_last_one_and_two_day
from crawl_stock_data.utils.read_file_util import read_file_export_list_of_symbol
from crawl_stock_data.views.general_view import save_predicted_stock_value_log
from django.db import transaction


def setup_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(crawl_stock_data_every_day, CronTrigger.from_crontab('46 15 * * *'))
    # scheduler.add_job(create_predicted_stock_value_auto, CronTrigger.from_crontab('33 12 * * *'))  #
    scheduler.add_job(create_saving_checkpoint_auto, CronTrigger.from_crontab('29 16 * * *'))
    # scheduler.add_job(using_checkpoint_for_prediction_to_compare_profit, CronTrigger.from_crontab('59 15 * * *'))
    scheduler.add_job(training_SVM_auto, CronTrigger.from_crontab('52 15 * * *'))
    scheduler.start()


def get_symbols():
    symbol_list = read_file_export_list_of_symbol()
    symbols = [item['symbol'] for item in symbol_list]
    return symbols


def crawl_stock_data_every_day():
    # Your code to crawl stock data goes here

    # add the logs to see when running the cron job
    print("Cron job is running")
    symbols = get_symbols()

    for symbol in symbols:
        if check_exist_stock_data(symbol):
            delete_stock_data(symbol)

        list_of_models = get_stock_data_by_yahoo_finance(symbol)

        # save the data to the database using the model save method
        for model in list_of_models:
            model.save()
        print("Cron job added data for symbol: " + symbol)

    print("Cron job is finished")


@transaction.atomic
def training_SVM_auto():
    print("Cron job for training SVM is running")
    symbol_list = read_file_export_list_of_symbol()
    symbols = [item['symbol'] for item in symbol_list]

    for symbol in symbols:
        print("Cron job for training SVM is running for symbol: " + symbol)
        path = ('/mnt/learning/last_project/app/server/stock_server/'
                'crawl_stock_data/training/checkpoint/online_learning_model/svm/SVM_{}_13-23.pkl'.format(symbol))

        if not check_log_for_skipping(model="SVM", symbol=symbol):
            os.remove(path)

        SVM = SVM_model(symbol=symbol, path=path)
        SVM.training()
        saving_log(model="SVM", symbol=symbol)
        print("Cron job for training SVM is finished for symbol: " + symbol)
    print("Cron job for training SVM is finished")


def saving_log(model, symbol):
    current_date = datetime.now()

    training_log_model = TrainingLogModel()
    training_log_model.model = model
    training_log_model.symbol = symbol
    training_log_model.created_at = int(current_date.timestamp() * 1000000)
    training_log_model.training_date_at = str(current_date.strftime("%Y-%m-%d"))
    training_log_model.is_success = True
    training_log_model.save()


@transaction.atomic
def create_predicted_stock_value_auto():
    print("Cron job start for stock value prediction")

    symbols = get_symbols()

    for symbol in symbols:
        print("Running for symbol: " + symbol)
        the_list_of_date = get_the_list_of_date_in_n_week_age(5)

        for date in the_list_of_date:
            stock_data_list = get_stock_data(symbol)
            stock_data_list_data_frame = pd.DataFrame.from_records([s.to_dict() for s in stock_data_list])

            temp_list = stock_data_list_data_frame
            # convert date to datetime and minus 2 day of date
            date_time = datetime.strptime(date, '%Y-%m-%d')
            last_one_day, last_two_day = get_the_last_one_and_two_day(date_time)

            path = ('/mnt/learning/last_project/app/server/stock_server/' +
                    'crawl_stock_data/training/checkpoint'
                    '/online_learning_model/svm/tmp/SVM_{}_13-23({}).pkl'.format(symbol, last_one_day))

            svm = SVM_model(symbol, path)
            svm.training(last_two_day)

            predict_stock_service = PredictStockService(symbol, temp_list)
            prediction = predict_stock_service.predict_in_the_specific_date_with_SVM_model(last_one_day)

            save_predicted_stock_value_log(symbol, "SVM", prediction, date)
    print("Cron job end for stock value prediction")


@transaction.atomic
def using_checkpoint_for_prediction_to_compare_profit():
    print("Cron job start for stock value prediction")
    symbols = get_symbols()

    for symbol in symbols:
        print("Running for symbol: " + symbol)
        data = get_stock_data_by_date(symbol, '2023-01-01', '2023-12-31')
        data = pd.DataFrame.from_records([s.to_dict() for s in data])

        handle_stock_data_service = HandleStockDataService(data)
        stock_data_list_actual = handle_stock_data_service.add_buy_sell_signals()

        data = get_stock_data(symbol)
        data = pd.DataFrame.from_records([s.to_dict() for s in data])

        predict_stock_service = PredictStockService(symbol, data)

        predict_stock_in_the_range_of_date = (predict_stock_service
                                              .predict_in_the_time_with_SVM_model('2023-01-01', '2023-12-31'))

        stock_data_list_prediction = stock_data_list_actual.copy()
        stock_data_list_prediction['close'] = predict_stock_in_the_range_of_date["predicted_mean"]

        handle_stock_data_service = HandleStockDataService(stock_data_list_prediction)
        stock_data_list_prediction = handle_stock_data_service.add_buy_sell_signals()

        # calculate the profit
        profit = 100000
        for index, row in stock_data_list_actual.iterrows():
            if not math.isnan(row['Buy_Signal']):
                profit -= row['close']
            elif not math.isnan(row['Sell_Signal']):
                profit += row['close']

        # calculate the profit for prediction
        profit_prediction = 100000
        for index, row in stock_data_list_prediction.iterrows():
            if not math.isnan(row['Buy_Signal']):
                profit_prediction -= row['close']
            elif not math.isnan(row['Sell_Signal']):
                profit_prediction += row['close']

        model = CompareProfitResultModel()
        model.symbol = symbol
        model.actual_profit = profit
        model.predicted_profit = profit_prediction
        model.created_at = int(datetime.now().timestamp() * 1000000)
        model.save()

    print("Cron job end for stock value prediction")


def create_saving_checkpoint_auto():
    print("Cron job start for saving checkpoint from 2013-2022")

    symbols = get_symbols()

    for symbol in symbols:
        print("Running for symbol: " + symbol)

        path = ('/mnt/learning/last_project/app/server/stock_server/' +
                'crawl_stock_data/training/checkpoint'
                '/svm/SVM_{}_13-22.pkl'.format(symbol))

        svm = SVM_model(symbol, path, True)
        svm.training()

    print("Cron job end for stock value prediction")


def check_log_for_skipping(model, symbol):
    current_date = datetime.now()
    before_date = current_date - timedelta(days=1)

    timezone = pytz.timezone('Asia/Ho_Chi_Minh')

    date_to_check = timezone.localize(before_date)

    if date_to_check.weekday() == 5:
        before_date = before_date - timedelta(days=1)
    elif date_to_check.weekday() == 6:
        before_date = before_date - timedelta(days=2)

    training_log = training_log_dao.get_training_log_by_date(symbol=symbol, model=model,
                                                             date=str(before_date.strftime("%Y-%m-%d")))

    return False if training_log is None else True
