import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from itertools import repeat
import math
import ta

class dataset():
  def __init__(self, df):
    self.df = self.addTechnicalAnalysisIndicators(self.df)
    self.close = df['close']
    self.high = df['high']
    self.low = df['low']

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

class account():
  # stock object used to maintain stocks
  class stock():
    def __init__(self, price_bought):
      self.price_bought = price_bought

  def __init__(self, cash, risk, stock_list):
      self.cash = cash
      self.cash1 = cash
      self.risk = risk
      self.buy_orders = 0
      self.sell_orders = 0
      # portfolio is a dictionary that has a list for each stock ticker
      self.portfolio = {}
      for ticker in stock_list:
          self.portfolio[ticker] = []
      self.account_value = cash

  # recalculates the portfolio_value based on current prices
  def portfolioValue(self, current_price_dict):
    portfolio_value = 0
    for ticker in current_price_dict:
      portfolio_value += len(self.portfolio[ticker]) * current_price_dict[ticker]
    return portfolio_value

  def accountValue(self, current_price_dict):
    portfolio_value = self.portfolioValue(current_price_dict)
    account_value = self.cash + portfolio_value
    return account_value
          
  def buy(self, ticker, current_stock_price, amount_to_buy, time):
    # first, check if the order is possible
    if (self.cash < amount_to_buy * current_stock_price):
      print('Error: Attempted to buy stocks without enough cash.')
      return
    # inserts a stock object for the amount of stock specified
    for _ in range(amount_to_buy):
      self.portfolio[ticker].insert(0, self.stock(current_stock_price))
    self.cash -= amount_to_buy * current_stock_price
    print("{} - BUY @ ${}, cash: {}, av:{}, 1".format(time, current_stock_price, self.cash, self.account_value))

  def sell(self, ticker, current_stock_price, amount_to_sell):
    # first, check if the order is possible
    current_stock_amount = len(self.portfolio[ticker])
    if amount_to_sell > current_stock_amount:
      print('Error: Attempted to sell more stocks than are currently in the portfolio.')
      return
    # sell the amount required
    while len(self.portfolio[ticker]) > current_stock_amount - amount_to_sell:
      self.portfolio[ticker].pop(0)
      self.cash += current_stock_price
    
  def amount_to_buy(self, current_stock_price, account_value, equity_percent):
    cash_used_to_buy = equity_percent * account_value
    return math.floor(cash_used_to_buy/current_stock_price)

dataframes = {}
ticker_list = ['AAPL','V','MSFT','AMZN','FB','GOOG','JPM','UNH','BAC','MA']

suffix = '.USUSD_Candlestick_4_Hour_ASK_02.11.2017-31.07.2019.csv'

for ticker in ticker_list:
    df = pd.read_csv(ticker + suffix, sep=',')
    dataframes[ticker] = dataset(df)



def trade(dataframes, account, index):
  i = index
  for df in dataframes:
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
      time = df['timestamp'].iloc[i]
      portfolio_value = account.portfolioValue()
      account_value = portfolio_value + account.cash
      equity_05 = account.amount_to_buy(current_stock_price, account_value, 0.0005)
      equity_01 = account.amount_to_buy(current_stock_price, account_value, 0.0001)


      if ((account.cash - (equity_05*current_stock_price)) > (account.cash1*(1-account.risk))) & (rsi < 50) & (sma1>sma2):
        account.buy('AAPL', current_stock_price, equity_05, cash, account.portfolio)
        buy_orders += 1
        portfolio_value = len(portfolio) * current_stock_price
        account_value = portfolio_value + cash
        print("{} - BUY @ ${}, rsi: {}, cash: {}, av:{}, 1".format(time, current_stock_price, rsi, cash, account_value))

      elif ((account.cash - (equity_01*current_stock_price)) > (account.cash1*(1-account.risk))) & (rsi > 50) & (sma3>sma4):
        account.buy('AAPL', current_stock_price, equity_01, cash, portfolio)
        buy_orders += 1
        portfolio_value = len(portfolio) * current_stock_price
        account_value = portfolio_value + cash
        print("{} - BUY @ ${}, rsi: {}, cash: {}, av: {}, 2".format(time, current_stock_price, rsi, cash, account_value))

      elif (rsi > 75) & (sma1<sma2) & (len(portfolio) > 0):
        cash = sell('AAPL', current_stock_price, equity_05, cash, portfolio)
        sell_orders += 1
        portfolio_value = len(portfolio) * current_stock_price
        account_value = portfolio_value + cash
        print("{} - SELL @ ${}, rsi: {}, cash: {}, av: {}, 3".format(time, current_stock_price, rsi, cash, account_value))

      elif (rsi < 75) & (sma3<sma4) & (len(portfolio) > 0):
        cash = sell('AAPL', current_stock_price, equity_01, cash, portfolio)
        sell_orders += 1
        portfolio_value = len(portfolio) * current_stock_price
        account_value = portfolio_value + cash
        print("{} - SELL @ ${}, rsi: {}, cash: {}, av: {}, 4".format(time, current_stock_price, rsi, cash, account_value))


print('Technical Analysis\n----------------')

# portfolio value (monetary value of all stocks held in portfolio)
#portfolio vlaue is going to return incurrectly because we are unable to determine how many shares are in the portfolio; change
#how you add things to the portfolio and don't do it by multiplying the amount of cash
portfolio_value = len(portfolio)*(close.iloc[-1])
# money represents cash flows used to buy/sell stock
ROI = ((portfolio_value + cash - cash1) / cash1) * 100
# total value = money + portfolio value
print('Portfolio Value: {}'.format(round(portfolio_value,2)))
print('Cash Value: {}'.format(round(cash,2)))
print('Account Value: {}'.format(round(portfolio_value+cash,2)))
print('Return on Investment: {}%'.format(round(ROI,4)))
print('Buy orders: {}, Sell orders: {}'.format(buy_orders, sell_orders))


print('\n\nBuy and Hold\n----------------')
start = close.iloc[0]
end = close.iloc[-1]
ROI = ((end - start) / start) * 100
print('Total value: {}%'.format(round(ROI, 4)))
