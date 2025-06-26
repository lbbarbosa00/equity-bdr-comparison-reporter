# =========================================================================================================
#                                    BDR vs. Original Stock - Reporter
# =========================================================================================================
#
# Objetivo: Download market data to compare the price variation of BDRs (Brazilian Depositary Receipts)
#           with their original stocks by calculating the theoretical price and divergence (if applicable). 
#
# Bibliotecas necessárias:
#   pip install yfinance pandas matplotlib.pyplot
#
# =========================================================================================================

import pandas as pd # For data manipulation and analysis
import yfinance as yf # For downloading financial data from Yahoo Finance
import matplotlib.pyplot as plt # For plotting graphs
from matplotlib.backends.backend_pdf import PdfPages # For saving plots to a PDF file
import warnings 

# Suppress ignorable warnings from yfinance and pandas
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- 1. ASSET CONFIGURATION ---
# A list of dictionaries, where each dictionary holds the information for a company
# to be analyzed.
COMPANIES = [
    {
        "name": "Apple Inc.",
        "bdr_ticker": "AAPL34.SA",
        "stock_ticker": "AAPL",
        "conversion_factor": 20
    },
    {
        "name": "Microsoft Corporation",
        "bdr_ticker": "MSFT34.SA",
        "stock_ticker": "MSFT",
        "conversion_factor": 24
    },
    {
        "name": "Google (Alphabet Inc.)",
        "bdr_ticker": "GOGL34.SA",
        "stock_ticker": "GOOGL",
        "conversion_factor": 12
    },
    {
        "name": "Amazon Inc.",
        "bdr_ticker": "AMZO34.SA",
        "stock_ticker": "AMZN",
        "conversion_factor": 20
    },
    {
        "name": "NVIDIA Corporation",
        "bdr_ticker": "NVDC34.SA",
        "stock_ticker": "NVDA",
        "conversion_factor": 48
    }
]

ANALYSIS_PERIOD = "5y" # Period for which the data will be analyzed (5 years)
EXCHANGE_RATE_TICKER = "USDBRL=X" # Ticker for the exchange rate (USD to BRL)
PDF_FILENAME = "bdr_analysis_report_5y.pdf" # Name of the PDF file to save the plots

# --- 2. REPORT GENERATION LOGIC ---
print(f"--- STARTING BDR ANALYSIS & REPORT GENERATION ---")
print(f"A report named '{PDF_FILENAME}' will be created")

# Use 'with' statement to ensure the PDF file is properly saved and closed
with PdfPages (PDF_FILENAME) as pdf_report:
    for company in COMPANIES:
        company_name = company["name"]
        bdr_ticker = company["bdr_ticker"]
        stock_ticker = company["stock_ticker"]
        conversion_factor = company["conversion_factor"]

        print(f"\n[+] Processing: {company_name}")

        # --- 2.1. Data Fetching ---
        try:
            # Download data in a single call, more efficient call
            data = yf.download(
                [bdr_ticker, stock_ticker, EXCHANGE_RATE_TICKER],
                period=ANALYSIS_PERIOD,
                progress=False
            )['Close']
            data.columns = ['BDR_Price_BRL', 'Stock_Price_USD', 'Exchange_Rate_BRL']

            # Handle missing values (NaN) using ffill() approach
            if data.isnull().values.any():
                data.ffill(inplace=True) # Forward fill to handle missing values
                data.dropna(inplace=True) # Drop any remaining NaN values

            if data.empty:
                print(f"    [!] No data available for {company_name} after cleaning. Skipping...")
                continue

        except Exception as e:
            print(f"    [!] An error occurred while fetching data: {e}")
            continue

        # --- 2.2. Calculation ---
        data['Theoretical_BDR_Price'] = (data['Stock_Price_USD'] * data['Exchange_Rate_BRL']) / conversion_factor
        data['Divergence_Percentage'] = ((data['BDR_Price_BRL'] / data['Theoretical_BDR_Price']) - 1) * 100

        last_divergence = data['Divergence_Percentage'].iloc[-1]
        print(f"    -> Most recent divergence: {last_divergence:.2f}%")
        print(f"    -> Generating PDF page...")

        # --- 2.3. Plotting and Saving to PDF ---
        # Create a figure with two subplots, sized for an A4 page
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.27, 11.69), constrained_layout=True, dpi=600)
        fig.suptitle(f'Analysis Report: {company_name} ({bdr_ticker}) - {ANALYSIS_PERIOD}', fontsize=16)

        # Subplot 1: Price Comparison
        ax1.plot(data.index, data['BDR_Price_BRL'], label='Actual BDR Price (BRL)')
        ax1.plot(data.index, data['Theoretical_BDR_Price'], label='Theoretical BDR Price (BRL)', linestyle='--')
        ax1.set_title('Price Comparison (BRL)')
        ax1.set_ylabel('Price (R$)')
        ax1.legend()
        ax1.grid(True, linestyle='--', alpha=0.6)

        # Subplot 2: Divergence Percentage
        ax2.plot(data.index, data['Divergence_Percentage'], label='Divergence', color='green')
        ax2.axhline(0, color='red', linestyle='--', linewidth=1) # Zero line for reference
        ax2.set_title('Divergence (Premium/Discount)')
        ax2.set_ylabel('Divergence (%)')
        ax2.set_xlabel('Date')
        ax2.grid(True, linestyle='--', alpha=0.6)

        # Save the full figure to a new page in our PDF report
        pdf_report.savefig(fig)

        # Close the figure after saving to free up memory
        plt.close(fig)

print(f"\n--- ANALYSIS COMPLETE ---")
print(f"Report '{PDF_FILENAME}' has been successfully created in your project folder.")