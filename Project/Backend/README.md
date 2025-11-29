# Portfolio Optimizer
We have developed a portfolio optimizer. The program asks the user to input the intended stocks they want to invest in. We are calculating the expected return of each of their stocks, and giving the optimized suggestion on how to allocate their asset. We see a significant improvement in the annual return and Sharpe ratio with the optimized distribution of assets.

-------
## Features 

- Calculates the Annual Expected Return of stock *i* using CAPM
- Calculates the actual Compound Annual Growth Rate of stock *i* with historical data
- Visualizes the given stock's close price in 5 years with 20-day MA line
- Optimizes portfolio allocation and outputs the percentage of asset's distribution under different strategies

## Notes
- Historical data means data from 5 years
- You can input multiple stocks, one at a time, and it prints the return for each stock you input.
- Rf: using the U.S. 10-year Treasury annual return
- Rm: using S&P 500 index annual return

## Dependencies
- pip

- Node.js
https://nodejs.org/en/download/prebuilt-installer

## Get Started

You have to run BOTH Backend and Frontend commands to use our tool!
Open the first terminal to run Backend:
```bash

git clone "https://github.com/CS196Illinois/FA25-Group12.git"

cd FA25-Group12/Project/Backend
python -m pip install -r requirements.txt
python -m uvicorn version2:app --reload --port 8000
```
Open another terminal to run Frontend:
```bash
cd FA25-Group12/Project/Frontend/src/my-react-app
npm install
npm start
```

## Note for foreign stocks

When you enter a stock that’s outside the U.S. market, append the region/market to the end of its ticker. 
Example: Tencent(Tencent is listed in Hong Kong) → 0700.HK, Sony → 6758.T, whereas U.S. stocks like Apple stay AAPL.


## Reference

Capital Asset Pricing Model (CAPM), calculating the expected return of an asset by assessing its risk compared to the overall market.

$$
{\Large E(R_i) = R_f + \beta (R_m - R_f)}
$$


- E(Ri): The Expected Return of Stock i

- Rf: Risk-free Return

- Rm: Expected Market Return

- beta: Stock's Sensitivity to the market


Modern Portfolio Theory (MPT), balancing the tradeoff between expected return and risk (volatility) in a portfolio of assets.












