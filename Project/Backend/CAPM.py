import yfinance as yf
import pandas as pd
import statsmodels.api as sm

# CAPM Model:
# E(Ri) = Rf + beta * (Rm - Rf)
# E(Ri): Expected Return of Stock i
# Rf: Risk-free Return
# Rm: Expected Market Return
# beta: Stock's Sensitivity to the market, beta = Cov(Ri, Rm) / Var(Rm)

sp500 = yf.Ticker("^GSPC")
hist = sp500.history(period="5y")  # S&P 500 data in last 5 years
sp_year = hist["Close"].resample("Y").last()
annual_returns = sp_year.pct_change().dropna()
Rm = annual_returns.mean() # Expected Market Return

tnx = yf.Ticker("^TNX") # U.S. 10-year Treasury Return
Rf = tnx.history(period="1mo")["Close"].iloc[-1] / 100 # Risk-free Return

print("Expected market return (S&P 500 Index)", Rm)
print("Risk-free Rate (U.S. 10-Year Treasury): ", Rf)

print("How many stocks are you considering?")
i = int(input())

for a in range(i):
    print("Enter your choice of stock, in yahoo finance ticker format: ")

    choice = str(input())
    
    stock = yf.Ticker(choice).history(period="5y")["Close"]
    market = yf.Ticker("^GSPC").history(period="5y")["Close"]

    # Calculating beta using statsmodels.api
    
    returns = pd.DataFrame({"stock": stock.pct_change(), "market": market.pct_change()}).dropna()

    X = sm.add_constant(returns["market"])
    model = sm.OLS(returns["stock"], X).fit()
    beta = model.params["market"] 

    print("Beta of the stock, sensitivity to market: ", beta)

    stock_return = Rf + beta * (Rm - Rf) # Expected Stock Return from CAPM Model

    print("The expected annual return of your stock is:", int(stock_return * 10000)/ 100.0, "%")

    t = yf.Ticker(choice)
    hist = t.history(period="5y")["Close"]

    prices = hist.resample("YE").last()

    price_dict = {d.year: p for d, p in prices.items()}

    # CAGR
    buy_price = price_dict[years[0]]
    sell_price = price_dict[years[-1]]
    n_years = years[-1] - years[0]
    cagr = (sell_price / buy_price) ** (1/n_years) - 1 # Actual Compound Annual Growth Rate of the Stock

    print("The actual annual return of your stock in 5 years is:", int(cagr*10000) / 100.0, "%")


