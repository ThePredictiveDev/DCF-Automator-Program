# DCF Automator Program

## Overview
This project is an Automated Discounted Cash Flow (DCF) Calculator designed to streamline the process of evaluating the intrinsic value of a stock. It fetches financial data from Yahoo Finance, projects future cash flows, and calculates the present value to determine whether a stock is undervalued, fairly valued, or overvalued.

## Key Features

- **Automated Data Fetching:** Pulls financial statements (Income Statement, Balance Sheet, and Cash Flow Statement) from Yahoo Finance using the `yfinance` library.
- **Growth Rate Calculation:** Dynamically calculates historical growth rates for multiple financial terms over the past five years.
- **Free Cash Flow Projections:** Projects Free Cash Flow to the Firm (FCFF) for the next six years using individual growth rates for revenue, COGS, SG&A, R&D, etc.
- **Valuation Assessment:** Calculates the Weighted Average Cost of Capital (WACC), Terminal Value, and Discounted Cash Flow (DCF) to determine the enterprise value and equity value per share. Compares the intrinsic value to the current stock price to assess valuation.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Inputs Required](#inputs-required)
- [Outputs](#outputs)
- [Contributing](#contributing)
- [License](#license)

## Installation
**Prerequisites**
Ensure you have Python 3.7+ installed on your system.

**Clone the Repository**
```bash
git clone https://github.com/your-username/dcf-calculator.git
cd dcf-calculator
```

**Install Required Packages**
```bash
pip install -r requirements.txt
```

The key dependencies include:
- pandas
- numpy
- yfinance
- scikit-learn

## Usage

**Running the Script**
To run the script, use the following command in your terminal:

```bash
python dcf_calculator.py
```

## Inputs Required 
The script will prompt you to input the following parameters:

- **Stock Ticker**: The ticker symbol of the company as listed on Yahoo Finance.
- **Home Country**: The country in which the company is primarily based.
- **Market Index**: The market index ticker symbol (e.g., S&P 500, NASDAQ).
- **Tax Rate**: The applicable tax rate for the company.
- **Other Financial Metrics**: If data fetching fails, you will be asked to input values like revenue, COGS, SG&A, R&D, Depreciation & Amortization, etc.
- **Valuation Parameters**: Market value of debt, market value of equity, implied equity risk premium, standard deviation of the bond market index, terminal growth rate, etc.

## Outputs
The script will output the following key metrics:

- **Calculated WACC**
- **Cost of Equity and Cost of Debt**
- **Beta of the stock**
- **Enterprise Value (EV)**
- **Equity Value**
- **Equity Value Per Share**
- **Valuation Rating (Undervalued, Fairly Valued, Overvalued)**

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new feature branch (git checkout -b feature-branch).
3. Commit your changes (git commit -m 'Add some feature').
4. Push to the branch (git push origin feature-branch).
5. Open a Pull Request.
6. Please ensure your changes are well-documented and include tests where applicable

## License
This project is licensed under the [MIT](https://opensource.org/license/mit) License.







