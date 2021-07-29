import os
import plotly.express as px
import pandas as pd
import math

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash


from helpers import apology, login_required, lookup, usd, get_time, correlation, statement, get_avg_prices

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    buysum, cash, grandtotal = statement(db)
    return render_template("index.html", buysum=buysum, cash=cash, grandtotal=grandtotal)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    sp500df = pd.read_csv("static/sp500.csv", encoding = "latin_1")
    symbollist = []
    """ only take 100 stock due to limtied credit in IEX cloud"""
    for i in range(100):
        symbol = sp500df.loc[i,"Symbol"]
        symbollist.append(symbol)
    symbollist = sorted(symbollist)
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Show the quoted page
        result = lookup(request.form.get("symbol"),0)
        if result == None:
            return apology("No such stock", 400)
        shares = request.form.get("shares", type=int)
        if shares == None:
            return apology("Missing number of shares", 400)
        if shares <= 0:
            return apology("Number of shares must be positive integer", 400)
        cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        if result["price"] * shares > cash[0]["cash"]:
            return apology("You don't have enough cash", 400)
        cash = cash[0]["cash"] - result["price"] * shares
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash, session["user_id"])
        now = get_time()
        db.execute("INSERT INTO history(user_id, action, symbol, price, shares, datetime, name) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   session["user_id"], "buy", result["symbol"], result["price"], shares, now, result["name"])
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html", symbollist=symbollist)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    trans = db.execute(
        "SELECT name, symbol, shares, price, action, datetime FROM history WHERE user_id = ? ORDER BY datetime", session["user_id"])
    return render_template("history.html", trans=trans)


@app.route("/graph")
@login_required
def graph():
    return render_template("graph.html")

@app.route("/n_graph")
@login_required
def n_graph():
    return render_template("n_graph.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        symbol = request.form.get("symbol")
        # Show the quoted page
        historical = lookup(request.form.get("symbol"),"3m")
        df = pd.DataFrame(historical)
        fig = px.line(historical, x="date", y="close", template="plotly_white",
        title=f"Stock price history for {symbol}")
        fig.write_html("/home/ubuntu/project/finance/templates/graph.html")

        result = lookup(request.form.get("symbol"),0)
        if result == None:
            return apology("No such stock", 400)
        return render_template("quoted.html", result=result)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")

@app.route("/portfolio", methods=["GET", "POST"])
@login_required
def portfolio():
    #compose the dataframe
    symbollist = []
    """
    ###only take 100 stock due to limtied credit in IEX cloud and that should be regular daily job,
    ###but I only update it once due to limited created
    sp500df = pd.read_csv("static/sp500.csv", encoding = "latin_1")
    for i in range(100):
        symbol = sp500df.loc[i,"Symbol"]
        name = sp500df.loc[i,"Name"]
        symbollist.append(symbol)
        historical = lookup(symbol,"3m")
        tempdf = pd.DataFrame(historical)
        tempdf = tempdf.assign(symbol=symbol)
        tempdf = tempdf.assign(name=name)
        tempdf = tempdf.assign(norm_close=0)
        min_date = tempdf["date"].min()
        ref_val = tempdf[tempdf["date"] == min_date]["close"].values[0]
        for j in range(len(tempdf)):
            tempdf.loc[j, "norm_close"] = tempdf.loc[j, "close"] / ref_val
        if i == 0:
            df = tempdf
        elif (i > 0):
            df = df.append(tempdf)
    con = 'sqlite:///finance.db'
    df.to_sql('sp500', con, if_exists='replace', index = False)
    """

    con = 'sqlite:///finance.db'
    df = pd.read_sql_table ('sp500', con)
    symbollist = df.symbol.unique()
    buysum, cash, grandtotal = statement(db)
    #calculate variance and risk
    temp_syms = []
    for i in range(len(buysum)):
        temp_syms.append(buysum[i]["symbol"])
    pf1_df = df[df.symbol.isin(temp_syms)]
    pf1_avgn, pf1_avgc = get_avg_prices(pf1_df)
    pf1_var = pf1_avgn.var()
    risk = math.sqrt(pf1_var)
    r_array, p_array, sorted_coeff = correlation(symbollist, df, pf1_avgc)
    for symbol in sorted_coeff:
        if (symbol[0] not in temp_syms):
            post_sym = symbol[0]
            break
    for symbol in reversed(sorted_coeff):
        if (symbol[0] not in temp_syms):
            neg_sym = symbol[0]
            break
    #Assuuming risk > 0.01 , then the risk level is high (since I didnt take the weight as the factor, it is just a pure assumption for demo)
    if risk > 0.04:
        risklevel = "High, recommend to diversify"
        color = "color:#FF0000;"
        rec_name = df.name[df["symbol"] == neg_sym].unique()
        rec_sym = neg_sym
    else:
        risklevel = "Low, recommend with more correlated stock"
        color = "color:#008000;"
        rec_name = df.name[df["symbol"] == post_sym].unique()
        rec_sym = post_sym
    return render_template("portfolio.html", buysum=buysum, risklevel=risklevel, rec_name=rec_name, rec_sym=rec_sym, color=color)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for any exisitng username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username was submitted
        if not request.form.get("username") or len(rows) >= 1:
            return apology("Input is blank or Username already exists", 400)

        # Ensure password was submitted
        elif not request.form.get("password") or (request.form.get("password") != request.form.get("confirmation")):
            return apology("Input is blank or passowrds do not match", 400)

        hash = generate_password_hash(request.form.get("password"), method='pbkdf2:sha1', salt_length=8)
        db.execute("INSERT INTO users(username, hash) VALUES (?, ?)", request.form.get("username"), hash)

        # Redirect user to login page
        return render_template("login.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Show the quoted page
        symbol = request.form.get("symbol")
        result = lookup(symbol,0)
        if result == None:
            return apology("No such stock", 400)
        shares = request.form.get("shares", type=int)
        if shares == None:
            return apology("Missing number of shares", 400)
        if shares <= 0:
            return apology("Number of shares must be positive integer", 400)
        # check any stock and number of shares in new table
        buysum = db.execute(
            "SELECT symbol, SUM(shares), name FROM history WHERE user_id = ? AND action = ? GROUP BY symbol ORDER BY symbol", session["user_id"], "buy")
        sellsum = db.execute(
            "SELECT symbol, SUM(shares), name FROM history WHERE user_id = ? AND action = ? GROUP BY symbol ORDER BY symbol", session["user_id"], "sell")
        for i in range(len(buysum)):
            if buysum[i]["symbol"] == symbol.upper():
                if buysum[i]["SUM(shares)"] < shares:
                    return apology("Not enough shares or Not own this stock", 400)
                for j in range(len(sellsum)):
                    if buysum[i]["symbol"] == sellsum[j]["symbol"]:
                        if buysum[i]["SUM(shares)"] < (sellsum[j]["SUM(shares)"] + shares):
                            return apology("Not enough shares or Not own this stock", 403)
                now = get_time()
                db.execute("INSERT INTO history(user_id, action, symbol, price, shares, datetime, name) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           session["user_id"], "sell", result["symbol"], result["price"], shares, now, result["name"])
                cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
                cash = cash[0]["cash"] + result["price"] * shares
                db.execute("UPDATE users SET cash = ? WHERE id = ?", cash, session["user_id"])
                return redirect("/")
        return apology("Don't own this stock", 400)
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        symbols = []
        buysum = db.execute(
            "SELECT symbol, SUM(shares), name FROM history WHERE user_id = ? AND action = ? GROUP BY symbol ORDER BY symbol", session["user_id"], "buy")
        sellsum = db.execute(
            "SELECT symbol, SUM(shares), name FROM history WHERE user_id = ? AND action = ? GROUP BY symbol ORDER BY symbol", session["user_id"], "sell")
        for i in range(len(buysum)):
            symbols.append(buysum[i]["symbol"])
            for j in range(len(sellsum)):
                if buysum[i]["symbol"] == sellsum[j]["symbol"] and buysum[i]["SUM(shares)"] <= sellsum[j]["SUM(shares)"]:
                    symbols.remove(buysum[i]["symbol"])
        return render_template("Sell.html", symbols=symbols)


@app.route("/changepw", methods=["GET", "POST"])
@login_required
def changepw():
    if request.method == "POST":
        if not request.form.get("password") or not request.form.get("confirmation") or (request.form.get("password") != request.form.get("confirmation")):
            return apology("Input is blank or passowrds do not match", 400)
        row = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        if check_password_hash(row[0]["hash"], request.form.get("password")):
            return apology("Old password is same as new password", 400)
        else:
            hash = generate_password_hash(request.form.get("password"), method='pbkdf2:sha1', salt_length=8)
            db.execute("UPDATE users SET hash = ? WHERE id = ?", hash, session["user_id"])
            return redirect("/")
    else:
        return render_template("changepw.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
