import yfinance as yf
import pandas as pd
import statsmodels.api as sm

sp500 = yf.Ticker("^GSPC")

hist = sp500.history(period="5y")  # last 10 years

sp_year = hist["Close"].resample("Y").last()

annual_returns = sp_year.pct_change().dropna()

Rm = annual_returns.mean()

tnx = yf.Ticker("^TNX")
Rf = tnx.history(period="1mo")["Close"].iloc[-1] / 100 

print("Here is how current market looks like: ")
print("Expected market return (S&P 500 Index)", Rm)
print("Risk-free Rate (U.S. 20 Years Treasury): ", Rf)

print("How many stocks are you considering?")

i = int(input())

for a in range(i):
    print("Enter your choice of stock, in yahoo finance ticker format: ")

    choice = str(input())

    stock = yf.Ticker(choice).history(period="5y")["Close"]
    market = yf.Ticker("^GSPC").history(period="5y")["Close"]

    returns = pd.DataFrame({
        "stock": stock.pct_change(),
        "market": market.pct_change()
    }).dropna()

    X = sm.add_constant(returns["market"])
    model = sm.OLS(returns["stock"], X).fit()
    beta = model.params["market"]

    print("Beta of the stock, sensitivity to market: ", beta)

    stock_return = Rf + beta * (Rm - Rf)

    print("The expected annual return of your stock is:", int(stock_return * 10000)/ 100.0, "%")

    t = yf.Ticker(choice)
    hist = t.history(start="2020-01-01", end="2025-12-31")

    prices = hist["Close"]

    year_end_prices = prices.resample("YE").last()

    price_dict = {d.year: p for d, p in year_end_prices.items()}

    # Annual returns
    annual_returns = {}
    years = sorted(price_dict.keys())
    for i in range(1, len(years)):
        y0, y1 = years[i-1], years[i]
        annual_returns[y1] = price_dict[y1] / price_dict[y0] - 1

    # CAGR
    buy_price = price_dict[years[0]]
    sell_price = price_dict[years[-1]]
    n_years = years[-1] - years[0]
    cagr = (sell_price / buy_price) ** (1/n_years) - 1

    print("The actual annual return of your stock in 5 years is:", int(cagr*10000) / 100.0, "%")

