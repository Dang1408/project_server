import warnings
import os
import joblib
import pandas as pd
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler

from crawl_stock_data.dao.stock_data_dao import get_stock_data
from crawl_stock_data.service.process_data_service import ProcessDataService


class SVM_model():
    def __init__(self, symbol, path, training_for_test: bool = False):
        self.symbol = symbol

        self.input_feature = ['open', 'high', 'low', 'close', 'volume',
                              'NATR_3', 'RSI_3', 'ADX_3', 'CCI_3_0.015',
                              'ROC_3', 'STOCHk_14_3_3', 'STOCHd_14_3_3',
                              'WILLR_3', 'OBV', 'MACD_12_26_9', 'BBL_3_2.0',
                              'BBM_3_2.0', 'BBU_3_2.0', 'BBB_3_2.0',
                              'BBP_3_2.0', 'min_price_3', 'max_price_3',
                              'mid_price', 'tema_8']

        self.rename_feature = {0: "open", 1: "high", 2: "low", 3: "close", 4: "volume",
                               5: "NATR_3", 6: "RSI_3", 7: "ADX_3", 8: "CCI_3_0.015",
                               9: "ROC_3", 10: "STOCHk_14_3_3", 11: "STOCHd_14_3_3",
                               12: "WILLR_3", 13: "OBV", 14: "MACD_12_26_9",
                               15: "BBL_3_2.0", 16: "BBM_3_2.0", 17: "BBU_3_2.0", 18: "BBB_3_2.0",
                               19: "BBP_3_2.0", 20: "min_price_3", 21: "max_price_3",
                               22: "mid_price", 23: "tema_8"}
        self.path = path
        self.training_for_test = training_for_test

    def training(self, specific_date=None):

        # get the data from database
        data = get_stock_data(self.symbol)
        data = pd.DataFrame(s.to_dict() for s in data)

        process_data_service = ProcessDataService(data)

        data = process_data_service.process_NYSE_stock_data()

        # check the file in path exist or not
        # if exist, read the file
        # if not, create the file
        from sklearn.exceptions import ConvergenceWarning, DataConversionWarning
        # Filter out DataConversionWarning
        warnings.filterwarnings("ignore", category=DataConversionWarning)
        # Filter out ConvergenceWarning
        warnings.filterwarnings("ignore", category=ConvergenceWarning)

        if self.training_for_test:
            self.training_model_from_2013_to_2022(data)
            return

        if specific_date is not None:
            self.training_model_before_inputting_date(data, specific_date)
            return

        if self.check_file_existence():
            os.remove(self.path)
            self.training_model_and_save_checkpoint(data)
        else:
            self.training_model_and_save_checkpoint(data)

    def training_model_and_save_checkpoint(self, data):
        print("Training model")
        # split the data into input and output for training
        train_X, y = self.split_and_scale_data(data)

        # Create the model
        svr = SVR(C=1, kernel='linear', max_iter=5000)
        svr_model = svr.fit(train_X, y)

        # Save the model
        joblib.dump(svr_model, self.path)

    def split_and_scale_data(self, data):
        df = data.loc['2013-01-01':]
        main_dataset = df[self.input_feature]
        main_dataset = main_dataset.dropna()

        # create the next date column
        main_dataset['next_date'] = main_dataset['close'].shift(-1)
        main_dataset = main_dataset.dropna()

        # split the data into input and output for training

        # input
        X = main_dataset.drop(['next_date'], axis=1)

        # output
        y = main_dataset[['next_date']]

        # Scale input dataset
        scaler = StandardScaler()
        X = scaler.fit_transform(X)

        # Create the dataframe
        train_X = pd.DataFrame(X)
        train_X.rename(columns=self.rename_feature, inplace=True)
        train_X.index = main_dataset.index

        return train_X, y

    def check_file_existence(self):
        return os.path.exists(self.path)

    def training_model_before_inputting_date(self, data, date):
        print("Training model")
        # split the data into input and output for training
        train_X, y = self.split_and_scale_data(data)

        train_X = train_X[:date]
        y = y[:date]

        # Create the model
        svr = SVR(C=1, kernel='linear', max_iter=5000)
        svr_model = svr.fit(train_X, y)

        # Save the model
        joblib.dump(svr_model, self.path)

    def training_model_from_2013_to_2022(self, data):
        print("Training model")
        # split the data into input and output for training
        train_x, y = self.split_and_scale_data(data)

        train_x = train_x['2013-01-01': '2022-12-31']
        y = y['2013-01-01': '2022-12-31']

        # Create the model
        svr = SVR(C=1, kernel='linear', max_iter=5000)
        svr_model = svr.fit(train_x, y)

        # Save the model
        joblib.dump(svr_model, self.path)


