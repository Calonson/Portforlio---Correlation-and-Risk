import os
import requests
import pandas as pd
import numpy as np
import scipy.stats
import urllib.parse
import csv

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from cs50 import get_string
from functools import wraps
from datetime import datetime


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol, time):
    """Look up quote for symbol."""

    # Contact API for immediate price
    if time != "3m":
        try:
            api_key = os.environ.get("API_KEY")
            url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}"
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException:
            return None

        # Parse response
        try:
            quote = response.json()
            return {
                "name": quote["companyName"],
                "price": float(quote["latestPrice"]),
                "symbol": quote["symbol"]
            }
        except (KeyError, TypeError, ValueError):
            return None

    # Contact API for historical price
    else:
        try:
            api_key = os.environ.get("API_KEY")
            url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/chart/{time}?chartCloseOnly=True&&token={api_key}"
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException:
            return None

        # Parse response
        try:
            quote = response.json()
            return quote
        except (KeyError, TypeError, ValueError):
            return None


def get_time():
    now = datetime.now()
    return now


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"


def correlation(symbols, df, pf1_df):
    coefficient = {}
    pvalue = np.zeros([len(symbols)])
    for i in range(len(symbols)):
            vals_i = df[df["symbol"] == symbols[i]]['close'].values
            r, p = scipy.stats.pearsonr(vals_i, pf1_df)
            coefficient.update({symbols[i]:r})
            pvalue[i] = p
    sorted_coeff = sorted(coefficient.items(), key=lambda x: x[1],reverse=True)
    return coefficient, pvalue, sorted_coeff


def statement(db):
    cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
    cash = cash[0]["cash"]
    cash = round(cash, 2)
    buysum = db.execute(
        "SELECT symbol, SUM(shares), name FROM history WHERE user_id = ? AND action = ? GROUP BY symbol ORDER BY symbol", session["user_id"], "buy")
    sellsum = db.execute(
        "SELECT symbol, SUM(shares), name FROM history WHERE user_id = ? AND action = ? GROUP BY symbol ORDER BY symbol", session["user_id"], "sell")
    i = 0
    while i < len(buysum):
        for j in range(len(sellsum)):
            if buysum[i]["symbol"] == sellsum[j]["symbol"]:
                buysum[i]["SUM(shares)"] = buysum[i]["SUM(shares)"] - sellsum[j]["SUM(shares)"]
        if buysum[i]["SUM(shares)"] == 0:
            buysum.pop(i)
        else:
            i = i + 1
    grandtotal = 0
    for k in range(len(buysum)):
        symbol = buysum[k]["symbol"]
        result = lookup(symbol,0)
        buysum[k]["price"] = result["price"]
        buysum[k]["total"] = result["price"] * buysum[k]["SUM(shares)"]
        grandtotal = buysum[k]["total"] + grandtotal
    grandtotal = grandtotal + cash
    return buysum, cash, grandtotal

def get_avg_prices(df):
    for i in range(2):
        if i == 0:
            tmp_piv_df = df[["norm_close", "symbol", "date"]].pivot("date", "symbol")
            tmp_piv_df = tmp_piv_df.dropna()
            tmp_piv_df.columns = tmp_piv_df.columns.get_level_values(1)
            avg_normalc = tmp_piv_df.mean(axis=1)
        elif i > 0:
            tmp_piv_df = df[["close", "symbol", "date"]].pivot("date", "symbol")
            tmp_piv_df = tmp_piv_df.dropna()
            tmp_piv_df.columns = tmp_piv_df.columns.get_level_values(1)
            avg = tmp_piv_df.mean(axis=1)
            avg_close = []
            for j in range(len(avg)):
                avg_close.append(avg[j])

    return avg_normalc, avg_close
