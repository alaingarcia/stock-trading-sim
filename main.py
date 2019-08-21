import stock_trading_sim as st
import pandas as pd

ticker_list = ['AAPL','V','MSFT','AMZN','FB','GOOG','JPM','UNH','BAC','MA']
account = st.account(cash=1000000, risk=1, stock_list=ticker_list)
suffix = '.USUSD_Candlestick_4_Hour_ASK_30.01.2018-31.07.2019.csv'

for ticker in account.stock_list:
    df = pd.read_csv('data/' + ticker + suffix, sep=',')
    st.dataset_dict[ticker] = st.dataset(df)

# only works if all the datasets are consistent with each other
# same time periods, same length of time, etc.
for i in range(len(st.dataset_dict[ticker_list[0]].df.index)):
    st.trade(st.dataset_dict, account, i)

account.print_results(st.dataset_dict)