import pandas as pd
import pandas_ta as ta


# Bring your packages onto the path

class ProcessDataService:

    def __init__(self, dataframe: pd.DataFrame | None):
        self.CustomStrategy = ta.Strategy(
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
        self.dataframe = dataframe

    # write the function to create the column tema of the dataframe
    @staticmethod
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

    @staticmethod
    def create_min_max_mid_price(stock: pd.DataFrame, period: int) -> pd.Series:
        stock[f'min_price_{period}'] = stock['low'].rolling(window=period).min()
        stock[f'max_price_{period}'] = stock['high'].rolling(window=period).max()
        stock['mid_price'] = (stock['high'] + stock['low']) / 2

    @staticmethod
    def calculate_MA_smoothness(ma: pd.Series):
        diff_i = ma - ma.shift(1)
        diff_i = diff_i.dropna()
        smooth = (diff_i - diff_i.shift(1)).dropna()
        smooth = smooth.abs().mean()
        return smooth

    @staticmethod
    def calculate_MA_lag(stock: pd.DataFrame, ma: pd.Series):
        lag = (stock['Close'] - ma).dropna()
        lag = lag.abs().mean()
        return lag

    def rename_column_and_set_type(self, df: pd.DataFrame | None):

        if df is None:
            df = self.dataframe

        if 'date' in df.columns:
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

    def process_NYSE_stock_data(self):
        # get data from database and convert to dataframe

        temp_df = self.dataframe
        df = self.rename_column_and_set_type(temp_df)

        # create the column of the technical indicator
        df = self.add_technical_indicator(df)

        return df

    def add_technical_indicator(self, df):
        # create the column of the technical indicator
        df.ta.strategy(self.CustomStrategy)

        # create the column of the min, max, mid price
        self.create_min_max_mid_price(df, 3)

        # create the column of the tema 2, 8, 100
        df['tema_2'] = self.create_tema(df, 2)
        df['tema_8'] = self.create_tema(df, 8)
        df['tema_100'] = self.create_tema(df, 100)

        # drop the nan value
        df.dropna(inplace=True)
        df = df.drop(columns=['MACDh_12_26_9', 'MACDs_12_26_9', 'DMP_3', 'DMN_3'])

        return df

    def process_VNINDEX_stock_data(self, file):

        data = pd.read_csv(file)
        # get the file name
        stock_name = file.name.split('/')[-1].split('.')[0]

        data = data.rename(
            columns={'Ngày': 'Date', 'Mở': 'open',
                     'Cao': 'high', 'Thấp': 'low',
                     'Lần cuối': 'close', 'KL': 'volume'})

        if '% Thay đổi' in data.columns:
            data = data.drop(columns=['% Thay đổi'])

        data['Date'] = pd.to_datetime(data['Date'], format='%d/%m/%Y')
        data = data.set_index('Date')
        data = data.sort_index()
        main_df = data.copy()

        for i in range(len(main_df['volume'])):
            if 'K' in str(main_df['volume'][i]):
                main_df['volume'][i] = main_df['volume'][i].replace('K', '')
                main_df['volume'][i] = float(main_df['volume'][i]) * 1000
            elif 'M' in str(data['volume'][i]):
                main_df['volume'][i] = main_df['volume'][i].replace('M', '')
                main_df['volume'][i] = float(main_df['volume'][i]) * 1000000
            else:
                main_df['volume'][i] = float(main_df['volume'][i])

        main_df["volume"] = main_df["volume"].astype(int)
        main_df["close"] = main_df["close"].str.replace(',', '').astype(float)
        main_df["open"] = main_df["open"].str.replace(',', '').astype(float)
        main_df["high"] = main_df["high"].str.replace(',', '').astype(float)
        main_df["low"] = main_df["low"].str.replace(',', '').astype(float)

        # create the column of the technical indicator
        main_df = self.add_technical_indicator(main_df)

        # # save file to csv format into the media_url
        # main_df.to_csv(f'{MEDIA_ROOT}/stock_data/clean_{stock_name}.csv', index=True)

        return main_df, stock_name
