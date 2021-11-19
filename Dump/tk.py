#!/usr/bin/python3
import tkinter as tk
from pandas.core.frame import DataFrame
import yfinance as yf
import numpy as np
from cutecharts.charts import Line
import talib as ta
import pandas as pd
from pywebio.input import * 
from pywebio.output import * 
def get_score(df: DataFrame, indicator: str, entry_type='long'):
    indicator = indicator.upper()
    if indicator == 'RSI' and entry_type == 'long':
        try:
            rsiValue = df.rsi.head(1).values[0]
            if rsiValue in range(60,70):
                return 5
            elif rsiValue in range(70,80):
                return 4
            elif rsiValue >= 80:
                return 3
            elif rsiValue in range(50,60):
                return 2
            else:
                return 0
        except IndexError:
            return 0
    if indicator == 'MACD' and entry_type == 'long':
        macd = df.macd_crossover
        try:
            date = macd.iloc[list(np.where(df["macd_crossover"] == 1)[0])].index.values[0]
            date = pd.to_datetime(date)
            dates = df.index.values
            for i in range(0,len(dates)):
                if pd.to_datetime(dates[i]).date() == date:
                    return 5 - i
            return 0
        except IndexError:
            return 0
    if indicator == 'EMA' and entry_type == 'long':
        try:
            date = df.ema_crossover.iloc[list(np.where(df["ema_crossover"] == 1)[0])].index.values[0]
            date = pd.to_datetime(date)
            dates = df.index.values
            for i in range(0,len(dates)):
                if pd.to_datetime(dates[i]).date() == date:
                    return 5 - i
            return 0
        except IndexError:
            return 0
    if indicator == 'VOLUME' and entry_type == 'long':
        try:
            date = df.volume_buy.iloc[list(np.where(df["volume_buy"] == 1)[0])].index.values[0]
            date = pd.to_datetime(date)
            dates = df.index.values
            for i in range(0,len(dates)):
                if pd.to_datetime(dates[i]).date() == date:
                    return 5 - i
            return 0
        except IndexError:
            return 0
    return None

def create_chart(labels: list, values: list):
    chart = Line("Total Scores vs Date")
    chart.set_options(labels=labels, x_label="Date", y_label="Score")
    chart.add_series("Total Scores", values)
    return chart 
def create_chart2(labels: list, values: list):
    chart = Line("Close vs Date")
    chart.set_options(labels=labels, x_label="Close", y_label="Score")
    chart.add_series("Close", values)
    return chart
def create_chart3(labels: list, values: list):
    chart = Line("High vs Score")
    chart.set_options(labels=labels, x_label="High", y_label="Score")
    chart.add_series("High", values)
    return chart
def create_chart4(labels: list, values: list):
    chart = Line("Close vs Date")
    chart.set_options(labels=labels, x_label="Close", y_label="Score")
    chart.add_series("Close", values)
    return chart
def import_csv_data():
    from tkinter.filedialog import askopenfilename
    from pywebio.output import put_text,put_markdown,put_file ,put_html
    global v
    csv_file_path = askopenfilename()
    v.set(csv_file_path)

    data = pd.read_csv(csv_file_path)
    data.set_index('Date', inplace=True)
    #try to remove Adj Close if not present do nothing
    try:
        data = data.drop(['Adj Close'], axis = 1)
    except KeyError:
        tk.messagebox.showinfo("Error", "Please select a valid csv file")
        return
    
    data['5EMA'] = pd.Series.ewm(data['Close'], span=5).mean()

    data['26EMA'] = pd.Series.ewm(data['Close'], span=26).mean()

    data['rsi'] = ta.RSI(data['Close'].values, timeperiod=14)

    data['macd'], data['macdSignal'], data['macdHist'] = ta.MACD(data.Close.values, fastperiod=12, slowperiod=26, signalperiod=9)

    data['macd_crossover'] = np.where(((data.macd > data.macdSignal) & (data.macd.shift(1) < data.macdSignal.shift(1))), 1, 0)
    data['macd_crossunder'] = np.where(((data.macd < data.macdSignal) & (data.macd.shift(1) > data.macdSignal.shift(1))), 1, 0)
    data['ema_crossover'] = np.where(((data['5EMA'].shift(1) <= data['26EMA'].shift(1)) & (data['5EMA'] > data['26EMA'] )), 1, 0)
    data['ema_crossunder'] = np.where(((data['5EMA'].shift(1) >= data['26EMA'].shift(1)) & (data['5EMA'] < data['26EMA'] )), 1, 0)

    data['rsi_buy'] = np.where(data.rsi > 60, 1, 0)
    data['rsi_sell'] = np.where(data.rsi < 40, 1, 0)

    data['volume_buy'] = np.where((data.Volume > data.Volume.ewm(span=5).mean()) & (data.Close > data.Close.shift(1)), 1, 0)
    data['volume_sell'] = np.where((data.Volume > data.Volume.ewm(span=5).mean()) & (data.Close < data.Close.shift(1)), 1, 0)

    last_week_data = data.tail(5).sort_values(by='Date', ascending=False)
    rsiScore = get_score(last_week_data, indicator='rsi')
    macdScore = get_score(last_week_data, indicator='macd')
    emaScore = get_score(last_week_data, indicator='ema')
    volumeScore = get_score(last_week_data, indicator='volume')
    totalScore = rsiScore + macdScore + emaScore + volumeScore

    totalScoreL = [0,0,0,0,0]
    for i in range(len(data.index.values)-5):
        df = data[i:i+5]
        rsiScore = get_score(df, indicator='rsi')
        macdScore = get_score(df, indicator='macd')
        emaScore = get_score(df, indicator='ema')
        volumeScore = get_score(df, indicator='volume')
        totalScore = rsiScore + macdScore + emaScore + volumeScore
        totalScoreL.append(totalScore)

    data['totalScore'] = totalScoreL
    data['totalScore'].astype(int)
    #data['totalScore ewm'] =data['totalScore'].ewm(span=5).mean()
    chart = create_chart(list(data.index),list(data.totalScore))
    put_html(chart.render_notebook())
    chart2 = create_chart2(list(data.Close),list(data.totalScore))
    put_html(chart2.render_notebook())
    chart3 = create_chart3(list(data.High),list(data.totalScore))
    put_html(chart3.render_notebook())
    #chart4 = create_chart4(list(data.Close),list(data["totalScore ewm"]))
    #put_html(chart4.render_notebook())
    #content
    put_html(DataFrame(data).to_html())
    #calculate corelation matrix
    corr = data.corr()
    #plot corelation matrix
    put_html(DataFrame(corr).to_html())
    data.to_csv('results.csv')
    with open ('results.csv', 'rb') as fp:
        content = fp.read()
    put_markdown("""## export results here""")
    put_file('results.csv', content, 'Download the CSV file by clicking here')
def about():
    tk.messagebox.showinfo("About", "This is a trading tool for stocks.\n\n Back-End By Dev Mehta \n\n Front-End By Vivek Patel")
#display welcome in tn tkinter window in full screen
def how_to_use():
    tk.messagebox.showinfo("How to use", "1. Go to https://finance.yahoo.com/ \n\n2. Download Historical Data.\n\n3. Select file.\n\n4. Click on Import.\n\n5. Wait for the results.\n\n6. Click on Export to save results\n\n")
#tk.Label(root, text='File Path').pack(side="top", fill="both", expand=True, padx=10, pady=10)try("500x500")
def Download():
    tk.messagebox.showinfo("Info","This feature is in beta version Please visit this page later\n\n")
    #import yfinance as yf
    # tickers = [
    # 'SBILIFE',
    # 'MARUTI',
    # 'TATAMOTORS',
    # 'ITC',
    # 'ASIANPAINT',
    # 'POWERGRID',
    # 'NTPC',
    # 'INDUSINDBK',
    # 'TECHM',
    # 'BAJFINANCE',
    # 'SBIN',
    # 'TATACONSUM',
    # 'BAJAJFINSV',
    # 'LT',
    # 'INFY',
    # 'HDFCBANK',
    # 'WIPRO',
    # 'UPL']
    # tk.messagebox.showinfo("Download","This feature is in beta version\n\n following data will be downloaded\n\n"+str(tickers))
    # for ticker in tickers:
    #     yf.Ticker(f'{ticker}.NS').history(period='max', actions=False).to_csv(f'data/{ticker}.csv')
    #     tk.messagebox.showinfo("Please Wait", "Downloaded "+ticker+'Data Successfully')
    # tk.messagebox.showinfo("Downloaded", "Downloaded Successfully"+"\n\n"+"Please import the file from data directory")
root = tk.Tk()
root.title("Stock Market Analysis")
root.geometry("300x400")
root.bind('<Escape>', lambda e: root.destroy())
label = tk.Label(root, text='File Path')
label.pack()
v = tk.StringVar()
entry = tk.Entry(root, textvariable=v)
entry.pack()
Button1 = tk.Button(root, text='Import', command=import_csv_data)
Button1.pack()
Button4 = tk.Button(root, text='How to use', command=how_to_use)
Button4.pack()
Button5 = tk.Button(root, text='Download Data', command=Download)
Button5.pack()
Button3 = tk.Button(root, text='About', command=about)
Button3.pack()
Button2 = tk.Button(root, text='Exit', command=root.destroy)
Button2.pack()
#set padding of all buttons
for child in root.winfo_children():
    child.pack_configure(padx=10, pady=10)

# entry = tk.Entry(root, textvariable=v).grid(row=5, column=2)
# tk.Button(root, text='Browse Data Set',command=import_csv_data).grid(row=7, column=2)
# tk.Button(root, text='Close',command=root.destroy).grid(row=8, column=2)
#CREATE SEARCH BAR
root.mainloop()
root.destroy()