import pandas as pd
from sklearn.preprocessing import StandardScaler
import joblib

from crawl_stock_data.service.process_data_service import ProcessDataService


class PredictStockService:

    def __init__(self, symbol, dataframe: pd.DataFrame):
        self.symbol = symbol
        self.dataframe = dataframe
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

    def scale_data(self, data: pd.DataFrame):

        # Fix scale of trainning data
        temp_data = data['2013-01-01':'2023-12-31']

        # scale data
        X = temp_data[self.input_feature]
        X = X.set_index(temp_data.index)

        scaler_input = StandardScaler()
        scaler_input_fit = scaler_input.fit(X)
        # scale main dataset
        scaler_input = scaler_input_fit.transform(X)

        data_for_validation = pd.DataFrame(scaler_input)
        data_for_validation = data_for_validation.rename(columns=self.rename_feature)
        data_for_validation = data_for_validation.set_index(temp_data.index)

        return data_for_validation

    def next_date_with_SVM_model(self):
        path_to_file = ('/mnt/learning/last_project/app/server/stock_server/crawl_stock_data/training/checkpoint/'
                        'online_learning_model/svm/SVM_{}_13-23.pkl'.format(self.symbol))

        svm_model = joblib.load(path_to_file)

        # process data
        processDataService = ProcessDataService(self.dataframe)
        data = processDataService.process_NYSE_stock_data()

        # scale data
        data_for_validation = self.scale_data(data)

        data_for_validation = data_for_validation.tail(1)
        # predict the stock value
        prediction = svm_model.predict(data_for_validation)
        prediction = pd.DataFrame(prediction)
        prediction = prediction.rename(columns={0: "predicted_mean"})

        return prediction[['predicted_mean']].values[0][0]
