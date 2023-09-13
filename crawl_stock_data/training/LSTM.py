import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import random

from sklearn.preprocessing import StandardScaler
from torch.optim.lr_scheduler import StepLR
import torch
from torch.utils.data import DataLoader, Dataset

from crawl_stock_data.dao.stock_data_dao import get_stock_data
from crawl_stock_data.service.process_data_service import ProcessDataService


class TimeSeriesDataset(Dataset):
    def __init__(self, X, y, sequence_length=5):
        self.X = torch.tensor(X).float()
        self.y = torch.tensor(y).float()
        self.sequence_length = sequence_length

    def __len__(self):
        return len(self.X)

    def __getitem__(self, i):

        if i >= self.sequence_length - 1:
            i_start = i - self.sequence_length + 1
            x = self.X[i_start:(i + 1), :]
        elif self.sequence_length == 1:
            return self.X[i], self.y[i]
        else:
            padding = self.X[0].repeat(self.sequence_length - i - 1, 1)
            x = self.X[0:(i + 1), :]
            # print(padding.shape, x.shape)
            x = torch.cat((padding, x), 0)
            # x = self.X[0:i, :]
            # print(x.shape,padding.shape)

        return x, self.y[i]


class LSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_stacked_layers):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_stacked_layers = num_stacked_layers

        self.lstm = nn.LSTM(input_size, hidden_size, num_stacked_layers, batch_first=True)

        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x, device):
        batch_size = x.size(0)
        h0 = torch.zeros(self.num_stacked_layers, batch_size, self.hidden_size).to(device)
        c0 = torch.zeros(self.num_stacked_layers, batch_size, self.hidden_size).to(device)

        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out


class LSTMModel:
    def __init__(self, symbol, path):
        self.learning_rate = None
        random.seed(0)
        torch.manual_seed(0)
        self.device = 'cpu'
        self.batch_size = 64
        self.sequence_length = 5
        self.losses = []
        self.val = []
        self.optimizer = None
        self.scheduler = None
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
        self.epochs = 2000
        self.learning_rate = 0.01
        self.loss_fn = nn.MSELoss()
        self.model = LSTM(23, 64, 2)
        self.model.to(self.device)

        data = get_stock_data(self.symbol)
        data = pd.DataFrame(s.to_dict() for s in data)
        process_data_service = ProcessDataService(data)
        self.data = process_data_service.process_NYSE_stock_data()

    def train_loop(self, dataloader, model, loss_fn, optimizer):
        size = len(dataloader.dataset)
        # Set the model to training mode - important for batch normalization and dropout layers
        # Unnecessary in this situation but added for best practices
        model.train()
        train_loss = 0
        num_batches = len(dataloader)

        for batch, (X, y) in enumerate(dataloader):
            # Compute prediction and loss
            pred = model(X)
            loss = loss_fn(pred, y)
            train_loss += loss.item()
            # Backpropagation
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()

            if batch % 100 == 0:
                loss, current = loss.item(), (batch + 1) * len(X)
                # print(f"loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")

        print(f"train Error: Avg loss: {train_loss / num_batches:>8f}")
        self.losses.append((train_loss / num_batches))

    def test_loop(self, dataloader, model, loss_fn):
        # Set the model to evaluation mode - important for batch normalization and dropout layers
        # Unnecessary in this situation but added for best practices
        model.eval()
        size = len(dataloader.dataset)
        num_batches = len(dataloader)
        test_loss, correct = 0, 0

        # Evaluating the model with torch.no_grad() ensures that no gradients are computed during test mode
        # also serves to reduce unnecessary gradient computations and memory usage for tensors with requires_grad=True
        with torch.no_grad():
            for X, y in dataloader:
                pred = model(X)
                test_loss += loss_fn(pred, y).item()
                correct += (pred.argmax(1) == y).type(torch.float).sum().item()

        test_loss /= num_batches
        correct /= size

        self.val.append(test_loss)

        self.scheduler.step()
        # curr_lr = optimizer.param_groups[0]['lr']

        print(f"Test Error: Avg loss: {test_loss:>8f}  \n")

    def train(self):
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)
        self.scheduler = StepLR(self.optimizer, step_size=200, gamma=0.1)

        train_X, train_Y = self.split_and_scale_data(self.data)

        train_dataset = TimeSeriesDataset(train_X, train_Y, self.sequence_length)
        train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)

        for t in range(self.epochs):
            if self.epochs % 100 == 0:
                print(f"Epoch {t + 1}\n-------------------------------")

            self.train_loop(train_loader, self.model, self.loss_fn, self.optimizer)
        print("Done!")

        self.losses = []
        torch.save(self.model, self.path)

    def split_and_scale_data(self, data):
        # split the data into train and test
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
        scaler.fit(X)
        X = scaler.transform(X)

        # Create the dataframe
        train_X = pd.DataFrame(X)
        train_X.rename(columns=self.rename_feature, inplace=True)
        train_X.index = main_dataset.index

        return train_X, y
