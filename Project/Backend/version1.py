import yfinance as yf
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

def build_returns_aligned(stock_close: pd.Series, market_close: pd.Series) -> pd.DataFrame:
    """Align stock & market by date (tz-naive, date-only), then compute % changes."""
    s1 = stock_close.dropna().copy()
    s2 = market_close.dropna().copy()
    if getattr(s1.index, "tz", None) is not None:
        s1.index = s1.index.tz_localize(None)
    if getattr(s2.index, "tz", None) is not None:
        s2.index = s2.index.tz_localize(None)
    s1.index = s1.index.normalize()
    s2.index = s2.index.normalize()
    s1.name, s2.name = "stock", "market"
    both = pd.concat([s1, s2], axis=1, join="inner").dropna()
    return both.pct_change().dropna()

sp500 = yf.Ticker("^GSPC")

hist = sp500.history(period="5y")  # last 5 years
sp_year = hist["Close"].resample("Y").last()
annual_returns = sp_year.pct_change().dropna()
Rm = annual_returns.mean()

tnx = yf.Ticker("^TNX")
Rf = tnx.history(period="1mo")["Close"].iloc[-1] / 1000 # 1000 because TNX measures 10 years

print("Here is how current market looks like: ")
print("Expected market return (S&P 500 Index)", Rm)
print("Risk-free Rate (U.S. 20 Years Treasury): ", Rf)

print("How many stocks are you considering?")
i = int(input())

for a in range(i):
    print("Enter your choice of stock, in yahoo finance ticker format: ")
    choice = str(input()).strip()

    stock  = yf.Ticker(choice).history(period="5y")["Close"]
    market = yf.Ticker("^GSPC").history(period="5y")["Close"]

    # ---- Robust, aligned returns (fixes KeyError 'market') ----
    returns = build_returns_aligned(stock, market)
    if returns.empty:
        stock_d  = yf.download(choice,  period="5y", interval="1d", progress=False)["Close"]
        market_d = yf.download("^GSPC", period="5y", interval="1d", progress=False)["Close"]
        returns  = build_returns_aligned(stock_d, market_d)
    

    if returns.empty:
        print(f"Not enough overlapping observations for {choice}. Skipping CAPM beta.")
    else:
        X = sm.add_constant(returns["market"])
        model = sm.OLS(returns["stock"], X).fit()
        beta = model.params["market"]
        print("Beta of the stock, sensitivity to market: ", beta)

        stock_return = Rf + beta * (Rm - Rf)
        print("The expected annual return of your stock is:",
              int(stock_return * 10000) / 100.0, "%")

    t = yf.Ticker(choice)
    hist = t.history(start="2020-01-01", end="2025-12-31")
    prices = hist.get("Close", pd.Series(dtype=float))

    year_end_prices = prices.resample("YE").last()
    price_dict = {d.year: p for d, p in year_end_prices.items()}

    # Annual returns
    annual_returns = {}
    years = sorted(price_dict.keys())
    for j in range(1, len(years)):
        y0, y1 = years[j-1], years[j]
        annual_returns[y1] = price_dict[y1] / price_dict[y0] - 1

    # CAGR
    if years:
        buy_price = price_dict[years[0]]
        sell_price = price_dict[years[-1]]
        n_years = max(1, years[-1] - years[0])
        if buy_price > 0:
            cagr = (sell_price / buy_price) ** (1/n_years) - 1
            print("The actual annual return of your stock in 5 years is:",
                  int(cagr * 10000) / 100.0, "%")

    # Plot (per stock) with 20-day MA
    if not prices.empty:
        ma20 = prices.rolling(window=20).mean()
        plt.figure(figsize=(10,5))
        plt.plot(prices.index, prices.values, label=f"{choice} Close")
        plt.plot(ma20.index, ma20.values, label="20-day MA")
        plt.title(f"{choice} closing price (last 5 years) with 20-day MA")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

