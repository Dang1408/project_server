import pandas as pd
import pandas_ta as ta

from crawl_stock_data.dao import get_stock_data

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


# write the function to create the column tema of the dataframe
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


def create_min_max_mid_price(stock: pd.DataFrame, period:int ) -> pd.Series:
    stock[f'min_price_{period}'] = stock['low'].rolling(window=period).min()
    stock[f'max_price_{period}'] = stock['high'].rolling(window=period).max()
    stock['mid_price'] = (stock['high'] + stock['low']) / 2


def calculate_MA_smoothness(ma:pd.Series):
    diff_i = ma -ma.shift(1)
    diff_i = diff_i.dropna()
    smooth =(diff_i-diff_i.shift(1)).dropna()
    smooth = smooth.abs().mean()
    return smooth


def calculate_MA_lag(stock: pd.DataFrame, ma:pd.Series):
    lag = (stock['Close']-ma).dropna()
    lag= lag.abs().mean()
    return lag


def process_data(symbol):
    # get data from database and convert to dataframe

    data = get_stock_data(symbol)

    temp_df = pd.DataFrame.from_records([s.to_dict() for s in data])
    temp_df['date'] = pd.to_datetime(temp_df['date'], utc=True, format="ISO8601")
    temp_df["date"] = temp_df["date"].dt.strftime("%Y-%m-%d")

    df = temp_df.copy()
    df.rename(columns={'date': 'Date'}, inplace=True)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    df.sort_index(inplace=True)

    # convert the type of the columns to float
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)

    # create the column of the technical indicator
    df.ta.strategy(CustomStrategy)

    # create the column of the min, max, mid price
    create_min_max_mid_price(df, 3)

    # create the column of the tema 2, 8, 100
    df['tema_2'] = create_tema(df, 2)
    df['tema_8'] = create_tema(df, 8)
    df['tema_100'] = create_tema(df, 100)

    # drop the nan value
    df.dropna(inplace=True)
    df = df.drop(columns=['MACDh_12_26_9', 'MACDs_12_26_9', 'DMP_3', 'DMN_3'])
    print("The length of the data after deleting null is: ", len(df))

    return df
