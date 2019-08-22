import stock_trading_sim as st
import pandas as pd

if __name__ == '__main__':
    ticker_list = ['AAPL','V','MSFT','AMZN','FB','GOOG','JPM','UNH','BAC','MA']
    file_suffix = '.USUSD_Candlestick_4_Hour_ASK_30.01.2018-31.07.2019.csv'
    data_folder = 'data/'

    account = st.account(cash=1000000, risk=1, stock_list=ticker_list, verbose=True)  
    account.initializeDatasets(file_suffix, data_folder)
    account.trade()
    account.print_results(st.dataset_dict)