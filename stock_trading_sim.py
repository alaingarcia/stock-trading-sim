import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from itertools import repeat
import math
import ta

# dataset_dict holds all the datasets
dataset_dict = {}

# current_price_dict holds all the current prices
current_price_dict = {}

# dataset object used to hold technical analysis data for a certain stock
class dataset():
  def __init__(self, df):
    self.close = df['Close']
    self.high = df['High']
    self.low = df['Low']
    self.df = self.addTechnicalAnalysisIndicators(df)

  def addTechnicalAnalysisIndicators(self, df):
    ''' #bollinger indicators (1 or 0)
    df['bb_high_indicator'] = ta.bollinger_hband_indicator(close)
    df['bb_low_indicator'] = ta.bollinger_lband_indicator(close)'''
    
    close, high, low = self.close, self.high, self.low
    # rsi with time period (for 5 min intervals, n=12 -> 1 hour)
    df['rsi'] = ta.rsi(close, n=14)
    df['upperboll'] = ta.bollinger_hband(close, ndev=2, fillna=False)
    df['lowerboll'] = ta.bollinger_lband(close, ndev=2, fillna=False)
    df['lowerkelt'] = ta.keltner_channel_lband(high, low, close, n=10, fillna=False)
    df['upperkelt'] = ta.keltner_channel_hband(high, low, close, n=10, fillna=False)
    df['sma14'] = ta.bollinger_mavg(close, n=14)
    df['sma30'] = ta.bollinger_mavg(close, n=30)
    df['sma50'] = ta.bollinger_mavg(close, n=50)
    df['sma200'] = ta.bollinger_mavg(close, n=200)
    return df

# account object used to keep track of cash, value, risk, and stocks held while 
# buying/selling multiple stocks
class account():
  # stock object used to maintain stocks
  class stock():
    def __init__(self, price_bought, time_bought):
      self.price_bought = price_bought
      self.time_bought = time_bought

  def __init__(self, cash, risk, stock_list):
      self.cash = cash
      self.starting_cash = cash
      self.risk = risk
      self.buy_orders = 0
      self.sell_orders = 0
      # portfolio is a dictionary that has a list for each stock ticker
      self.portfolio = {}
      self.stock_list = stock_list
      for ticker in self.stock_list:
          self.portfolio[ticker] = []
      self.portfolio_value = 0
      self.account_value = cash
  
  def initializeDatasets(self, file_suffix, data_folder='data/'):
    for ticker in self.stock_list:
        df = pd.read_csv(data_folder + ticker + file_suffix, sep=',')
        dataset_dict[ticker] = dataset(df)

  # recalculates the portfolio_value based on current prices
  def portfolioValue(self, current_price_dict):
    portfolio_value = 0
    for ticker in current_price_dict:
      portfolio_value += len(self.portfolio[ticker]) * current_price_dict[ticker]
    return portfolio_value

  def accountValue(self, current_price_dict):
    self.portfolio_value = self.portfolioValue(current_price_dict)
    account_value = self.cash + self.portfolio_value
    return account_value
          
  def buy(self, ticker, current_stock_price, amount_to_buy, time):
    # first, check if the order is possible
    if (self.cash < amount_to_buy * current_stock_price):
      print('Error: Attempted to buy stocks without enough cash.')
      return
    # inserts a stock object for the amount of stock specified
    for _ in range(amount_to_buy):
      self.portfolio[ticker].insert(0, self.stock(current_stock_price, time))
      self.buy_orders += 1
    self.cash -= amount_to_buy * current_stock_price
    self.cash = round(self.cash, 2)
    print("{} - BUY {} {} @ ${} ea, cash: {}, account_value: {}".format(time, amount_to_buy, ticker, current_stock_price, self.cash, self.account_value))

  def sell(self, ticker, current_stock_price, amount_to_sell, time):
    # first, check if the order is possible
    current_stock_amount = len(self.portfolio[ticker])
    if amount_to_sell > current_stock_amount:
      print('Error: Attempted to sell more stocks than are currently in the portfolio.')
      return
    # sell the amount required
    while len(self.portfolio[ticker]) > current_stock_amount - amount_to_sell:
      self.portfolio[ticker].pop(0)
      self.cash += current_stock_price
      self.sell_orders += 1
    self.cash = round(self.cash, 2)
    print("{} - SELL {} {} @ ${} ea, cash: {}, account_value: {}".format(time, amount_to_sell, ticker, current_stock_price, self.cash, self.account_value))
    
  def amount_to_buy(self, current_stock_price, account_value, equity_percent):
    cash_used_to_buy = equity_percent * account_value
    return math.floor(cash_used_to_buy/current_stock_price)

  # trades (buy/sell) at current price using available cash
  def trade(self, dataset_dict=dataset_dict):
    
    # only works if all the datasets are consistent with each other
    # same time periods, same length of time, etc.

    # gets the amount of rows in dataset, run potential trades
    for i in range(len(dataset_dict[self.stock_list[0]].df.index)):

      # update current price dict for accurate account value
      for ticker in dataset_dict:
        current_price_dict[ticker] = dataset_dict[ticker].close.iloc[i]
      
      self.account_value = self.accountValue(current_price_dict)

      for ticker in dataset_dict:
        # shorthand
        df = dataset_dict[ticker].df
        close = dataset_dict[ticker].close

        # calculate necessary technical analysis indicators for each stock/ticker
        if i < len(df['rsi']) - 1:
          rsi = round(df['rsi'].iloc[i], 2)
          rsi_next = round(df['rsi'].iloc[i+1], 2)
          rsi_prev = round(df['rsi'].iloc[i-1], 2)
          sma1 = round(df['sma14'].iloc[i], 2)
          sma2 = round(df['sma30'].iloc[i], 2)
          sma3 = round(df['sma50'].iloc[i], 2)
          sma4 = round(df['sma200'].iloc[i], 2)
          lowerkelt = round(df['lowerkelt'].iloc[i], 2)
          upperkelt = round(df['upperkelt'].iloc[i], 2)
          lowerboll = round(df['lowerboll'].iloc[i], 2)
          upperboll = round(df['upperboll'].iloc[i], 2)

          current_stock_price = close.iloc[i]
          prev_stock_price = close.iloc[i-1]
          time = df['Local time'].iloc[i]

          # ------ TRADING RULES ------

          # Buys
          if ((rsi < 50) & (sma1>sma2)) or ((rsi > 50) & (sma3>sma4)):
            self.buy(ticker, current_stock_price, amount_to_buy=1, time=time)

          # Sells
          elif (((rsi > 75) & (sma1<sma2)) or ((rsi < 75) & (sma3<sma4))) & (len(self.portfolio[ticker]) > 0):
            self.sell(ticker, current_stock_price, amount_to_sell=1, time=time)

  # Calculates ROI based on technical analysis trading and compares it to buy and hold ROI
  def print_results(self, dataset_dict):
    buy_hold_start, buy_hold_end = 0, 0

    # update current price dict for accurate account/portfolio value
    for ticker in dataset_dict:
      current_price_dict[ticker] = dataset_dict[ticker].close.iloc[-1]
      buy_hold_start += dataset_dict[ticker].close.iloc[0]
      buy_hold_end += dataset_dict[ticker].close.iloc[-1]
    
    self.account_value = self.accountValue(current_price_dict)

    print('--------Technical Analysis--------')
    ROI = ((self.portfolio_value + self.cash - self.starting_cash) / self.starting_cash) * 100
    # total value = money + portfolio value
    print('Portfolio Value: {}'.format(round(self.portfolio_value,2)))
    print('Cash Value: {}'.format(round(self.cash,2)))
    print('Account Value: {}'.format(round(self.portfolio_value+self.cash,2)))
    print('Buy orders: {}, Sell orders: {}'.format(self.buy_orders, self.sell_orders))
    print('Return on Investment: {}%'.format(round(ROI,4)))

    print('--------Buy and Hold--------')
    ROI = ((buy_hold_end - buy_hold_start) / buy_hold_start) * 100
    print('Return on Investment: {}%'.format(round(ROI, 4)))