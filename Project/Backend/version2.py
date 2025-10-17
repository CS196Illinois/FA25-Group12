import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm  # type: ignore
import matplotlib.pyplot as plt  # type: ignore

# ---- Optional: SciPy for constrained optimization ----
try:
    from scipy.optimize import minimize # type: ignore
    _HAVE_SCIPY = True
except Exception:
    _HAVE_SCIPY = False

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

def annualize_cov(cov_daily: np.ndarray, periods: int = 252) -> np.ndarray:
    return cov_daily * periods

def portfolio_stats(w: np.ndarray, mu: np.ndarray, Sigma_ann: np.ndarray, rf: float) -> dict:
    port_ret = float(w @ mu)
    port_var = float(w @ Sigma_ann @ w)
    port_vol = float(np.sqrt(max(port_var, 0.0)))
    sharpe = (port_ret - rf) / port_vol if port_vol > 0 else np.nan
    return {"expected_return": port_ret, "volatility": port_vol, "sharpe": sharpe}

def optimize_max_sharpe(mu: np.ndarray, Sigma_ann: np.ndarray, rf: float, allow_short: bool) -> np.ndarray:
    n = len(mu)
    if not _HAVE_SCIPY:
        # Fallback: heuristic proportional to (mu - rf) / diag(Sigma)
        risk = np.diag(Sigma_ann).clip(min=1e-12)
        scores = (mu - rf) / np.sqrt(risk)
        scores = np.maximum(scores, 0) if not allow_short else scores
        if np.all(scores == 0):
            return np.ones(n) / n
        w = scores / scores.sum()
        return w

    def neg_sharpe(w):
        r = w @ mu
        v = w @ Sigma_ann @ w
        vol = np.sqrt(max(v, 1e-18))
        return - (r - rf) / vol

    w0 = np.ones(n) / n
    bounds = [(-1, 1) if allow_short else (0, 1) for _ in range(n)]
    cons = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    res = minimize(neg_sharpe, w0, method="SLSQP", bounds=bounds, constraints=cons, options={"maxiter": 1000})
    return (res.x if res.success else w0)

def optimize_min_variance(mu: np.ndarray, Sigma_ann: np.ndarray, allow_short: bool) -> np.ndarray:
    n = len(mu)
    if not _HAVE_SCIPY:
        # Fallback: inverse-variance weights (no short)
        iv = 1 / np.diag(Sigma_ann).clip(min=1e-12)
        if not allow_short:
            iv = np.maximum(iv, 0)
        return iv / iv.sum()

    def var_obj(w):
        return w @ Sigma_ann @ w

    w0 = np.ones(n) / n
    bounds = [(-1, 1) if allow_short else (0, 1) for _ in range(n)]
    cons = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    res = minimize(var_obj, w0, method="SLSQP", bounds=bounds, constraints=cons, options={"maxiter": 1000})
    return (res.x if res.success else w0)

def optimize_target_return(mu: np.ndarray, Sigma_ann: np.ndarray, target_ret: float, allow_short: bool) -> np.ndarray:
    n = len(mu)
    if not _HAVE_SCIPY:
        # Fallback: project to closest direction to reach target (no constraints robustness not guaranteed)
        w = np.ones(n) / n
        # Simple scaling towards higher expected return names
        up = np.maximum(mu, 0)
        if up.sum() > 0:
            w = up / up.sum()
        return w

    def var_obj(w):
        return w @ Sigma_ann @ w

    w0 = np.ones(n) / n
    bounds = [(-1, 1) if allow_short else (0, 1) for _ in range(n)]
    cons = [
        {"type": "eq", "fun": lambda w: np.sum(w) - 1},
        {"type": "eq", "fun": lambda w, mu=mu, t=target_ret: w @ mu - t},
    ]
    res = minimize(var_obj, w0, method="SLSQP", bounds=bounds, constraints=cons, options={"maxiter": 1000})
    return (res.x if res.success else w0)

def print_weights(tickers, w):
    print("\nOptimal Portfolio Weights")
    print("-" * 30)
    for t, wi in zip(tickers, w):
        print(f"{t:<8s} : {wi:6.2%}")
    print(f"Sum      : {w.sum():6.2%}")

# -------------------- Existing market setup --------------------
sp500 = yf.Ticker("^GSPC")
hist = sp500.history(period="5y")  # last 5 years
sp_year = hist["Close"].resample("Y").last()
annual_returns = sp_year.pct_change().dropna()
Rm = annual_returns.mean()

tnx = yf.Ticker("^TNX")
Rf = tnx.history(period="1mo")["Close"].iloc[-1] / 100  # TNX is ~10Y yield in tenths of a percent; adjust to decimal

print("Here is how current market looks like: ")
print("Expected market return (S&P 500 Index)", Rm)
print("Risk-free Rate (U.S. 10 Years Treasury): ", Rf)

print("How many stocks are you considering?")
i = int(input().strip())

# ---- Collect per-stock artifacts for later optimization ----
tickers = []
expected_returns_capm = {}  # annualized, CAPM
daily_returns_matrix = []   # list of Series; will align into DataFrame

for _ in range(i):
    print("Enter your choice of stock, in yahoo finance ticker format: ")
    choice = str(input()).strip()
    tickers.append(choice)

    stock = yf.Ticker(choice).history(period="5y")["Close"]
    market = yf.Ticker("^GSPC").history(period="5y")["Close"]

    # ---- Robust, aligned returns (fixes KeyError 'market') ----
    returns = build_returns_aligned(stock, market)
    if returns.empty:
        stock_d = yf.download(choice, period="5y", interval="1d", progress=False)["Close"]
        market_d = yf.download("^GSPC", period="5y", interval="1d", progress=False)["Close"]
        returns = build_returns_aligned(stock_d, market_d)

    if returns.empty:
        print(f"Not enough overlapping observations for {choice}. Skipping CAPM beta.")
        # Still try to carry daily returns of stock alone for covariance later
        single = yf.Ticker(choice).history(period="5y")["Close"].dropna().pct_change().dropna()
        single.name = choice
        daily_returns_matrix.append(single)
        continue
    else:
        X = sm.add_constant(returns["market"])
        model = sm.OLS(returns["stock"], X).fit()
        beta = model.params.get("market", np.nan)
        print("Beta of the stock, sensitivity to market: ", beta)

        stock_return = Rf + beta * (Rm - Rf)
        expected_returns_capm[choice] = float(stock_return)

        print("The expected annual return of your stock is:",
              int(stock_return * 10000) / 100.0, "%")

    # Save stock daily returns (for covariance)
    stock_daily = returns["stock"].copy()
    stock_daily.name = choice
    daily_returns_matrix.append(stock_daily)

    # ---- Actual CAGR & plot ----
    t = yf.Ticker(choice)
    hist = t.history(start="2020-01-01", end="2025-12-31")
    prices = hist.get("Close", pd.Series(dtype=float))

    year_end_prices = prices.resample("YE").last()
    price_dict = {d.year: p for d, p in year_end_prices.items()}

    # Annual returns
    annual_returns_stock = {}
    years = sorted(price_dict.keys())
    for j in range(1, len(years)):
        y0, y1 = years[j - 1], years[j]
        annual_returns_stock[y1] = price_dict[y1] / price_dict[y0] - 1

    # CAGR
    if years:
        buy_price = price_dict[years[0]]
        sell_price = price_dict[years[-1]]
        n_years = max(1, years[-1] - years[0])
        if buy_price > 0:
            cagr = (sell_price / buy_price) ** (1 / n_years) - 1
            print("The actual annual return of your stock in 5 years is:",
                  int(cagr * 10000) / 100.0, "%")

    # Plot (per stock) with 20-day MA
    if not prices.empty:
        ma20 = prices.rolling(window=20).mean()
        plt.figure(figsize=(10, 5))
        plt.plot(prices.index, prices.values, label=f"{choice} Close")
        plt.plot(ma20.index, ma20.values, label="20-day MA")
        plt.title(f"{choice} closing price (last 5 years) with 20-day MA")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

# -------------------- PORTFOLIO OPTIMIZER --------------------
# Build a single DataFrame of daily returns aligned across all chosen stocks
if len(daily_returns_matrix) >= 2:
    stock_returns_df = pd.concat(daily_returns_matrix, axis=1, join="inner").dropna()
else:
    stock_returns_df = pd.DataFrame(daily_returns_matrix[0]) if daily_returns_matrix else pd.DataFrame()

# Keep tickers that actually have returns
valid_cols = [c for c in stock_returns_df.columns if c in expected_returns_capm or c in tickers]
stock_returns_df = stock_returns_df[valid_cols]

# Expected returns vector (annual, CAPM). If some tickers missed CAPM (insufficient overlap),
# fall back to their historical mean return annualized.
mu_series = pd.Series(index=stock_returns_df.columns, dtype=float)
for col in stock_returns_df.columns:
    if col in expected_returns_capm:
        mu_series[col] = expected_returns_capm[col]
    else:
        # fallback: historical daily mean * 252 (approx; ignores compounding)
        mu_series[col] = stock_returns_df[col].mean() * 252.0

if mu_series.isna().all() or stock_returns_df.empty:
    print("\n[Portfolio] Not enough data to optimize (no returns or expected returns).")
else:
    Sigma_daily = stock_returns_df.cov().values
    Sigma_ann = annualize_cov(Sigma_daily, periods=252)
    mu = mu_series.values
    used_tickers = list(mu_series.index)

    print("\nChoose optimizer mode: (1) max_sharpe  (2) min_variance  (3) target_return (Enter an integer)")
    mode_input = input().strip()
    if mode_input not in {"1", "2", "3"}:
        mode_input = "1"

    allow_short = False  # set True if you want to allow shorting
    if mode_input == "1":
        w = optimize_max_sharpe(mu, Sigma_ann, Rf, allow_short)
    elif mode_input == "2":
        w = optimize_min_variance(mu, Sigma_ann, allow_short)
    else:
        print("Enter target annual return in decimal (e.g., 0.12 for 12%):")
        try:
            target_ret = float(input().strip())
        except Exception:
            target_ret = float(np.nan)
        if not np.isfinite(target_ret):
            print("Invalid target; defaulting to max_sharpe.")
            w = optimize_max_sharpe(mu, Sigma_ann, Rf, allow_short)
        else:
            w = optimize_target_return(mu, Sigma_ann, target_ret, allow_short)

    # Normalize minor numerical drift
    w = np.array(w, dtype=float)
    if w.sum() != 0:
        w = np.maximum(w, 0) if not allow_short else w
        s = w.sum()
        if s == 0:
            w = np.ones_like(w) / len(w)
        else:
            w = w / s
    else:
        w = np.ones_like(w) / len(w)

    print_weights(used_tickers, w)
    stats = portfolio_stats(w, mu, Sigma_ann, Rf)
    print("\nPortfolio Stats (annualized):")
    print(f"Expected Return : {stats['expected_return']:.2%}")
    print(f"Volatility      : {stats['volatility']:.2%}")
    print(f"Sharpe (Rf={Rf:.2%}) : {stats['sharpe']:.3f}")

    # Compare to equal-weighted baseline
    weq = np.ones_like(w) / len(w)
    stats_eq = portfolio_stats(weq, mu, Sigma_ann, Rf)
    print("\nEqual-Weight Baseline:")
    print(f"Expected Return : {stats_eq['expected_return']:.2%}")
    print(f"Volatility      : {stats_eq['volatility']:.2%}")
    print(f"Sharpe (Rf={Rf:.2%}) : {stats_eq['sharpe']:.3f}")

    print("Your information is complete, reached end of version2.")
