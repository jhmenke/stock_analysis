from datetime import datetime
from json import loads
from os.path import join, realpath, dirname

import numpy as np
import pandas as pd
import requests
from alpha_vantage.timeseries import TimeSeries
from diskcache import Cache

from stock_analysis import api_key

db = Cache(join(dirname(realpath(__file__)), "stockdb"))

def available_stocks():
    if "stock_list" not in db:
        db["stock_list"] = ["T", "MSFT", "GOOGL", "IBM", "NFLX", "MAXR", "OCDGF"]
    return db["stock_list"]


def modify_available_stocks(new_stock_list):
    assert isinstance(new_stock_list, (tuple, list))
    if new_stock_list == [","]:
        return
    db["stock_list"] = [s for s in new_stock_list if len(s)]


def search_symbol(name: str):
    if len(name) == 0:
        return ""
    url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={name}&apikey={api_key}"
    response = requests.get(url)
    df = pd.DataFrame(loads(response.content.decode("utf-8"))["bestMatches"])
    df.drop(["4. region", "5. marketOpen", "6. marketClose", "7. timezone"], axis=1, inplace=True)
    return df


def receive_stock_data(symbol: str):
    ts = TimeSeries(key=api_key, output_format='pandas')
    # data, meta_data = ts.get_intraday(symbol=symbol, interval='60min', outputsize='full')
    data, meta_data = ts.get_daily_adjusted(symbol=symbol, outputsize="full")
    data = data.sort_index()
    data.rename(columns={
        "1. open": "open",
        "2. high": "high",
        "3. low": "low",
        # "5. adjusted close": "close",
        "4. close": "close",
        "6. volume": "volume",
        "7. divident amount": "dividends",
        "8. split coefficient": "split_coefficient"
    }, inplace=True)
    data.insert(0, "time", data.index.astype(np.int64))
    data["date"] = pd.to_datetime(data.index)
    data["ma21"] = data.close.rolling(21).mean()
    data["ma50"] = data.close.rolling(50).mean()
    data["ma200"] = data.close.rolling(200).mean()
    data["ema21"] = data.close.ewm(span=21, min_periods=0, adjust=False, ignore_na=True).mean()
    data["ema50"] = data.close.ewm(span=50, min_periods=0, adjust=False, ignore_na=True).mean()
    data["ema200"] = data.close.ewm(span=200, min_periods=0, adjust=False, ignore_na=True).mean()
    data = insert_fibonacci_levels(data)
    data = data.iloc[-200:]  # limit to 200 trading days
    return data


def insert_fibonacci_levels(data: pd.DataFrame, use_closing=False):
    min_, max_ = (data.close.min(), data.close.max()) if use_closing else (data.low.min(), data.high.max())
    idxmin_, idxmax_ = (data.close.idxmin(), data.close.idxmax()) if use_closing else (data.low.idxmin(), data.high.idxmax())
    levels, retracements = fib_levels(min_, max_, "down" if idxmin_ > idxmax_ else "up")
    for level, retr in zip(levels, 100. * retracements):
        col_name = f"fib_{retr:.0f}"
        if col_name in data.columns:
            data[col_name] = level
        else:
            data.insert(len(data.columns), col_name, level)
    return data


def load_stock_data(symbol: str):
    if symbol in db and db[symbol]["updated"] == datetime.today().date():
        return db[symbol]["data"]
    db[symbol] = {
        "data": receive_stock_data(symbol),
        "updated": datetime.today().date()
        }
    return db[symbol]["data"]


def fib_levels(stocks_min: float, stocks_max: float, trend: str = "down"):
    assert trend in ("up", "down")
    stock_range = stocks_max - stocks_min
    retracements = np.array([0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0])
    return stocks_min + stock_range * retracements, retracements


def parse_fibs(df: pd.DataFrame):
    trend = "up" if df["close"].idxmax() > df["close"].idxmin() else "down"
    fib_retr, _ = fib_levels(df["low"].min(), df["high"].max(), trend=trend)
    fib_retr2, levels = fib_levels(df["close"].min(), df["close"].max(), trend=trend)
    fib_means = (fib_retr + fib_retr2) / 2.
    return fib_means, fib_retr, fib_retr2, levels


def parse_gaps(df: pd.DataFrame):
    assert isinstance(df.index, pd.RangeIndex)
    df["gap"] = False
    for i in df.index[1:]:
        diff_top = df.loc[i, "low"] - df.loc[i - 1, "high"]
        diff_bottom = df.loc[i - 1, "low"] - df.loc[i, "high"]
        if diff_top > 0 or diff_bottom > 0:
            df.loc[i, "gap"] = True