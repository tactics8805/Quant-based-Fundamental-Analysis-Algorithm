import requests
import pandas as pd
import numpy as np

# --- 1. Configuration ---

# !! IMPORTANT !!
# Get your free API key from https://www.alphavantage.co/support/#api-key
API_KEY = "YOUR_API_KEY_HERE" 

# --- Valuation Constants (Update these based on current market data) ---

# Current 10-Year Treasury Yield (as of Nov 2025)
# This is your Risk-Free Rate (Rf)
RISK_FREE_RATE = 0.0411 

# Expected long-term average S&P 500 return
# This is your Market Return (Rm)
EXPECTED_MARKET_RETURN = 0.09

# Standard terminal growth rate (long-term inflation proxy)
TERMINAL_GROWTH_RATE = 0.02


# --- 2. Helper Functions (Data Acquisition & Calculation) ---

def get_company_overview(ticker):
    """
    Fetches company overview data (Market Cap, P/E, EPS, Beta, etc.)
    """
    print(f"Fetching overview for {ticker}...")
    try:
        url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={API_KEY}'
        r = requests.get(url)
        r.raise_for_status() # Raises an error for bad responses (4xx or 5xx)
        data = r.json()
        if "Note" in data:
            print(f"API Limit Hit? Response: {data}")
            return None
        if not data:
            print(f"No overview data found for {ticker}.")
            return None
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching overview data: {e}")
        return None

def get_financial_statement(ticker, statement_type="INCOME_STATEMENT"):
    """
    Fetches financial statements (INCOME_STATEMENT, BALANCE_SHEET, CASH_FLOW).
    Returns the 'annualReports' section as a pandas DataFrame.
    """
    print(f"Fetching {statement_type} for {ticker}...")
    try:
        url = f'https://www.alphavantage.co/query?function={statement_type}&symbol={ticker}&apikey={API_KEY}'
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        
        if "Note" in data:
            print(f"API Limit Hit? Response: {data}")
            return None
            
        reports = data.get('annualReports', [])
        if not reports:
            print(f"No annual reports found for {statement_type} on {ticker}.")
            return None
            
        # Convert list of reports into a DataFrame
        df = pd.DataFrame(reports)
        # Set fiscalDateEnding as the index
        df.set_index('fiscalDateEnding', inplace=True)
        # Convert numeric columns, handling 'None' or '' strings
        for col in df.columns:
            if col != 'reportedCurrency':
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Sort by date, oldest to newest (important for CAGR and F-Score)
        return df.sort_index() 

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {statement_type} data: {e}")
        return None
    except (KeyError, TypeError) as e:
        print(f"Error processing {statement_type} data: {e}. Data received: {data}")
        return None

def _calculate_cagr(start_value, end_value, periods):
    """Helper function to calculate Compound Annual Growth Rate."""
    if start_value is None or end_value is None or start_value <= 0 or periods == 0:
        return None
    
    # (end/start)^(1/periods) - 1
    return (end_value / start_value) ** (1 / periods) - 1


# --- 3. The Main Analyzer Class ---

class FundamentalAnalyzer:
    def __init__(self, ticker):
        self.ticker = ticker
        self.overview = None
        self.income_statement = None
        self.balance_sheet = None
        self.cash_flow = None
        self.ratios = {} # Dictionary to store all calculated metrics

    def fetch_all_data(self):
        """
        Orchestrator method to fetch all required data.
        """
        print(f"--- Starting Analysis for {self.ticker} ---")
        self.overview = get_company_overview(self.ticker)
        self.income_statement = get_financial_statement(self.ticker, "INCOME_STATEMENT")
        self.balance_sheet = get_financial_statement(self.ticker, "BALANCE_SHEET")
        self.cash_flow = get_financial_statement(self.ticker, "CASH_FLOW")
        print("--- Data Fetching Complete ---")

    def calculate_ratios(self):
        """
        Calculate key ratios from the latest data.
        """
        if self.overview is None or self.income_statement is None or self.balance_sheet is None:
            print("Cannot calculate ratios. Fetch data first.")
            return

        print("Calculating basic ratios...")
        try:
            # --- Valuation Ratios (from Overview) ---
            self.ratios['P/E_Ratio'] = float(self.overview.get('PERatio', 'N/A'))
            self.ratios['P/B_Ratio'] = float(self.overview.get('PriceToBookRatio', 'N/A'))
            self.ratios['P/S_Ratio'] = float(self.overview.get('PriceToSalesRatioTTM', 'N/A'))
            self.ratios['Dividend_Yield'] = float(self.overview.get('DividendYield', 'N/A'))

            # --- Profitability Ratios (using latest annual report) ---
            latest_income = self.income_statement.iloc[-1]
            latest_balance = self.balance_sheet.iloc[-1]
            
            net_income = latest_income.get('netIncome')
            total_revenue = latest_income.get('totalRevenue')
            total_shareholder_equity = latest_balance.get('totalShareholderEquity')
            
            if net_income and total_revenue:
                self.ratios['Net_Profit_Margin'] = net_income / total_revenue
            
            if net_income and total_shareholder_equity:
                self.ratios['Return_on_Equity (ROE)'] = net_income / total_shareholder_equity

            # --- Solvency Ratios (using latest annual report) ---
            total_debt = latest_balance.get('longTermDebt', 0) + latest_balance.get('shortTermDebt', 0)
            
            if total_debt and total_shareholder_equity:
                self.ratios['Debt_to_Equity'] = total_debt / total_shareholder_equity

            print("Basic ratios calculated.")
        except Exception as e:
            print(f"Error calculating basic ratios: {e}")

    def calculate_piotroski_f_score(self):
        """
        Calculates the Piotroski F-Score (0-9) for financial strength.
        This requires at least 2-3 years of annual data.
        """
        if self.income_statement is None or self.balance_sheet is None or self.cash_flow is None:
            print("Cannot calculate F-Score. Fetch data first.")
            return

        if len(self.income_statement) < 3 or len(self.balance_sheet) < 3 or len(self.cash_flow) < 1:
            print(f"Cannot calculate F-Score. Not enough historical data (need 3+ years). Found {len(self.income_statement)} years.")
            return

        print("Calculating Piotroski F-Score...")
        try:
            # Get latest (T) and previous (T-1) reports
            inc_T = self.income_statement.iloc[-1]
            inc_T_1 = self.income_statement.iloc[-2]
            
            bs_T = self.balance_sheet.iloc[-1]
            bs_T_1 = self.balance_sheet.iloc[-2]
            bs_T_2 = self.balance_sheet.iloc[-3] # Need T-2 for average assets
            
            cf_T = self.cash_flow.iloc[-1]

            score = 0
            
            # --- PROFITABILITY ---
            
            # 1. Positive Net Income
            net_income_T = inc_T.get('netIncome')
            if net_income_T and net_income_T > 0:
                score += 1

            # 2. Positive Operating Cash Flow
            op_cash_flow_T = cf_T.get('operatingCashflow')
            if op_cash_flow_T and op_cash_flow_T > 0:
                score += 1
            
            # 3. Higher Return on Assets (ROA)
            avg_assets_T = (bs_T.get('totalAssets') + bs_T_1.get('totalAssets')) / 2
            avg_assets_T_1 = (bs_T_1.get('totalAssets') + bs_T_2.get('totalAssets')) / 2
            
            if avg_assets_T > 0 and avg_assets_T_1 > 0:
                roa_T = net_income_T / avg_assets_T
                roa_T_1 = inc_T_1.get('netIncome') / avg_assets_T_1
                if roa_T > roa_T_1:
                    score += 1

            # 4. Cash Flow > Net Income (Accruals)
            if op_cash_flow_T and net_income_T and op_cash_flow_T > net_income_T:
                score += 1

            # --- LEVERAGE, LIQUIDITY & SOURCE OF FUNDS ---
            
            # 5. Lower Long-Term Debt Ratio
            debt_ratio_T = bs_T.get('longTermDebt') / bs_T.get('totalAssets')
            debt_ratio_T_1 = bs_T_1.get('longTermDebt') / bs_T_1.get('totalAssets')
            if debt_ratio_T < debt_ratio_T_1:
                score += 1

            # 6. Higher Current Ratio
            current_ratio_T = bs_T.get('totalCurrentAssets') / bs_T.get('totalCurrentLiabilities')
            current_ratio_T_1 = bs_T_1.get('totalCurrentAssets') / bs_T_1.get('totalCurrentLiabilities')
            if current_ratio_T > current_ratio_T_1:
                score += 1

            # 7. No New Shares Issued (Dilution)
            shares_T = bs_T.get('commonStock')
            shares_T_1 = bs_T_1.get('commonStock')
            if shares_T <= shares_T_1:
                score += 1

            # --- OPERATING EFFICIENCY ---

            # 8. Higher Gross Margin
            margin_T = inc_T.get('grossProfit') / inc_T.get('totalRevenue')
            margin_T_1 = inc_T_1.get('grossProfit') / inc_T_1.get('totalRevenue')
            if margin_T > margin_T_1:
                score += 1

            # 9. Higher Asset Turnover Ratio
            turnover_T = inc_T.get('totalRevenue') / avg_assets_T
            turnover_T_1 = inc_T_1.get('totalRevenue') / avg_assets_T_1
            if turnover_T > turnover_T_1:
                score += 1

            print(f"Piotroski F-Score: {score}")
            self.ratios['Piotroski_F_Score'] = score
            return score
            
        except Exception as e:
            print(f"Error calculating F-Score: {e}. Data might be missing.")
            return None

    def calculate_historical_growth(self, years=5):
        """
        Calculates historical CAGR for key metrics.
        """
        if self.income_statement is None or len(self.income_statement) < 2:
            print("Not enough income statement data for growth calculation.")
            return
        
        print(f"Calculating historical growth ({years}Y)...")

        # Ensure we don't try to go back further than we have data
        actual_periods = min(years, len(self.income_statement) - 1)
        
        if actual_periods == 0:
             print("Not enough data for CAGR (need min 2 points).")
             return

        try:
            # Get the first and last data points from the available range
            start_report = self.income_statement.iloc[-1 - actual_periods]
            end_report = self.income_statement.iloc[-1]
            
            # --- Revenue Growth ---
            start_revenue = start_report.get('totalRevenue')
            end_revenue = end_report.get('totalRevenue')
            
            revenue_cagr = _calculate_cagr(start_revenue, end_revenue, actual_periods)
            self.ratios[f'Revenue_CAGR_{actual_periods}Y'] = revenue_cagr

            # --- Net Income Growth ---
            start_net_income = start_report.get('netIncome')
            end_net_income = end_report.get('netIncome')
            
            net_income_cagr = _calculate_cagr(start_net_income, end_net_income, actual_periods)
            self.ratios[f'Net_Income_CAGR_{actual_periods}Y'] = net_income_cagr
            
            print("Historical growth calculated.")

        except Exception as e:
            print(f"Error calculating historical growth: {e}")

    def calculate_cost_of_equity_capm(self, risk_free_rate, market_return):
        """
        Calculates the Cost of Equity using the Capital Asset Pricing Model (CAPM).
        k_e = Rf + B * (Rm - Rf)
        """
        if self.overview is None:
            print("Cannot calculate CAPM. Fetch overview data first.")
            return None
        
        print("Calculating Cost of Equity (CAPM)...")
        try:
            beta_str = self.overview.get('Beta')
            if beta_str is None or beta_str == 'N/A':
                print("Beta not found. Cannot calculate CAPM.")
                return None
                
            beta = float(beta_str)
            
            cost_of_equity = risk_free_rate + beta * (market_return - risk_free_rate)
            
            print(f"  CAPM Inputs: Rf={risk_free_rate:.4f}, B={beta:.4f}, Rm={market_return:.4f}")
            print(f"  Cost of Equity (k_e): {cost_of_equity:.4f}")
            
            self.ratios['Cost_of_Equity (CAPM)'] = cost_of_equity
            return cost_of_equity

        except Exception as e:
            print(f"Error calculating CAPM: {e}")
            return None

    def run_simple_dcf(self, growth_rate, wacc, terminal_growth):
        """
        Runs a very simplified 5-year Discounted Cash Flow (DCF) model.
        """
        if self.cash_flow is None or self.balance_sheet is None or self.overview is None:
            print("Cannot run DCF. Fetch all data first.")
            return None

        print(f"\n--- Running Simplified DCF ---")
        print(f"Assumptions: Growth={growth_rate:.4f}, WACC={wacc:.4f}, Terminal Growth={terminal_growth:.4f}")

        try:
            # Get the most recent Free Cash Flow (FCF)
            latest_cf = self.cash_flow.iloc[-1]
            op_cash_flow = latest_cf.get('operatingCashflow')
            cap_ex = latest_cf.get('capitalExpenditures')
            
            if op_cash_flow is None or cap_ex is None:
                print("Could not find 'operatingCashflow' or 'capitalExpenditures'.")
                return None

            last_fcf = op_cash_flow - abs(cap_ex) # CapEx is often negative
            print(f"  Last FCF: {last_fcf / 1e6:.2f}M")

            # Project FCF for 5 years
            projected_fcf = []
            for i in range(1, 6):
                fcf = last_fcf * ((1 + growth_rate) ** i)
                projected_fcf.append(fcf)

            # Calculate Terminal Value (Perpetuity Growth Model)
            terminal_value = (projected_fcf[-1] * (1 + terminal_growth)) / (wacc - terminal_growth)
            
            # Discount all future cash flows
            discounted_values = []
            for i, fcf in enumerate(projected_fcf):
                dfcf = fcf / ((1 + wacc) ** (i + 1))
                discounted_values.append(dfcf)
            
            d_terminal_value = terminal_value / ((1 + wacc) ** 5)
            
            # Enterprise Value = Sum of discounted FCFs + Discounted Terminal Value
            enterprise_value = sum(discounted_values) + d_terminal_value

            # Calculate Equity Value = Enterprise Value - Net Debt
            latest_balance = self.balance_sheet.iloc[-1]
            total_debt = latest_balance.get('longTermDebt', 0) + latest_balance.get('shortTermDebt', 0)
            cash = latest_balance.get('cashAndCashEquivalentsAtCarryingValue', 0)
            net_debt = total_debt - cash
            
            equity_value = enterprise_value - net_debt
            
            shares_outstanding = self.overview.get('SharesOutstanding')
            if shares_outstanding is None or int(shares_outstanding) == 0:
                print("Could not find SharesOutstanding.")
                return None
                
            shares_outstanding = int(shares_outstanding)
            implied_share_price = equity_value / shares_outstanding

            print(f"  Enterprise Value: {enterprise_value:,.2f}")
            print(f"  Net Debt: {net_debt:,.2f}")
            print(f"  Equity Value: {equity_value:,.2f}")
            print(f"  Shares Outstanding: {shares_outstanding:,}")
            print(f"  IMPLIED SHARE PRICE: {implied_share_price:.2f}")

            return {
                "implied_share_price": implied_share_price,
                "equity_value": equity_value,
                "enterprise_value": enterprise_value
            }
            
        except Exception as e:
            print(f"Error during DCF calculation: {e}")
            return None

    def display_results(self):
        """
        Prints a summary of all collected data and calculated ratios.
        """
        if not self.overview:
            print(f"No data for {self.ticker}. Run fetch_all_data() first.")
            return
            
        print("\n" + "="*50)
        print(f"      ANALYSIS SUMMARY: {self.ticker} ({self.overview.get('Name')})")
        print("="*50)
        print(f"Sector: {self.overview.get('Sector', 'N/A')}")
        print(f"Industry: {self.overview.get('Industry', 'N/A')}")
        
        print("\n--- Key Metrics (from Overview) ---")
        print(f"Market Cap: {int(self.overview.get('MarketCapitalization', 0)):,}")
        print(f"EPS: {self.overview.get('EPS', 'N/A')}")
        print(f"Beta: {self.overview.get('Beta', 'N/A')}")

        print("\n--- Quantitative Models & Ratios ---")
        if self.ratios:
            for key, value in self.ratios.items():
                if isinstance(value, (float, np.floating)):
                    print(f"{key}: {value:.4f}")
                else:
                    print(f"{key}: {value}")
        else:
            print("No ratios calculated. Run calculations first.")
        
        print("="*50 + "\n")


# --- 4. Main Execution ---

if __name__ == "__main__":
    
    # --- 1. SET UP ANALYSIS ---
    ticker_to_analyze = "AAPL" # Change this to any ticker
    analyzer = FundamentalAnalyzer(ticker_to_analyze)
    
    # --- 2. FETCH DATA ---
    analyzer.fetch_all_data()
    
    # --- 3. RUN ALL QUANTITATIVE MODELS ---
    analyzer.calculate_ratios()
    analyzer.calculate_piotroski_f_score()
    analyzer.calculate_historical_growth(years=5)
    
    # This model uses the constants from the top of the file
    cost_of_equity = analyzer.calculate_cost_of_equity_capm(
        risk_free_rate=RISK_FREE_RATE, 
        market_return=EXPECTED_MARKET_RETURN
    )
    
    # --- 4. DISPLAY RESULTS ---
    analyzer.display_results()

    # --- 5. RUN DATA-DRIVEN VALUATION (DCF) ---
    
    # Get the calculated growth rate, with a fallback
    growth_rate_5y = analyzer.ratios.get('Revenue_CAGR_5Y')
    if growth_rate_5y is None or growth_rate_5y <= 0:
        print("Warning: Using fallback growth rate.")
        growth_rate_5y = 0.08 # Fallback
        
    # Use our calculated cost of equity as the discount rate
    if cost_of_equity is None:
        print("Warning: Using fallback WACC.")
        cost_of_equity = 0.09 # Fallback
    
    analyzer.run_simple_dcf(
        growth_rate=growth_rate_5y,
        wacc=cost_of_equity, # Using k_e as a proxy for WACC
        terminal_growth=TERMINAL_GROWTH_RATE
    )