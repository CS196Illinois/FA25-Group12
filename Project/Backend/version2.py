# backend/app.py
import math
from typing import List, Literal, Optional, Dict, Any

import numpy as np
import pandas as pd
import yfinance as yf
import statsmodels.api as sm

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# ---- Optional: SciPy for constrained optimization ----
try:
    from scipy.optimize import minimize
    _HAVE_SCIPY = True
except Exception:
    _HAVE_SCIPY = False


# ----------------- helpers from your script -----------------
def build_returns_aligned(stock_close: pd.Series, market_close: pd.Series) -> pd.DataFrame:
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
    sharpe = (port_ret - rf) / port_vol if port_vol > 0 else float("nan")
    return {"expected_return": port_ret, "volatility": port_vol, "sharpe": sharpe}

def optimize_max_sharpe(mu: np.ndarray, Sigma_ann: np.ndarray, rf: float, allow_short: bool) -> np.ndarray:
    n = len(mu)
    if not _HAVE_SCIPY:
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
        iv = 1 / np.diag(Sigma_ann).clip(min=1e-12)
        if not allow_short:
            iv = np.maximum(iv, 0)
        return iv / iv.sum()

    def var_obj(w): return w @ Sigma_ann @ w

    w0 = np.ones(n) / n
    bounds = [(-1, 1) if allow_short else (0, 1) for _ in range(n)]
    cons = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    res = minimize(var_obj, w0, method="SLSQP", bounds=bounds, constraints=cons, options={"maxiter": 1000})
    return (res.x if res.success else w0)

def optimize_target_return(mu: np.ndarray, Sigma_ann: np.ndarray, target_ret: float, allow_short: bool) -> np.ndarray:
    n = len(mu)
    if not _HAVE_SCIPY:
        w = np.ones(n) / n
        up = np.maximum(mu, 0)
        if up.sum() > 0:
            w = up / up.sum()
        return w

    def var_obj(w): return w @ Sigma_ann @ w

    w0 = np.ones(n) / n
    bounds = [(-1, 1) if allow_short else (0, 1) for _ in range(n)]
    cons = [
        {"type": "eq", "fun": lambda w: np.sum(w) - 1},
        {"type": "eq", "fun": lambda w, mu=mu, t=target_ret: w @ mu - t},
    ]
    res = minimize(var_obj, w0, method="SLSQP", bounds=bounds, constraints=cons, options={"maxiter": 1000})
    return (res.x if res.success else w0)


# ----------------- request/response models -----------------
class OptimizeRequest(BaseModel):
    tickers: List[str]
    mode: Literal["max_sharpe", "min_variance", "target_return"] = "max_sharpe"
    targetReturn: Optional[float] = None            # decimal, e.g. 0.12 for 12%
    allowShort: bool = False
    historyYears: int = 5

class OptimizeResponse(BaseModel):
    market: Dict[str, float]
    perStock: Dict[str, Dict[str, float]]
    usedTickers: List[str]
    weights: Dict[str, float]
    stats: Dict[str, float]
    baseline: Dict[str, float]


# ----------------- app + CORS -----------------
app = FastAPI(title="Portfolio Optimizer API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # lock this down in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------- core endpoint -----------------
@app.post("/api/optimize", response_model=OptimizeResponse)
def optimize(req: OptimizeRequest):
    years = req.historyYears
    period = f"{years}y"

    # Market (Rm) & Risk-free (Rf)
    sp500 = yf.Ticker("^GSPC").history(period=period)["Close"]
    sp_year = sp500.resample("Y").last()
    annual_returns = sp_year.pct_change().dropna()
    Rm = float(annual_returns.mean())

    tnx = yf.Ticker("^TNX").history(period="1mo")["Close"]
    Rf = float(tnx.iloc[-1] / 100.0)  # decimal

    # Per-stock: CAPM expected returns + daily returns for covariance
    per_stock: Dict[str, Dict[str, float]] = {}
    daily_returns_matrix = []
    capm_mu: Dict[str, float] = {}

    market_full_close = yf.Ticker("^GSPC").history(period=period)["Close"]

    for ticker in req.tickers:
        hist_close = yf.Ticker(ticker).history(period=period)["Close"]
        # aligned returns
        returns = build_returns_aligned(hist_close, market_full_close)

        # CAPM beta & expected return
        if not returns.empty:
            X = sm.add_constant(returns["market"])
            model = sm.OLS(returns["stock"], X).fit()
            beta = float(model.params.get("market", float("nan")))
            exp_ret = float(Rf + beta * (Rm - Rf))
            capm_mu[ticker] = exp_ret
            stock_daily = returns["stock"].copy()
            stock_daily.name = ticker
            daily_returns_matrix.append(stock_daily)
        else:
            # fallback: still collect stock-only daily returns for covariance
            single = hist_close.dropna().pct_change().dropna()
            single.name = ticker
            daily_returns_matrix.append(single)
            beta = float("nan")
            exp_ret = float("nan")

        # simple CAGR (optional)
        prices = hist_close.dropna()
        cagr = float("nan")
        if len(prices) > 1:
            years_span = max(1, (prices.index[-1].year - prices.index[0].year))
            if prices.iloc[0] > 0 and years_span > 0:
                cagr = float((prices.iloc[-1] / prices.iloc[0]) ** (1 / years_span) - 1)

        per_stock[ticker] = {"beta": beta, "expectedCAPM": exp_ret, "cagrApprox": cagr}

    if len(daily_returns_matrix) == 0:
        # Nothing usable
        return OptimizeResponse(
            market={"Rm": Rm, "Rf": Rf},
            perStock=per_stock,
            usedTickers=[],
            weights={},
            stats={},
            baseline={}
        )

    stock_returns_df = pd.concat(daily_returns_matrix, axis=1, join="inner").dropna()
    used_tickers = list(stock_returns_df.columns)

    # expected returns vector (annual)
    mu_series = pd.Series(index=used_tickers, dtype=float)
    for col in used_tickers:
        if col in capm_mu and np.isfinite(capm_mu[col]):
            mu_series[col] = capm_mu[col]
        else:
            mu_series[col] = stock_returns_df[col].mean() * 252.0

    Sigma_ann = annualize_cov(stock_returns_df.cov().values, periods=252)
    mu = mu_series.values

    allow_short = req.allowShort
    if req.mode == "max_sharpe":
        w = optimize_max_sharpe(mu, Sigma_ann, Rf, allow_short)
    elif req.mode == "min_variance":
        w = optimize_min_variance(mu, Sigma_ann, allow_short)
    else:
        t = req.targetReturn if (req.targetReturn is not None) else float("nan")
        if not (isinstance(t, (int, float)) and math.isfinite(t)):
            w = optimize_max_sharpe(mu, Sigma_ann, Rf, allow_short)
        else:
            w = optimize_target_return(mu, Sigma_ann, t, allow_short)

    # Clean & normalize
    w = np.array(w, dtype=float)
    if not allow_short:
        w = np.maximum(w, 0)
    s = w.sum()
    if s == 0:
        w = np.ones_like(w) / len(w)
    else:
        w = w / s

    stats = portfolio_stats(w, mu, Sigma_ann, Rf)
    weq = np.ones_like(w) / len(w)
    stats_eq = portfolio_stats(weq, mu, Sigma_ann, Rf)

    return OptimizeResponse(
        market={"Rm": Rm, "Rf": Rf},
        perStock=per_stock,
        usedTickers=used_tickers,
        weights={t: float(x) for t, x in zip(used_tickers, w.tolist())},
        stats={k: float(v) for k, v in stats.items()},
        baseline={k: float(v) for k, v in stats_eq.items()},
    )
