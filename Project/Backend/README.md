# Calculating Expected Annual Return Using CAPM Model 
We have written out the code for calculating the expected return. Feel free to run the code and input the stocks you want.

-------

$$
{\Large E(R_i) = R_f + \beta (R_m - R_f)}
$$


E(Ri): The Expected Return of Stock i

Rf: Risk-free Return

Rm: Expected Market Return

beta: Stock's Sensitivity to the market

## Features 

- Calculating the Annual Expected Return of stock *i* using CAPM
- Calculating the actual Compound Annual Growth Rate of stock *i* with historical data

## Notes
- Historical data means data from 5 years
- You can input multiple stocks, one at a time, and it prints the return for each stock you input.
- Rf: using the U.S. 10-year Treasury annual return
- Rm: using S&P 500 index annual return

## How to use

We have written the Python program for the model. Simply download the file and input the stock ticker you want to calculate.
When you enter a stock that’s outside the U.S. market, append the region/market to the end of its ticker. 
Example: Tencent(Tencent is listed in Hong Kong) → 0700.HK, Sony → 6758.T, whereas U.S. stocks like Apple stay AAPL.

## Code
[version2](https://github.com/CS196Illinois/FA25-Group12/blob/master/Project/Backend/version2.py)





