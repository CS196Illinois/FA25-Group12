# quant/candidate.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
import datetime as dt

import numpy as np
import pandas as pd
import yfinance as yf

# ---- Optional: statsmodels for CAPM beta ----
try:
    import statsmodels.api as sm  # type: ignore
    _HAVE_STATSMODELS = True
except Exception:
    _HAVE_STATSMODELS = False


# ---------- shared util (compatible with your friend's code) ----------
def build_returns_aligned(stock_close: pd.Series, market_close: pd.Series) -> pd.DataFrame:
    """Align stock & market by date (tz-naive, date-only), then compute % changes."""
    s1 = stock_close.dropna().copy()
    s2 = market_close.dropna().copy()
    # strip tz if present
    if getattr(s1.index, "tz", None) is not None:
        s1.index = s1.index.tz_localize(None)
    if getattr(s2.index, "tz", None) is not None:
        s2.index = s2.index.tz_localize(None)
    # normalize to dates
    s1.index = s1.index.normalize()
    s2.index = s2.index.normalize()
    s1.name, s2.name = "stock", "market"
    both = pd.concat([s1, s2], axis=1, join="inner").dropna()
    return both.pct_change().dropna()


def _safe_now_utc():
    return dt.datetime.utcnow().replace(tzinfo=None)


@dataclass
class Candidate:
    """
    Parent class for a security. Lightweight and stateless beyond ticker & cache.
    - Provides: current price, basic info, historical close, aligned returns, CAPM metrics.
    - Plays well with the optimizer by exposing daily returns/history.
    """
    ticker: str
    _tkr: yf.Ticker = field(init=False, repr=False)
    _info_cache: Optional[Dict] = field(default=None, init=False, repr=False)
    _last_price_cache: Optional[Tuple[float, dt.datetime]] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        self.ticker = self.ticker.strip().upper()
        self._tkr = yf.Ticker(self.ticker)

    # ---------- Market data ----------
    def current_price(self, use_fast: bool = True) -> Optional[float]:
        """
        Returns the latest price (best-effort). Caches for a few seconds to avoid spam.
        """
        # Simple 5s memoization
        if self._last_price_cache:
            px, ts = self._last_price_cache
            if ( _safe_now_utc() - ts ).total_seconds() < 5:
                return px

        price: Optional[float] = None
        if use_fast:
            # yfinance fast_info is fastest when available
            try:
                fi = getattr(self._tkr, "fast_info", None)
                if fi:
                    price = float(fi.get("last_price") or fi.get("last_close") or 0) or None
            except Exception:
                price = None

        if price is None:
            try:
                # fallback to history
                h = self._tkr.history(period="1d", interval="1m")
                if not h.empty:
                    price = float(h["Close"].dropna().iloc[-1])
            except Exception:
                price = None

        if price is None:
            try:
                h = self._tkr.history(period="5d", interval="1d")
                if not h.empty:
                    price = float(h["Close"].dropna().iloc[-1])
            except Exception:
                pass

        if price is not None:
            self._last_price_cache = (price, _safe_now_utc())
        return price

    def basic_info(self) -> Dict[str, Optional[str]]:
        """Return a compact dict of basic company info."""
        if self._info_cache is None:
            info = {}
            # yfinance switched to .get_info() for some versions
            try:
                if hasattr(self._tkr, "get_info"):
                    info = self._tkr.get_info() or {}
                else:
                    info = getattr(self._tkr, "info", {}) or {}
            except Exception:
                info = {}
            self._info_cache = info

        i = self._info_cache or {}
        fields = {
            "symbol": self.ticker,
            "shortName": i.get("shortName"),
            "longName": i.get("longName"),
            "sector": i.get("sector"),
            "industry": i.get("industry"),
            "currency": i.get("currency"),
            "country": i.get("country"),
            "exchange": i.get("exchange"),
            "website": i.get("website"),
        }
        return fields

    def close_history(self, period: str = "5y", interval: str = "1d") -> pd.Series:
        """Get adjusted close series for given period/interval."""
        try:
            h = self._tkr.history(period=period, interval=interval, auto_adjust=True)
            s = h.get("Close", pd.Series(dtype=float)).dropna()
            s.name = self.ticker
            return s
        except Exception:
            return pd.Series(dtype=float, name=self.ticker)

    def daily_returns(self, period: str = "5y") -> pd.Series:
        """Daily returns from adjusted close."""
        s = self.close_history(period=period, interval="1d")
        return s.pct_change().dropna()

    # ---------- Market / CAPM helpers ----------
    @staticmethod
    def market_close(period: str = "5y", interval: str = "1d", market_ticker: str = "^GSPC") -> pd.Series:
        m = yf.Ticker(market_ticker).history(period=period, interval=interval, auto_adjust=True)
        s = m.get("Close", pd.Series(dtype=float)).dropna()
        s.name = market_ticker
        return s

    @staticmethod
    def risk_free_rate_from_tnx() -> Optional[float]:
        """
        Approximate risk-free rate using ^TNX (10Y yield in % * 0.1).
        """
        try:
            tnx = yf.Ticker("^TNX").history(period="1mo")["Close"].dropna()
            return float(tnx.iloc[-1]) / 100.0
        except Exception:
            return None

    def capm_beta(self, market_ticker: str = "^GSPC", period: str = "5y") -> Optional[float]:
        """
        Estimate beta via OLS on daily returns (stock ~ market).
        """
        if not _HAVE_STATSMODELS:
            return None
        stock = self.close_history(period=period, interval="1d")
        market = self.market_close(period=period, market_ticker=market_ticker)
        rets = build_returns_aligned(stock, market)
        if rets.empty:
            return None
        X = sm.add_constant(rets["market"])
        try:
            model = sm.OLS(rets["stock"], X).fit()
            return float(model.params.get("market", np.nan))
        except Exception:
            return None

    def capm_expected_return(
        self,
        market_expected_return: Optional[float] = None,
        rf: Optional[float] = None,
        market_ticker: str = "^GSPC",
        period: str = "5y",
    ) -> Optional[float]:
        """
        E[R_i] = Rf + beta_i * (E[R_m] - Rf)
        - If market_expected_return not provided, estimate from last 5Y annual returns of ^GSPC.
        """
        if rf is None:
            rf = self.risk_free_rate_from_tnx()
        beta = self.capm_beta(market_ticker=market_ticker, period=period)
        if beta is None or rf is None:
            return None

        if market_expected_return is None:
            sp = yf.Ticker(market_ticker).history(period="5y")["Close"]
            sp_y = sp.resample("Y").last().pct_change().dropna()
            if sp_y.empty:
                return None
            market_expected_return = float(sp_y.mean())

        return float(rf + beta * (market_expected_return - rf))

    # ---------- Interop hooks for your friend’s optimizer ----------
    def export_daily_returns(self, period: str = "5y") -> pd.Series:
        """Alias for compatibility with optimization pipeline."""
        return self.daily_returns(period=period)


@dataclass
class Position(Candidate):
    """
    Subclass representing a holding with transactions (lots).
    - purchase(): add a lot (qty, price, timestamp)
    - realized/unrealized PnL
    - @classmethod total_profit(): aggregate unrealized + realized across all Position instances
    """
    lots: List[Tuple[float, int, dt.datetime]] = field(default_factory=list)  # (price, qty, time)
    realized_pnl: float = 0.0

    # Class-level registry of all Position instances for aggregation
    _registry: List["Position"] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        super().__post_init__()
        # register instance
        type(self)._registry.append(self)

    # ---------- Trading ops ----------
    def purchase(self, qty: int, price: Optional[float] = None, when: Optional[dt.datetime] = None):
        """
        Record a buy. If price not given, uses current market price.
        """
        if qty <= 0:
            raise ValueError("qty must be positive")

        if price is None:
            price = self.current_price()
        if price is None:
            raise RuntimeError("Could not fetch current price; provide price explicitly.")

        when = when or _safe_now_utc()
        self.lots.append((float(price), int(qty), when))

    def sell(self, qty: int, price: Optional[float] = None, when: Optional[dt.datetime] = None):
        """
        Optional feature: record a sell using FIFO; realizes PnL.
        """
        if qty <= 0:
            raise ValueError("qty must be positive")

        if price is None:
            price = self.current_price()
        if price is None:
            raise RuntimeError("Could not fetch current price; provide price explicitly.")

        remaining = qty
        new_lots: List[Tuple[float, int, dt.datetime]] = []
        for lot_price, lot_qty, lot_time in self.lots:
            if remaining == 0:
                new_lots.append((lot_price, lot_qty, lot_time))
                continue
            take = min(remaining, lot_qty)
            self.realized_pnl += (float(price) - lot_price) * take
            leftover = lot_qty - take
            if leftover > 0:
                new_lots.append((lot_price, leftover, lot_time))
            remaining -= take
        if remaining > 0:
            raise ValueError("Not enough quantity to sell.")
        self.lots = new_lots

    # ---------- Analytics on the position ----------
    @property
    def quantity(self) -> int:
        return int(sum(q for _, q, _ in self.lots))

    @property
    def cost_basis(self) -> float:
        total_cost = sum(p * q for p, q, _ in self.lots)
        return float(total_cost)

    @property
    def average_cost(self) -> Optional[float]:
        qty = self.quantity
        if qty == 0:
            return None
        return self.cost_basis / qty

    def market_value(self, price: Optional[float] = None) -> float:
        if price is None:
            price = self.current_price()
        if price is None:
            return 0.0
        return float(price) * self.quantity

    def unrealized_pnl(self, price: Optional[float] = None) -> float:
        return self.market_value(price=price) - self.cost_basis

    def total_profit(self, price: Optional[float] = None) -> float:
        """
        Profit for THIS position: realized + unrealized.
        """
        return self.realized_pnl + self.unrealized_pnl(price=price)

    # ---------- Class-level aggregations ----------
    @classmethod
    def all_positions(cls) -> List["Position"]:
        # return only live instances (best-effort; simple container)
        return list(cls._registry)

    @classmethod
    def total_profit_all(cls, price_map: Optional[Dict[str, float]] = None) -> float:
        """
        Class method that calculates the total profit across all positions.
        If price_map provided (ticker -> price), uses those; otherwise fetches live prices.
        """
        total = 0.0
        for pos in cls._registry:
            p = price_map.get(pos.ticker) if price_map else None
            total += pos.total_profit(price=p)
        return float(total)

    # ---------- Interop  ----------
    def export_position_snapshot(self) -> Dict:
        """
        Minimal snapshot your teammate can log/store.
        """
        return {
            "ticker": self.ticker,
            "qty": self.quantity,
            "avg_cost": self.average_cost,
            "cost_basis": self.cost_basis,
            "market_value": self.market_value(),
            "unrealized_pnl": self.unrealized_pnl(),
            "realized_pnl": self.realized_pnl,
        }
