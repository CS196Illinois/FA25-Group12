# Group 12: Portfolio Optimizer

**Group Name:** Group 12

**MVP Link:** [https://majestic-kataifi-bac07d.netlify.app](https://majestic-kataifi-bac07d.netlify.app)

**Team Members:** Dligach2, Jingxil4, Ashwinp4, Zhuojun9, Davidk17, rongxiw2

**Project Manager:** pillai7

---

## Overview

A full-stack web application that optimizes investment portfolios using CAPM and Modern Portfolio Theory. The tool calculates expected returns, analyzes historical performance, and provides optimized asset allocation strategies to maximize returns while managing risk.

🌐 **Live Demo:** [https://majestic-kataifi-bac07d.netlify.app](https://majestic-kataifi-bac07d.netlify.app)

---

## Features 

- **CAPM Analysis:** Calculates Annual Expected Return using Capital Asset Pricing Model
- **Historical Performance:** Analyzes Compound Annual Growth Rate (CAGR) with 5 years of data
- **Portfolio Optimization:** Suggests optimal asset allocation using three strategies:
  - Max Sharpe Ratio
  - Minimum Variance
  - Target Return
- **Visualization:** Displays portfolio weights with interactive donut charts
- **Market Comparison:** Compares optimized portfolio vs. equal-weight baseline
- **Real-time Data:** Fetches live stock prices via yfinance API

---

## Tech Stack

**Frontend:**
- React, JavaScript, CSS
- Hosted on Netlify

**Backend:**
- Python, FastAPI, Uvicorn
- Hosted on Render

**Data & Computation:**
- yfinance (stock data)
- NumPy, SciPy (optimization algorithms)
- Pandas (data processing)

**DevOps:**
- Git/GitHub (version control)
- Environment variables (configuration)
- CORS (cross-origin security)

---

## Quick Start

### Option 1: Use Live Website (Recommended)

Simply visit: **[https://majestic-kataifi-bac07d.netlify.app](https://majestic-kataifi-bac07d.netlify.app)**

No installation required! The application is fully deployed and ready to use.

> **Note:** First request may take 30-50 seconds as the backend server wakes up from sleep (free tier limitation).

---

### Option 2: Run Locally

#### Prerequisites
- Python 3.13+
- Node.js 18+
- pip

#### Backend Setup

**macOS/Linux:**
```bash
git clone "https://github.com/CS196Illinois/FA25-Group12.git"
cd FA25-Group12/Project/Backend
python3 -m pip install -r requirements.txt
python3 -m uvicorn version2:app --reload --port 8000
```

**Windows:**
```cmd
git clone "https://github.com/CS196Illinois/FA25-Group12.git"
cd FA25-Group12\Project\Backend
python -m pip install -r requirements.txt
python -m uvicorn version2:app --reload --port 8000
```

Backend will run at: `http://localhost:8000`  
API docs available at: `http://localhost:8000/docs`

#### Frontend Setup

Open a **new terminal** and run:

**macOS/Linux:**
```bash
cd FA25-Group12/Project/Frontend/src/my-react-app
npm install
npm start
```

**Windows:**
```cmd
cd FA25-Group12\Project\Frontend\src\my-react-app
npm install
npm start
```

Frontend will open at: `http://localhost:3000`

---

## Usage

1. **Enter stock tickers** (e.g., AAPL, MSFT, NVDA)
2. **Select optimization mode:**
   - Max Sharpe: Maximize risk-adjusted returns
   - Min Variance: Minimize portfolio volatility
   - Target Return: Achieve specific return target
3. **Set parameters:**
   - Target Return (for Target Return mode)
   - Historical data period (default: 5 years)
4. **Click "Run Optimizer"**
5. **View results:**
   - Optimized portfolio weights
   - Expected return, volatility, Sharpe ratio
   - Comparison with equal-weight baseline

---

## International Stocks

For stocks outside the U.S. market, append the market suffix:

| Market | Suffix | Example |
|--------|--------|---------|
| Hong Kong | .HK | Tencent: `0700.HK` |
| Tokyo | .T | Sony: `6758.T` |
| London | .L | BP: `BP.L` |
| U.S. | (none) | Apple: `AAPL` |

---

## How It Works

### Capital Asset Pricing Model (CAPM)

Calculates expected return by assessing risk compared to the market:

$$E(R_i) = R_f + \beta (R_m - R_f)$$

Where:
- **E(Ri)**: Expected return of stock *i*
- **Rf**: Risk-free rate (U.S. 10-year Treasury)
- **Rm**: Market return (S&P 500)
- **β (beta)**: Stock's sensitivity to market movements

### Modern Portfolio Theory (MPT)

Optimizes the tradeoff between expected return and risk (volatility) by:
1. Calculating covariance matrix of returns
2. Solving constrained optimization problem
3. Finding optimal weights that maximize utility

---

## API Endpoints

**Base URL (Production):** `https://portfolio-optimizer-backend-66q4.onrender.com`

### `POST /api/optimize`

Optimize portfolio allocation.

**Request:**
```json
{
  "tickers": ["AAPL", "MSFT", "NVDA"],
  "mode": "max_sharpe",
  "target_return": 0.12,
  "history_years": 5
}
```

**Response:**
```json
{
  "weights": {
    "AAPL": 0.43,
    "MSFT": 0.39,
    "NVDA": 0.17
  },
  "stats": {
    "expected_return": 0.1795,
    "volatility": 0.2672,
    "sharpe": 0.519
  },
  "market_snapshot": "..."
}
```

### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-03T12:00:00"
}
```

---

## Architecture

```
User Browser
     ↓
[Netlify - React Frontend]
     ↓ HTTPS/JSON
[Render - FastAPI Backend]
     ↓
[yfinance API - Stock Data]
```

**Production URLs:**
- Frontend: `https://majestic-kataifi-bac07d.netlify.app`
- Backend: `https://portfolio-optimizer-backend-66q4.onrender.com`
- API Docs: `https://portfolio-optimizer-backend-66q4.onrender.com/docs`

---

## Development

### Environment Variables

**Frontend (.env):**
```bash
REACT_APP_API_URL=https://portfolio-optimizer-backend-66q4.onrender.com
```

For local development:
```bash
REACT_APP_API_URL=http://localhost:8000
```

### Building for Production

```bash
# Frontend
cd Frontend/src/my-react-app
npm run build

# Deploy build/ folder to Netlify
```

### Deployment

**Backend:**
- Push to GitHub → Automatic deployment to Render

**Frontend:**
- Build locally → Upload to Netlify
- Or connect GitHub repo for automatic deployment

---

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## References

- **Capital Asset Pricing Model (CAPM):** Sharpe, W. F. (1964)
- **Modern Portfolio Theory (MPT):** Markowitz, H. (1952)
- **yfinance:** Yahoo Finance data wrapper
- **FastAPI:** Modern Python web framework
- **React:** JavaScript UI library

---

## Team

CS 196 - Group 12  
University of Illinois Urbana-Champaign

---

## Acknowledgments

- Stock data provided by Yahoo Finance (yfinance)
- Optimization algorithms powered by SciPy
- Hosting provided by Render and Netlify (free tiers)

---

**Questions or Issues?**  
Open an issue on GitHub or contact the team.
