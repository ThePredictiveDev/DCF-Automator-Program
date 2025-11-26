# DCF Calculator - Quick Start Guide

## Installation

```bash
pip install -r requirements.txt
```

## Basic Usage

### Interactive Mode (Easiest)
```bash
python dcf_calculator.py --interactive
```

Follow the prompts to enter:
1. Stock ticker (e.g., AAPL)
2. Market index (e.g., ^GSPC for S&P 500)
3. Country name
4. Financial data (auto-fetched from Yahoo Finance)
5. Market parameters

### Example Session

```
Enter stock ticker (e.g., AAPL): AAPL
Enter market index ticker (e.g., ^GSPC for S&P 500): ^GSPC
Enter company's home country: United States

Fetching financial data from Yahoo Finance...
Successfully fetched financial data!
Revenue: $394328.00M
EBIT: $123136.00M
Total Debt: $111088.00M
Cash: $73100.00M

Use manual override for any values? (Y/N): N

Tax Rate (%): 21
Market Value of Debt: 100000
Market Value of Equity: 3000000
...
```

## Output Files

- **dcf_report.csv**: Structured CSV file with all metrics
- **dcf_calculator.log**: Detailed execution log

## Key Outputs

The calculator provides:
- Intrinsic value per share
- Valuation status (Undervalued/Fairly Valued/Overvalued)
- Margin of safety percentage
- WACC, Cost of Equity, Cost of Debt
- Beta and credit rating
- Enterprise value and equity value
- 5-year FCFF projections
- Terminal value

## Tips

1. **Market Index Tickers**:
   - S&P 500: ^GSPC
   - NASDAQ: ^IXIC
   - Dow Jones: ^DJI
   - FTSE 100: ^FTSE
   - DAX: ^GDAXI

2. **Terminal Growth Rate**:
   - Large cap: 2-3%
   - Mid cap: 3-4%
   - Small cap: 4-5%

3. **Equity Risk Premium**:
   - Typically 5-6% for developed markets
   - Higher for emerging markets

4. **Tax Rate**:
   - US: 21% (federal corporate rate)
   - Adjust for state taxes if applicable

## Troubleshooting

**Issue**: "No data available for ticker"
- **Solution**: Verify ticker symbol on Yahoo Finance
- Use manual input mode if auto-fetch fails

**Issue**: "Insufficient data for beta calculation"
- **Solution**: Ensure market index ticker is correct
- Calculator will use default beta=1.0

**Issue**: "Terminal growth >= WACC"
- **Solution**: Reduce terminal growth rate
- Calculator automatically adjusts if needed

## Support

Check the log file `dcf_calculator.log` for detailed error messages and execution trace.
