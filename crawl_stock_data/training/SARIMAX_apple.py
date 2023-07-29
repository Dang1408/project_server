import StandardScaler as StandardScaler
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from .process_data import process_data
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_squared_error

#turn off warning
import warnings

def calculate_mape(y_true, y_pred):
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100


def calculate_rmse(y_true, y_pred):
    return np.sqrt(mean_squared_error(y_true, y_pred))


def training_model():
    warnings.filterwarnings("ignore")
    symbol = 'AAPL'
    stock = process_data(symbol)

    # split data into train and training set
    df = stock.copy().loc['2013-01-01':]
    df.dropna(inplace=True)

    steps = -1
    main_dataset = df.copy()
    main_dataset['Next date'] = main_dataset['close'].shift(steps)
    main_dataset.dropna(inplace=True)

    # split data into train and training set
    X, Y, df_for_validation, df_for_validation_actual = handle_data(main_dataset)

    # Get only tema_2 from train_X, test_X

    train_X_with_tema_2 = X.drop(['tema_8', 'tema_100'], axis=1)
    train_X_with_tema_8 = X.drop(['tema_2', 'tema_100'], axis=1)
    train_X_with_tema_100 = X.drop(['tema_2', 'tema_8'], axis=1)
    train_X_without_tema = X.drop(['tema_2', 'tema_8', 'tema_100'], axis=1)

    # Get only tema_2 from df_for_validation
    df_for_validation_with_tema_2 = df_for_validation.drop(['tema_8', 'tema_100'], axis=1)
    df_for_validation_with_tema_8 = df_for_validation.drop(['tema_2', 'tema_100'], axis=1)
    df_for_validation_with_tema_100 = df_for_validation.drop(['tema_2', 'tema_8'], axis=1)
    df_for_validation_without_tema = df_for_validation.drop(['tema_2', 'tema_8', 'tema_100'], axis=1)

    # Train model and return mape and rmse
    train_model_and_calculate_mape_and_rmse(Y, train_X_with_tema_2, df_for_validation_actual,
                                            df_for_validation_with_tema_2)
    train_model_and_calculate_mape_and_rmse(Y, train_X_with_tema_8, df_for_validation_actual,
                                            df_for_validation_with_tema_8)
    train_model_and_calculate_mape_and_rmse(Y, train_X_with_tema_100, df_for_validation_actual,
                                            df_for_validation_with_tema_100)
    train_model_and_calculate_mape_and_rmse(Y, train_X_without_tema, df_for_validation_actual,
                                            df_for_validation_without_tema)


def train_model_and_calculate_mape_and_rmse(train_Y, train_X, df_for_validation_actual, df_for_validation):
    order = (2, 1, 0)
    seasonal_order = (2, 1, 0, 12)
    # train the model
    model = SARIMAX(endog=train_Y, exog=train_X, order=order, seasonal_order=seasonal_order,
                    enforce_invertibility=False, enforce_stationarity=True)
    model_fit = model.fit(maxiter=200, method='powell', disp=False, full_output=False)

    # save the checkpoint with string format name
    # at /mnt/learning/last_project/app/server/stock_server/crawl_stock_data/training/checkpoint
    model_fit.save(f"tema_{get_the_tema(train_X)}_apple.pkl")

    forecast = model_fit.forecast(steps=len(df_for_validation), exog=df_for_validation)
    forecast_apple_with_tema_2 = pd.DataFrame(forecast)
    forecast_apple_with_tema_2.reset_index(drop=True, inplace=True)
    forecast_apple_with_tema_2.index = df_for_validation_actual.index
    forecast_apple_with_tema_2["Actual"] = df_for_validation_actual

    error = calculate_rmse(forecast_apple_with_tema_2["predicted_mean"], forecast_apple_with_tema_2["Actual"])
    print("The root mean squared error of tema {} is {}.".format(get_the_tema(train_X), error))

    # calculate the mean absolute percentage error
    mape = calculate_mape(forecast_apple_with_tema_2["Actual"], forecast_apple_with_tema_2["predicted_mean"])
    print("The mean absolute percentage error of tema {} is {}.".format(get_the_tema(train_X), mape))

def handle_data(main_dataset):
    # scale the data
    scaler_input = StandardScaler()

    X = main_dataset[['low', 'high', 'open', 'close', 'volume',
                      'NATR_3', 'RSI_3', 'ADX_3', 'CCI_3_0.015',
                      'ROC_3', 'STOCHk_14_3_3', 'STOCHd_14_3_3',
                      'WILLR_3', 'OBV', 'MACD_12_26_9', 'BBL_3_2.0',
                      'BBM_3_2.0', 'BBU_3_2.0', 'BBB_3_2.0',
                      'BBP_3_2.0', 'min_price_3', 'max_price_3',
                      'mid_price', 'tema_2', 'tema_100', 'tema_8', "adj_close"]]

    scaler_input_fit = scaler_input.fit(X)
    scaled_data = scaler_input_fit.transform(X)
    scaled_data = pd.DataFrame(scaled_data)
    X = scaled_data
    # scale the target
    scaled_data = pd.DataFrame(scaled_data)
    scaler_output = StandardScaler()
    scaler_output_fit = scaler_output.fit(main_dataset[['Next date']])
    scaled_target = scaler_output_fit.transform(main_dataset[['Next date']])
    scaled_target = pd.DataFrame(scaled_target)
    Y = scaled_target

    # rename the columns
    X.rename(columns={0: 'open', 1: 'high', 2: 'low', 3: 'close', 4: 'volume', 5: 'NATR_3', 6: 'RSI_3', 7: 'ADX_3',
                      8: 'CCI_3_.015',
                      9: 'ROC_3', 10: 'STOCHk_14_3_3', 11: 'STOCHd_14_3_3', 12: 'WILLR_3', 13: 'OBV',
                      14: 'MACD_12_26_9',
                      15: 'BBL_3_2.0', 16: 'BBM_3_2.0', 17: 'BBU_3_2.0', 18: 'BBB_3_2.0', 19: 'BBP_3_2.0',
                      20: 'min_price_3',
                      21: 'max_price_3', 22: 'mid_price', 23: 'tema_2', 24: 'tema_100', 25: 'tema_8', 26: 'adj_close'},
             inplace=True)

    X.index = main_dataset.index

    Y.rename(columns={0: 'Next date'}, inplace=True)
    Y.index = main_dataset.index
    Y.head(3)

    # split the data into train and validation
    df_for_validation = X.loc['2023-01-01':'2023-06-27']

    df_for_validation_actual = Y.loc['2023-01-01':'2023-06-27']

    # Get the train data from X and Y between 2013-01-01 and 2023-01-01
    X = X.loc['2013-01-01':'2023-01-01']
    Y = Y.loc['2013-01-01':'2023-01-01']

    return X, Y, df_for_validation, df_for_validation_actual

def get_the_tema(df):
    if 'tema_2' in df:
        return 2
    elif 'tema_8' in df:
        return 8
    elif 'tema_100' in df:
        return 100
    else:
        return 0
