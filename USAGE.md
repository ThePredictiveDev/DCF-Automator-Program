# DCF Calculator - Usage Guide

## Quick Start

### Interactive Mode (Recommended)
```bash
python dcf_calculator.py --interactive
```

This will guide you through entering all required parameters step-by-step.

### Using Configuration File
1. Copy `config_example.json` to `config.json`
2. Edit `config.json` with your values
3. Run: `python dcf_calculator.py --config config.json --output report.csv`

## Required Inputs

### Basic Information
- **Stock Ticker**: Yahoo Finance ticker symbol (e.g., AAPL, MSFT)
- **Market Index**: Market index ticker (e.g., ^GSPC for S&P 500, ^IXIC for NASDAQ)
- **Country**: Company's home country

### Financial Data (Auto-fetched from Yahoo Finance)
- Total Revenue
- Cost of Goods Sold (COGS)
- SG&A Expenses
- R&D Expenses
- Depreciation & Amortization
- Current Assets
- Current Liabilities
- Cash & Cash Equivalents
- Total Debt
- Capital Expenditure
- EBIT
- Interest Expense

### Market Parameters
- **Tax Rate**: Corporate tax rate (as percentage, e.g., 21 for 21%)
- **Market Value of Debt**: Current market value of company's debt
- **Market Value of Equity**: Current market capitalization
- **Domestic Revenue %**: Percentage of revenue from home country
- **Sector Domestic Revenue %**: Average for the sector
- **S&P 500 Equity Risk Premium**: Typically 5-6%
- **Bond Market Std Dev**: Standard deviation of bond market returns
- **Longest Gov Bond Rate**: Longest-term government bond yield
- **Country Default Spread**: Country risk premium
- **Terminal Growth Rate**: Long-term growth assumption (typically 2-3%)

## Output

The calculator generates:
1. **Console Report**: Detailed text output with all key metrics
2. **CSV Report**: Structured data file (default: `dcf_report.csv`)
3. **Log File**: `dcf_calculator.log` with detailed execution logs

## Key Metrics Calculated

- **WACC** (Weighted Average Cost of Capital)
- **Cost of Equity**
- **Cost of Debt**
- **Beta** (calculated from historical returns)
- **Company Credit Rating** (based on interest coverage)
- **Enterprise Value**
- **Equity Value**
- **Intrinsic Value Per Share**
- **Valuation Status** (Undervalued/Fairly Valued/Overvalued)
- **Margin of Safety**

## Example

```bash
python dcf_calculator.py --interactive
```

Follow the prompts to enter:
- Ticker: AAPL
- Market Index: ^GSPC
- Country: United States
- Tax Rate: 21
- Market Value of Debt: 100000000000
- Market Value of Equity: 3000000000000
- ... (continue with remaining inputs)

## Error Handling

The calculator includes comprehensive error handling:
- Automatic retry for data fetching failures
- Validation of all inputs
- Fallback values for missing data
- Detailed logging for troubleshooting

## Notes

- All monetary values should be in the base currency (e.g., USD)
- The calculator automatically fetches financial data from Yahoo Finance
- Manual override is available if auto-fetch fails
- Beta is calculated using 5 years of historical data
- FCFF projections are made for 5 years with terminal value
