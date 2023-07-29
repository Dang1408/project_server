from crawl_stock_data.dao import check_exist_stock_data, delete_stock_data
from crawl_stock_data.service.yahooquery_service import get_stock_data_by_yahoo_finance
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from crawl_stock_data.training.SARIMAX_apple import training_model

def crawl_stock_data_every_day():
    # Your code to crawl stock data goes here

    # add the logs to see when running the cron job
    print("Cron job is running")

    symbol_list = ['AAPL', 'AMD', 'GOOGL']

    for symbol in symbol_list:
        if check_exist_stock_data(symbol):
            delete_stock_data(symbol)

        list_of_models = get_stock_data_by_yahoo_finance(symbol)

        # save the data to the database using the model save method
        for model in list_of_models:
            model.save()
        print("Cron job added data for symbol: " + symbol)

    print("Cron job is finished")

def trainning_SARIMAX_auto():
    print("Cron job for training SARIMAX is running")
    training_model()
    print("Cron job for training SARIMAX is finished")

def setup_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(crawl_stock_data_every_day, CronTrigger.from_crontab('28 1 * * *'))
    # scheduler.add_job(trainning_SARIMAX_auto, CronTrigger.from_crontab('* * * * *'))  #
    scheduler.start()
