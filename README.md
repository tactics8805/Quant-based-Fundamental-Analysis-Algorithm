# Quant-based-Fundamental-Analysis-Algorithm
Quantitative Stock Analyzer
This is a command-line Python script for performing quantitative fundamental analysis on a given stock ticker. It fetches financial data from the Alpha Vantage API and runs a suite of automated models to generate a financial health score and an intrinsic valuation.

📜 Description

This script moves beyond simple ratio lookups by implementing several well-known quantitative models. Instead of relying on subjective "assumptions" for valuation, it calculates key inputs (like the discount rate and growth rate) based on historical data and financial theory.

The analysis is performed by the FundamentalAnalyzer class, which:

Fetches all necessary financial statements.

Calculates key financial ratios.

Runs quantitative models (Piotroski, CAPM).

Calculates historical growth trends.

Runs a data-driven valuation (DCF).

✨ Features

Financial Statement Fetching: Pulls annual Income Statements, Balance Sheets, and Cash Flow Statements.

Key Ratio Analysis: Calculates standard metrics like P/E, P/B, ROE, and Debt-to-Equity.

Piotroski F-Score: Implements the 9-point Piotroski F-Score model to grade a company's financial strength (Profitability, Leverage, and Operating Efficiency).

Historical Growth (CAGR): Automatically calculates the 5-year Compound Annual Growth Rate (CAGR) for revenue and net income.

CAPM Discount Rate: Calculates the Cost of Equity using the Capital Asset Pricing Model (CAPM) to determine a data-driven discount rate (WACC proxy).

Data-Driven DCF Valuation: Runs a 5-year Discounted Cash Flow (DCF) model where the growth rate and discount rate are derived from the script's own calculations (CAGR and CAPM), not hard-coded guesses.

🚀 Getting Started

1. Prerequisites
Python 3.x

The following Python libraries: requests, pandas, numpy

2. Installation
Save the Code: Save the script as analysis.py (or any name you prefer).

Install Dependencies: Open your terminal and install the required libraries using pip:

Bash

pip install requests pandas numpy
3. Setup: The API Key
This script will not work without an API key.

Go to Alpha Vantage and claim your free API key.

Open the analysis.py script in your code editor.

Find this line at the top of the script:

Python

API_KEY = "YOUR_API_KEY_HERE"
Replace "YOUR_API_KEY_HERE" with the key you just received.

⚙️ How to Use
1. Configure Analysis (Optional)
At the top of the script, you can adjust the global constants used in the valuation models:

Python

# Current 10-Year Treasury Yield (Risk-Free Rate)
RISK_FREE_RATE = 0.0411 

# Expected long-term average S&P 500 return (Market Return)
EXPECTED_MARKET_RETURN = 0.09
The RISK_FREE_RATE changes daily. You should update this for the most accurate CAPM calculation. You can find the latest value by searching for "current 10-year treasury yield."

2. Set the Ticker
Scroll to the very bottom of the script to find the if __name__ == "__main__": block.

Change the ticker_to_analyze variable to the stock you want to analyze:

Python

# --- 1. SET UP ANALYSIS ---
ticker_to_analyze = "MSFT" # Change this to any ticker (e.g., "GOOGL", "JPM")
3. Run the Script
Open your terminal and navigate to the directory where you saved analysis.py.

Run the script:

Bash

python analysis.py
The script will print its progress as it fetches data, runs calculations, and will finally output a consolidated summary report and the results of the DCF valuation to your console.

⚠️ Disclaimers and Limitations
NOT FINANCIAL ADVICE: This script is for educational and informational purposes only. The output is not financial advice. All financial models are flawed approximations of reality. Do not make investment decisions based solely on this tool.

API LIMITS: The free Alpha Vantage API key is limited (e.g., 5 calls per minute, 500 per day). If you analyze a stock, you may need to wait a minute before analyzing another one.

DATA QUALITY: The models are 100% dependent on the data provided by the API. Free data can sometimes be incomplete or inaccurate. "Garbage in, garbage out."

MODEL SIMPLICITY: The DCF and CAPM models are simplified. A full-scale analysis would involve a more complex Weighted Average Cost of Capital (WACC) calculation, sensitivity analysis, and more nuanced growth projections.
