import pickle
import pandas as pd
import pandas_ta as ta
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import crawl_stock_data.dao as dao
import numpy as np
from sklearn.metrics import mean_squared_error
import joblib
import torch

CustomStrategy = ta.Strategy(
    name="Customize technical indicator",
    description="adding TI",
    ta=[
        {"kind": "natr", 'length': 3},
        {"kind": "rsi", 'length': 3},
        {"kind": "adx", 'length': 3},
        {"kind": "cci", 'length': 3},
        {"kind": "roc", 'length': 3},
        {"kind": "stoch", 'length': 3},
        {"kind": "willr", 'length': 3},
        {"kind": "obv"},
        {"kind": "macd"},
        {"kind": "bbands", 'length': 3},
    ]
)


def calculate_mape(y_true, y_pred):
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100


def calculate_rmse(y_true, y_pred):
    return np.sqrt(mean_squared_error(y_true, y_pred))


def create_tema(stock: pd.DataFrame, MA_period: int) -> pd.Series:
    ema1 = ta.ema(stock['close'], length=MA_period)

    # Calculate the second EMA
    ema2 = ta.ema(ema1, length=MA_period)

    # Calculate the third EMA
    ema3 = ta.ema(ema2, length=MA_period)

    # Calculate TEMA
    tema = 3 * (ema1 - ema2) + ema3
    # stock[f'tema_{MA_period}'] = tema
    return tema


def create_min_max_mid_price(stock: pd.DataFrame, period: int):
    stock[f'min_price_{period}'] = stock['low'].rolling(window=period).min()
    stock[f'max_price_{period}'] = stock['high'].rolling(window=period).max()
    stock['mid_price'] = (stock['high'] + stock['low']) / 2


input_feature = ['low', 'high', 'open', 'close', 'volume',
                 'NATR_3', 'RSI_3', 'ADX_3', 'CCI_3_0.015',
                 'ROC_3', 'STOCHk_14_3_3', 'STOCHd_14_3_3',
                 'WILLR_3', 'OBV', 'MACD_12_26_9', 'BBL_3_2.0',
                 'BBM_3_2.0', 'BBU_3_2.0', 'BBB_3_2.0',
                 'BBP_3_2.0', 'min_price_3', 'max_price_3',
                 'mid_price', 'tema_8']

rename_feature = {0: "low", 1: "high", 2: "open", 3: "close", 4: "volume",
                  5: "NATR_3", 6: "RSI_3", 7: "ADX_3", 8: "CCI_3_0.015",
                  9: "ROC_3", 10: "STOCHk_14_3_3", 11: "STOCHd_14_3_3",
                  12: "WILLR_3", 13: "OBV", 14: "MACD_12_26_9",
                  15: "BBL_3_2.0", 16: "BBM_3_2.0", 17: "BBU_3_2.0", 18: "BBB_3_2.0",
                  19: "BBP_3_2.0", 20: "min_price_3", 21: "max_price_3",
                  22: "mid_price", 23: "tema_8"}

def set_index(data):
    df = pd.DataFrame.from_records([s.to_dict() for s in data])

    df.rename(columns={'date': 'Date'}, inplace=True)
    df['Date'] = pd.to_datetime(df['Date'], utc=True, format="ISO8601")
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    df.set_index('Date', inplace=True)
    df = df.sort_index(ascending=True)

    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)

    return df

def process_data(data):
    # process data to get the historical data for the last 5 years
    # make sure it has the same format as the data we used to train the model
    # it has tema_2 column
    # it has CustomStrategy columns without null values (use df.ta.strategy(CustomStrategy))
    # it has min_price_3, max_price_3, mid_price columns

    df = set_index(data)

    # create tema_2 column
    df['tema_8'] = create_tema(df, 8)

    # create CustomStrategy columns
    df.ta.strategy(CustomStrategy)
    df = df.drop(columns=['MACDh_12_26_9', 'MACDs_12_26_9', 'DMP_3', 'DMN_3'])

    # create min_price_3, max_price_3, mid_price columns
    create_min_max_mid_price(df, 3)

    df.dropna(inplace=True)

    return df

def scale_data(symbol, data, is_having_next_date = True):

    step = -1
    temp_df = data.copy()
    temp_df["Next date"] = temp_df['close'].shift(step)
    temp_df.dropna(inplace=True)

    data = temp_df.copy()

    # Fix scale of trainning data

    if symbol == 'AAPL':
        data = data[:'2020-12-31']
    else:
        data = data[:'2022-12-31']

    # scale data
    X = data[input_feature]
    X = X.set_index(data.index)

    scaler_input = StandardScaler()
    scaler_input_fit = scaler_input.fit(X)
    scaler_input = scaler_input_fit.transform(X)

    # create a scaler for the output
    Y = data[['Next date']]
    scaler_output = StandardScaler()
    scaler_output_fit = scaler_output.fit(Y)
    Y = scaler_output_fit.transform(Y)

    data_for_validation_actual = pd.DataFrame(Y)
    data_for_validation_actual = data_for_validation_actual.rename(columns={0: "Actual"})
    data_for_validation_actual = data_for_validation_actual.set_index(data.index)

    data_for_validation = pd.DataFrame(scaler_input)
    data_for_validation = data_for_validation.rename(columns=rename_feature)
    data_for_validation = data_for_validation.set_index(X.index)

    if is_having_next_date:
        return data_for_validation, data_for_validation_actual, scaler_output_fit
    else:
        return data_for_validation, scaler_output_fit
def predict_stock_by_SARIMAX_model_only_next_date(symbol):
    path_to_file = ('/mnt/learning/last_project/app/server/stock_server/crawl_stock_data/'
                    'training/checkpoint/sarimax/model_AAPL_with_tema_8_v2.pkl')
    with open(path_to_file, 'rb') as file:
        model = pickle.load(file)

    data = dao.get_stock_data_by_date(symbol, "2013-01-01", "2023-12-31")

    # process data
    data = process_data(data)

    # predict the stock value
    # data = split_data(data, 3)
    # scale data
    data_for_validation, scaler_output_fit = scale_data(symbol, data, False)

    data_for_validation = data_for_validation.tail(1)

    # predict the stock value
    prediction = model.forecast(len(data_for_validation), exog= data_for_validation)
    prediction = pd.DataFrame(prediction)
    prediction = prediction.rename(columns={0: "predicted_mean"})

    # inverse the scale
    prediction['predicted_mean'] = scaler_output_fit.inverse_transform(prediction[['predicted_mean']])

    # get the result
    # result = data_for_validation[['Predicted']]

    return prediction[['predicted_mean']].values[0][0]

def predict_stock_by_SARIMAX_model(symbol, the_number_of_date):
    ##using model_fit from a file pkl to predict the stock value
    # load the model from disk

    path_to_file = '/mnt/learning/last_project/app/server/stock_server/crawl_stock_data/training/checkpoint/sarimax/model_AAPL_with_tema_8_v2.pkl'
    with open(path_to_file, 'rb') as file:
        model = pickle.load(file)

    data = dao.get_stock_data_by_date(symbol, "2015-01-01", "2023-12-31")

    # process data
    data = process_data(data)

    # predict the stock value
    # data = split_data(data, the_number_of_date)

    # scale data
    data_for_validation, data_for_validation_actual, scaler_output_fit = scale_data(data)

    # predict
    prediction = model.forecast(the_number_of_date, exog=data_for_validation)
    # scale back
    prediction = pd.DataFrame(prediction)
    prediction.reset_index(drop=True, inplace=True)
    prediction = prediction.set_index(data_for_validation_actual.index)
    prediction = prediction.rename(columns={0: "predicted_mean"})
    prediction["predicted_mean"] = scaler_output_fit.inverse_transform(prediction[["predicted_mean"]])
    prediction["Actual"] = scaler_output_fit.inverse_transform(data_for_validation_actual[["Actual"]])

    # calculate error
    rmse = calculate_rmse(prediction["Actual"], prediction["predicted_mean"])
    print("The root mean squared error is ", rmse)
    mape = calculate_mape(prediction["Actual"], prediction["predicted_mean"])
    print("The mean absolute percentage error is ", mape)

    return prediction, rmse, mape


def predicted_stock_by_SVM_model(symbol, the_number_of_date):
    svm_model = joblib.load(
        '/mnt/learning/last_project/app/server/stock_server/crawl_stock_data/training/checkpoint/svm/apple/tema_8.sav')

    data = dao.get_stock_data_by_date(symbol, "2015-01-01", "2023-12-31")

    # process data
    data = process_data(data)

    # predict the stock value
    # data = split_data(data, the_number_of_date)

    # scale data

    data_for_validation, data_for_validation_actual, scaler_output_fit = scale_data(data)

    # predict
    prediction = svm_model.predict(data_for_validation)
    # scale back
    prediction = pd.DataFrame(prediction)
    prediction.reset_index(drop=True, inplace=True)
    prediction = prediction.set_index(data_for_validation_actual.index)
    prediction.rename(columns={0: "predicted_mean"}, inplace=True)
    prediction["predicted_mean"] = scaler_output_fit.inverse_transform(prediction[["predicted_mean"]])
    prediction["Actual"] = scaler_output_fit.inverse_transform(data_for_validation_actual[["Actual"]])

    # calculate error
    rmse = calculate_rmse(prediction["Actual"], prediction["predicted_mean"])
    print("The root mean squared error is ", rmse)
    mape = calculate_mape(prediction["Actual"], prediction["predicted_mean"])
    print("The mean absolute percentage error is ", mape)

    return prediction, rmse, mape


def predicted_stock_by_LSTM_model(symbol, the_number_of_date):
    model = torch.load(
        '/mnt/learning/last_project/app/server/stock_server/crawl_stock_data/training/checkpoint/lstm/amd/lstm_tema_8.pth',
        map_location=torch.device('cpu'))

    data = dao.get_stock_data_by_date(symbol, "2015-01-01", "2023-12-31")

    # process data
    data = process_data(data)

    # predict the stock value
    # data = split_data(data, the_number_of_date)

    # scale data
    data_for_validation, data_for_validation_actual, scaler_output_fit = scale_data(data)

    # process data
    data_for_validation = data_for_validation.to_numpy()
    data_for_validation = data_for_validation.reshape(1.5, -1)
    X = torch.from_numpy(data_for_validation).float()

    # predict
    model.eval()
    with torch.no_grad():
        prediction = model(X)
    # scale back
    prediction = pd.DataFrame(prediction)
    prediction.reset_index(drop=True, inplace=True)
    prediction = prediction.set_index(data_for_validation_actual.index)
    prediction.rename(columns={0: "predicted_mean"}, inplace=True)
    prediction["predicted_mean"] = scaler_output_fit.inverse_transform(prediction[["predicted_mean"]])
    prediction["Actual"] = scaler_output_fit.inverse_transform(data_for_validation_actual[["Actual"]])

    # calculate error
    rmse = calculate_rmse(prediction["Actual"], prediction["predicted_mean"])
    print("The root mean squared error is ", rmse)
    mape = calculate_mape(prediction["Actual"], prediction["predicted_mean"])
    print("The mean absolute percentage error is ", mape)

    return prediction, rmse, mape
