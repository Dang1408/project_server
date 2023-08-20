from crawl_stock_data.dao.stock_data_dao import check_exist_stock_data, delete_stock_data
from crawl_stock_data.service.yahooquery_service import get_stock_data_by_yahoo_finance
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from crawl_stock_data.training.SVM import SVM_model

symbol_list = ['AAPL', 'AMD', 'GOOGL']


def crawl_stock_data_every_day():
    # Your code to crawl stock data goes here

    # add the logs to see when running the cron job
    print("Cron job is running")

    for symbol in symbol_list:
        if check_exist_stock_data(symbol):
            delete_stock_data(symbol)

        list_of_models = get_stock_data_by_yahoo_finance(symbol)

        # save the data to the database using the model save method
        for model in list_of_models:
            model.save()
        print("Cron job added data for symbol: " + symbol)

    print("Cron job is finished")


def training_SVM_auto():
    print("Cron job for training SVM is running")

    for symbol in symbol_list:
        print("Cron job for training SVM is running for symbol: " + symbol)
        path = ('/mnt/learning/last_project/app/server/stock_server/'
                'crawl_stock_data/training/checkpoint/online_learning_model/svm/SVM_{}_13-23.pkl'.format(symbol))
        SVM = SVM_model(symbol=symbol, path=path)
        SVM.training()
        print("Cron job for training SVM is finished for symbol: " + symbol)
    print("Cron job for training SVM is finished")


def setup_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(crawl_stock_data_every_day, CronTrigger.from_crontab('45 23 * * *'))
    scheduler.add_job(training_SVM_auto, CronTrigger.from_crontab('48 23 * * *'))  #
    scheduler.start()
