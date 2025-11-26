"""
Production-Ready DCF (Discounted Cash Flow) Calculator
Designed for investment banking professionals to perform accurate DCF valuations.
"""

import logging
import sys
import argparse
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yfinance as yf
from sklearn.linear_model import LinearRegression
import json
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dcf_calculator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class FinancialData:
    """Container for financial statement data."""
    total_revenue: float = 0.0
    cogs: float = 0.0
    sgna: float = 0.0
    rnd: float = 0.0
    depreciation_amortization: float = 0.0
    current_assets: float = 0.0
    current_liabilities: float = 0.0
    cash: float = 0.0
    total_debt: float = 0.0
    cap_ex: float = 0.0
    ebit: float = 0.0
    interest_expense: float = 0.0
    shares_outstanding: float = 0.0
    shares_issued: float = 0.0
    shares_repurchased: float = 0.0


@dataclass
class MarketData:
    """Container for market and valuation parameters."""
    stock_ticker: str = ""
    market_index: str = ""
    country: str = ""
    tax_rate: float = 0.0
    market_value_debt: float = 0.0
    market_value_equity: float = 0.0
    domestic_revenue_pct: float = 0.0
    sector_domestic_revenue_pct: float = 0.0
    equity_risk_premium_sp500: float = 0.0
    bond_market_stddev: float = 0.0
    longest_gov_bond_rate: float = 0.0
    country_default_spread: float = 0.0
    terminal_growth_rate: float = 0.0
    other_countries: List[Dict[str, float]] = field(default_factory=list)


@dataclass
class DCFResults:
    """Container for DCF calculation results."""
    beta: float = 0.0
    risk_free_rate: float = 0.0
    cost_of_equity: float = 0.0
    cost_of_debt: float = 0.0
    wacc: float = 0.0
    company_rating: str = ""
    company_default_spread: float = 0.0
    fcff_projections: List[float] = field(default_factory=list)
    terminal_value: float = 0.0
    enterprise_value: float = 0.0
    equity_value: float = 0.0
    equity_value_per_share: float = 0.0
    current_stock_price: float = 0.0
    valuation_status: str = ""
    margin_of_safety: float = 0.0


class DataFetcher:
    """Handles fetching financial data from Yahoo Finance with error handling."""
    
    def __init__(self, ticker: str, retry_count: int = 3):
        self.ticker = ticker.upper()
        self.retry_count = retry_count
        self.stock = None
        
    def fetch_data(self) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """Fetch balance sheet, income statement, and cash flow statement."""
        for attempt in range(self.retry_count):
            try:
                logger.info(f"Fetching data for {self.ticker} (attempt {attempt + 1}/{self.retry_count})")
                self.stock = yf.Ticker(self.ticker)
                
                balance_sheet = self.stock.balance_sheet
                income_statement = self.stock.financials
                cash_flow = self.stock.cashflow
                
                if balance_sheet is None or balance_sheet.empty:
                    raise ValueError(f"No balance sheet data available for {self.ticker}")
                if income_statement is None or income_statement.empty:
                    raise ValueError(f"No income statement data available for {self.ticker}")
                if cash_flow is None or cash_flow.empty:
                    raise ValueError(f"No cash flow data available for {self.ticker}")
                
                logger.info(f"Successfully fetched data for {self.ticker}")
                return balance_sheet, income_statement, cash_flow
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.retry_count - 1:
                    logger.error(f"Failed to fetch data for {self.ticker} after {self.retry_count} attempts")
                    return None, None, None
                continue
        
        return None, None, None
    
    def extract_financial_data(self, balance_sheet: pd.DataFrame, 
                               income_statement: pd.DataFrame,
                               cash_flow: pd.DataFrame) -> FinancialData:
        """Extract financial metrics from statements."""
        data = FinancialData()
        
        try:
            if not balance_sheet.empty:
                data.current_assets = self._safe_get(balance_sheet, 'Current Assets', 0)
                data.current_liabilities = self._safe_get(balance_sheet, 'Current Liabilities', 0)
                data.cash = self._safe_get(balance_sheet, 'Cash And Cash Equivalents', 0)
                data.total_debt = self._safe_get(balance_sheet, 'Total Debt', 0)
                
            if not income_statement.empty:
                data.total_revenue = self._safe_get(income_statement, 'Total Revenue', 0)
                data.cogs = self._safe_get(income_statement, 'Cost Of Revenue', 0)
                data.sgna = self._safe_get(income_statement, 'Selling General And Administration', 0)
                data.rnd = self._safe_get(income_statement, 'Research And Development', 0)
                data.ebit = self._safe_get(income_statement, 'EBIT', 0)
                data.interest_expense = self._safe_get(income_statement, 'Interest Expense', 0)
                
            if not cash_flow.empty:
                data.depreciation_amortization = self._safe_get(cash_flow, 'Reconciled Depreciation', 0)
                data.cap_ex = abs(self._safe_get(cash_flow, 'Capital Expenditure', 0))
                
            info = self.stock.info if self.stock else {}
            data.shares_outstanding = info.get('sharesOutstanding', 0) or info.get('impliedSharesOutstanding', 0) or 0
            
        except Exception as e:
            logger.error(f"Error extracting financial data: {str(e)}")
            
        return data
    
    def _safe_get(self, df: pd.DataFrame, key: str, default: float = 0.0) -> float:
        """Safely extract value from DataFrame."""
        try:
            if key in df.index:
                value = df.loc[key].iloc[0]
                if pd.isna(value) or value is None:
                    return default
                return float(value)
            return default
        except (KeyError, IndexError, ValueError, TypeError) as e:
            logger.warning(f"Could not extract {key}: {str(e)}")
            return default
    
    def fetch_stock_price(self) -> float:
        """Fetch current stock price."""
        try:
            hist = self.stock.history(period='1d')
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching stock price: {str(e)}")
            return 0.0
    
    def fetch_returns(self, market_index: str, years: int = 5) -> Tuple[Optional[pd.Series], Optional[pd.Series]]:
        """Fetch stock and market returns for beta calculation."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365)
            
            stock_data = yf.download(self.ticker, start=start_date, end=end_date, progress=False)
            market_data = yf.download(market_index, start=start_date, end=end_date, progress=False)
            
            if stock_data.empty or market_data.empty:
                logger.warning("Insufficient data for returns calculation")
                return None, None
            
            stock_returns = stock_data['Adj Close'].pct_change().dropna()
            market_returns = market_data['Adj Close'].pct_change().dropna()
            
            if len(stock_returns) < 30 or len(market_returns) < 30:
                logger.warning("Insufficient data points for beta calculation")
                return None, None
            
            return stock_returns, market_returns
            
        except Exception as e:
            logger.error(f"Error fetching returns: {str(e)}")
            return None, None


class FinancialCalculator:
    """Performs financial calculations for DCF analysis."""
    
    @staticmethod
    def calculate_beta(stock_returns: pd.Series, market_returns: pd.Series) -> float:
        """Calculate beta using linear regression."""
        try:
            if stock_returns is None or market_returns is None:
                return 1.0
            
            if len(stock_returns) < 30 or len(market_returns) < 30:
                logger.warning("Insufficient data for beta calculation, using default beta=1.0")
                return 1.0
            
            aligned = pd.DataFrame({
                'stock': stock_returns,
                'market': market_returns
            }).dropna()
            
            if len(aligned) < 30:
                logger.warning("Insufficient aligned data for beta calculation, using default beta=1.0")
                return 1.0
            
            model = LinearRegression()
            X = aligned['market'].values.reshape(-1, 1)
            y = aligned['stock'].values
            model.fit(X, y)
            beta = float(model.coef_[0])
            
            if beta <= 0 or beta > 5:
                logger.warning(f"Unusual beta value {beta:.2f}, capping at reasonable range")
                beta = max(0.1, min(3.0, beta))
            
            return beta
            
        except Exception as e:
            logger.error(f"Error calculating beta: {str(e)}")
            return 1.0
    
    @staticmethod
    def calculate_default_spread(ebit: float, interest_expense: float) -> Tuple[float, str]:
        """Calculate company default spread based on interest coverage ratio."""
        if interest_expense == 0 or ebit == 0:
            logger.warning("Cannot calculate default spread: zero interest expense or EBIT")
            return 2.0, "BB"
        
        interest_coverage = ebit / abs(interest_expense)
        
        rating_map = [
            (12.5, 0.59, "AAA"),
            (9.5, 0.70, "AA"),
            (7.5, 0.92, "A"),
            (6.0, 1.07, "A2"),
            (4.5, 1.21, "A3"),
            (4.0, 1.47, "BBB"),
            (3.5, 1.74, "BB+"),
            (3.0, 2.21, "BB"),
            (2.5, 3.14, "B"),
            (2.0, 3.61, "B2"),
            (1.5, 5.24, "B3"),
            (1.25, 8.51, "CCC"),
            (0.8, 11.78, "CC"),
            (0.5, 17.0, "C"),
        ]
        
        for threshold, spread, rating in rating_map:
            if interest_coverage > threshold:
                return spread, rating
        
        return 20.0, "D"
    
    @staticmethod
    def calculate_growth_rate(financial_data: pd.DataFrame, term: str, periods: int = 5) -> float:
        """Calculate average growth rate for a financial term."""
        try:
            if term not in financial_data.index:
                return 0.0
            
            values = financial_data.loc[term].iloc[:periods].values
            values = values[~pd.isna(values)]
            
            if len(values) < 2:
                return 0.0
            
            growth_rates = []
            for i in range(len(values) - 1):
                if values[i+1] != 0 and not pd.isna(values[i+1]):
                    growth = (values[i] - values[i+1]) / abs(values[i+1])
                    growth_rates.append(growth)
            
            if not growth_rates:
                return 0.0
            
            avg_growth = np.mean(growth_rates)
            
            if avg_growth > 1.0 or avg_growth < -0.5:
                logger.warning(f"Unusual growth rate {avg_growth:.2%} for {term}, capping")
                avg_growth = max(-0.5, min(0.5, avg_growth))
            
            return avg_growth
            
        except Exception as e:
            logger.error(f"Error calculating growth rate for {term}: {str(e)}")
            return 0.0
    
    @staticmethod
    def project_financials(current_value: float, growth_rate: float, years: int = 5) -> List[float]:
        """Project financial values over specified years."""
        projections = []
        for year in range(1, years + 1):
            projected = current_value * ((1 + growth_rate) ** year)
            projections.append(projected)
        return projections


class DCFCalculator:
    """Main DCF calculation engine."""
    
    def __init__(self, financial_data: FinancialData, market_data: MarketData):
        self.financial_data = financial_data
        self.market_data = market_data
        self.results = DCFResults()
        
    def calculate(self) -> DCFResults:
        """Perform complete DCF calculation."""
        try:
            logger.info("Starting DCF calculation")
            
            self._calculate_beta_and_rates()
            self._calculate_wacc()
            self._project_cash_flows()
            self._calculate_valuation()
            self._determine_valuation_status()
            
            logger.info("DCF calculation completed successfully")
            return self.results
            
        except Exception as e:
            logger.error(f"Error in DCF calculation: {str(e)}")
            raise
    
    def _calculate_beta_and_rates(self):
        """Calculate beta, risk-free rate, and cost components."""
        fetcher = DataFetcher(self.market_data.stock_ticker)
        stock_returns, market_returns = fetcher.fetch_returns(self.market_data.market_index)
        
        self.results.beta = FinancialCalculator.calculate_beta(stock_returns, market_returns)
        
        self.results.risk_free_rate = (
            self.market_data.longest_gov_bond_rate - self.market_data.country_default_spread
        ) / 100.0
        
        if self.results.risk_free_rate < 0:
            logger.warning("Negative risk-free rate calculated, using minimum 0.5%")
            self.results.risk_free_rate = 0.005
        
        company_default_spread, rating = FinancialCalculator.calculate_default_spread(
            self.financial_data.ebit,
            self.financial_data.interest_expense
        )
        self.results.company_default_spread = company_default_spread
        self.results.company_rating = rating
        
        logger.info(f"Beta: {self.results.beta:.4f}, Risk-free rate: {self.results.risk_free_rate:.4%}, Rating: {rating}")
    
    def _calculate_wacc(self):
        """Calculate Weighted Average Cost of Capital."""
        market_stddev = self.market_data.bond_market_stddev if self.market_data.bond_market_stddev > 0 else 0.15
        
        fetcher = DataFetcher(self.market_data.stock_ticker)
        _, market_returns = fetcher.fetch_returns(self.market_data.market_index)
        
        if market_returns is not None and len(market_returns) > 0:
            calculated_stddev = float(market_returns.std())
            if calculated_stddev > 0:
                market_stddev = calculated_stddev
        
        country_equity_risk_premium = (
            self.market_data.equity_risk_premium_sp500 / 100.0 +
            (self.market_data.country_default_spread / 100.0) * (market_stddev / max(self.market_data.bond_market_stddev, 0.01))
        )
        
        revenue_ratio = (
            self.market_data.domestic_revenue_pct / 
            max(self.market_data.sector_domestic_revenue_pct, 1.0)
        )
        
        company_equity_risk_premium = self.results.risk_free_rate + country_equity_risk_premium * revenue_ratio
        
        debt_equity_ratio = (
            self.market_data.market_value_debt / 
            max(self.market_data.market_value_equity, 1.0)
        )
        
        unlevered_beta = self.results.beta / (1 + (1 - self.market_data.tax_rate) * debt_equity_ratio)
        relevered_beta = unlevered_beta * (1 + (1 - self.market_data.tax_rate) * debt_equity_ratio)
        
        self.results.cost_of_equity = (
            self.results.risk_free_rate + 
            relevered_beta * (company_equity_risk_premium - self.results.risk_free_rate)
        )
        
        self.results.cost_of_debt = (
            self.results.risk_free_rate + 
            (self.market_data.domestic_revenue_pct / 100.0) * (self.market_data.country_default_spread / 100.0) +
            (self.results.company_default_spread / 100.0)
        )
        
        for other_country in self.market_data.other_countries:
            self.results.cost_of_debt += (
                (other_country['revenue_pct'] / 100.0) * (other_country['default_spread'] / 100.0)
            )
        
        if self.results.cost_of_debt < self.results.risk_free_rate:
            self.results.cost_of_debt = self.results.risk_free_rate + 0.01
        
        total_capital = self.market_data.market_value_debt + self.market_data.market_value_equity
        equity_weight = self.market_data.market_value_equity / max(total_capital, 1.0)
        debt_weight = self.market_data.market_value_debt / max(total_capital, 1.0)
        
        self.results.wacc = (
            self.results.cost_of_equity * equity_weight +
            self.results.cost_of_debt * (1 - self.market_data.tax_rate) * debt_weight
        )
        
        if self.results.wacc <= 0 or self.results.wacc > 1.0:
            logger.warning(f"Unusual WACC {self.results.wacc:.4f}, adjusting")
            self.results.wacc = max(0.05, min(0.30, self.results.wacc))
        
        logger.info(f"WACC: {self.results.wacc:.4%}, Cost of Equity: {self.results.cost_of_equity:.4%}, Cost of Debt: {self.results.cost_of_debt:.4%}")
    
    def _project_cash_flows(self):
        """Project free cash flows to the firm."""
        fetcher = DataFetcher(self.market_data.stock_ticker)
        balance_sheet, income_statement, cash_flow = fetcher.fetch_data()
        
        if income_statement is None or income_statement.empty:
            logger.warning("Cannot fetch income statement for growth rates, using defaults")
            revenue_growth = 0.05
            cogs_growth = 0.05
            sgna_growth = 0.03
            rnd_growth = 0.05
        else:
            revenue_growth = FinancialCalculator.calculate_growth_rate(income_statement, 'Total Revenue')
            cogs_growth = FinancialCalculator.calculate_growth_rate(income_statement, 'Cost Of Revenue')
            sgna_growth = FinancialCalculator.calculate_growth_rate(income_statement, 'Selling General And Administration')
            rnd_growth = FinancialCalculator.calculate_growth_rate(income_statement, 'Research And Development')
            
            if revenue_growth == 0:
                revenue_growth = 0.05
            if cogs_growth == 0:
                cogs_growth = 0.05
            if sgna_growth == 0:
                sgna_growth = 0.03
            if rnd_growth == 0:
                rnd_growth = 0.05
        
        if cash_flow is None or cash_flow.empty:
            logger.warning("Cannot fetch cash flow for growth rates, using defaults")
            capex_growth = 0.03
            dep_growth = 0.02
        else:
            capex_growth = FinancialCalculator.calculate_growth_rate(cash_flow, 'Capital Expenditure')
            dep_growth = FinancialCalculator.calculate_growth_rate(cash_flow, 'Reconciled Depreciation')
            
            if capex_growth == 0:
                capex_growth = 0.03
            if dep_growth == 0:
                dep_growth = 0.02
        
        revenue_proj = FinancialCalculator.project_financials(self.financial_data.total_revenue, revenue_growth, 5)
        cogs_proj = FinancialCalculator.project_financials(self.financial_data.cogs, cogs_growth, 5)
        sgna_proj = FinancialCalculator.project_financials(self.financial_data.sgna, sgna_growth, 5)
        rnd_proj = FinancialCalculator.project_financials(self.financial_data.rnd, rnd_growth, 5)
        capex_proj = FinancialCalculator.project_financials(self.financial_data.cap_ex, capex_growth, 5)
        dep_proj = FinancialCalculator.project_financials(self.financial_data.depreciation_amortization, dep_growth, 5)
        
        current_wc = (self.financial_data.current_assets - self.financial_data.cash) - self.financial_data.current_liabilities
        wc_change_proj = [current_wc * 0.1] * 5
        
        for i in range(5):
            gross_profit = revenue_proj[i] - cogs_proj[i]
            operating_profit = gross_profit - (sgna_proj[i] + rnd_proj[i])
            after_tax_op_profit = operating_profit * (1 - self.market_data.tax_rate)
            fcff = after_tax_op_profit + dep_proj[i] - capex_proj[i] - wc_change_proj[i]
            self.results.fcff_projections.append(fcff)
        
        terminal_growth = self.market_data.terminal_growth_rate / 100.0
        if terminal_growth >= self.results.wacc:
            logger.warning(f"Terminal growth {terminal_growth:.2%} >= WACC {self.results.wacc:.2%}, adjusting")
            terminal_growth = self.results.wacc - 0.01
        
        self.results.terminal_value = (
            self.results.fcff_projections[-1] * (1 + terminal_growth) / 
            (self.results.wacc - terminal_growth)
        )
        
        logger.info(f"FCFF projections: {[f'{x/1e6:.2f}M' for x in self.results.fcff_projections]}")
        logger.info(f"Terminal value: ${self.results.terminal_value/1e9:.2f}B")
    
    def _calculate_valuation(self):
        """Calculate enterprise value and equity value."""
        pv_fcff = sum(
            self.results.fcff_projections[i] / ((1 + self.results.wacc) ** (i + 1))
            for i in range(5)
        )
        
        pv_terminal = self.results.terminal_value / ((1 + self.results.wacc) ** 5)
        
        self.results.enterprise_value = pv_fcff + pv_terminal
        
        net_debt = self.financial_data.total_debt - self.financial_data.cash
        self.results.equity_value = self.results.enterprise_value - net_debt
        
        shares = self.financial_data.shares_outstanding
        if shares <= 0:
            if self.financial_data.shares_issued > 0:
                net_shares = self.financial_data.shares_issued - self.financial_data.shares_repurchased
                if net_shares > 0:
                    shares = net_shares
        
        if shares <= 0:
            logger.warning("Invalid shares outstanding, fetching from market data")
            fetcher = DataFetcher(self.market_data.stock_ticker)
            fetcher.stock = yf.Ticker(self.market_data.stock_ticker)
            try:
                info = fetcher.stock.info
                shares = info.get('sharesOutstanding') or info.get('impliedSharesOutstanding') or 0
                if shares <= 0:
                    shares = 1000000
                    logger.warning(f"Using default shares: {shares}")
            except Exception as e:
                logger.error(f"Error fetching shares: {str(e)}, using default")
                shares = 1000000
        
        self.results.equity_value_per_share = self.results.equity_value / shares
        
        fetcher = DataFetcher(self.market_data.stock_ticker)
        fetcher.stock = yf.Ticker(self.market_data.stock_ticker)
        self.results.current_stock_price = fetcher.fetch_stock_price()
    
    def _determine_valuation_status(self):
        """Determine if stock is overvalued, fairly valued, or undervalued."""
        if self.results.current_stock_price == 0:
            self.results.valuation_status = "Unable to determine (no current price)"
            return
        
        diff = self.results.equity_value_per_share - self.results.current_stock_price
        self.results.margin_of_safety = (diff / self.results.current_stock_price) * 100
        
        if abs(diff) < self.results.current_stock_price * 0.05:
            self.results.valuation_status = "Fairly Valued"
        elif diff > 0:
            self.results.valuation_status = "Undervalued"
        else:
            self.results.valuation_status = "Overvalued"


class ReportGenerator:
    """Generate comprehensive DCF analysis reports."""
    
    @staticmethod
    def generate_text_report(financial_data: FinancialData, market_data: MarketData, results: DCFResults) -> str:
        """Generate text report."""
        report = []
        report.append("=" * 80)
        report.append("DCF VALUATION REPORT")
        report.append("=" * 80)
        report.append(f"Company: {market_data.stock_ticker}")
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("KEY METRICS")
        report.append("-" * 80)
        report.append(f"Current Stock Price: ${results.current_stock_price:.2f}")
        report.append(f"Intrinsic Value Per Share: ${results.equity_value_per_share:.2f}")
        report.append(f"Valuation Status: {results.valuation_status}")
        report.append(f"Margin of Safety: {results.margin_of_safety:.2f}%")
        report.append("")
        
        report.append("COST OF CAPITAL")
        report.append("-" * 80)
        report.append(f"WACC: {results.wacc:.4%}")
        report.append(f"Cost of Equity: {results.cost_of_equity:.4%}")
        report.append(f"Cost of Debt: {results.cost_of_debt:.4%}")
        report.append(f"Risk-Free Rate: {results.risk_free_rate:.4%}")
        report.append(f"Beta: {results.beta:.4f}")
        report.append(f"Company Rating: {results.company_rating}")
        report.append(f"Company Default Spread: {results.company_default_spread:.2f}%")
        report.append("")
        
        report.append("VALUATION SUMMARY")
        report.append("-" * 80)
        report.append(f"Enterprise Value: ${results.enterprise_value/1e9:.2f}B")
        report.append(f"Equity Value: ${results.equity_value/1e9:.2f}B")
        report.append(f"Net Debt: ${(financial_data.total_debt - financial_data.cash)/1e6:.2f}M")
        report.append("")
        
        report.append("FREE CASH FLOW PROJECTIONS (5 Years)")
        report.append("-" * 80)
        for i, fcff in enumerate(results.fcff_projections, 1):
            report.append(f"Year {i}: ${fcff/1e6:.2f}M")
        report.append(f"Terminal Value: ${results.terminal_value/1e9:.2f}B")
        report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    @staticmethod
    def generate_csv_report(financial_data: FinancialData, market_data: MarketData, 
                           results: DCFResults, filename: str = "dcf_report.csv"):
        """Generate CSV report."""
        data = {
            'Metric': [
                'Stock Ticker', 'Current Price', 'Intrinsic Value', 'Valuation Status',
                'Margin of Safety %', 'WACC', 'Cost of Equity', 'Cost of Debt',
                'Beta', 'Company Rating', 'Enterprise Value', 'Equity Value',
                'Equity Value Per Share', 'Terminal Value'
            ],
            'Value': [
                market_data.stock_ticker,
                f"${results.current_stock_price:.2f}",
                f"${results.equity_value_per_share:.2f}",
                results.valuation_status,
                f"{results.margin_of_safety:.2f}%",
                f"{results.wacc:.4%}",
                f"{results.cost_of_equity:.4%}",
                f"{results.cost_of_debt:.4%}",
                f"{results.beta:.4f}",
                results.company_rating,
                f"${results.enterprise_value/1e9:.2f}B",
                f"${results.equity_value/1e9:.2f}B",
                f"${results.equity_value_per_share:.2f}",
                f"${results.terminal_value/1e9:.2f}B"
            ]
        }
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        logger.info(f"CSV report saved to {filename}")


def load_config(config_file: str) -> Optional[Dict]:
    """Load configuration from JSON file."""
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
    return None


def get_user_input_interactive() -> Tuple[FinancialData, MarketData]:
    """Interactive input collection with validation."""
    print("\n" + "=" * 80)
    print("DCF CALCULATOR - DATA INPUT")
    print("=" * 80 + "\n")
    
    market_data = MarketData()
    financial_data = FinancialData()
    
    market_data.stock_ticker = input("Enter stock ticker (e.g., AAPL): ").strip().upper()
    market_data.market_index = input("Enter market index ticker (e.g., ^GSPC for S&P 500): ").strip().upper()
    market_data.country = input("Enter company's home country: ").strip()
    
    print("\nFetching financial data from Yahoo Finance...")
    fetcher = DataFetcher(market_data.stock_ticker)
    balance_sheet, income_statement, cash_flow = fetcher.fetch_data()
    
    if balance_sheet is not None and not balance_sheet.empty:
        financial_data = fetcher.extract_financial_data(balance_sheet, income_statement, cash_flow)
        print("Successfully fetched financial data!")
        print(f"Revenue: ${financial_data.total_revenue/1e6:.2f}M")
        print(f"EBIT: ${financial_data.ebit/1e6:.2f}M")
        print(f"Total Debt: ${financial_data.total_debt/1e6:.2f}M")
        print(f"Cash: ${financial_data.cash/1e6:.2f}M")
        
        use_manual = input("\nUse manual override for any values? (Y/N): ").strip().upper()
        if use_manual == 'Y':
            print("Enter new values (press Enter to keep fetched value):")
            revenue = input(f"Total Revenue (current: ${financial_data.total_revenue/1e6:.2f}M): ").strip()
            if revenue:
                financial_data.total_revenue = float(revenue) * 1e6
    else:
        print("Could not fetch data automatically. Please enter manually:")
        financial_data.total_revenue = float(input("Total Revenue: ")) * 1e6
        financial_data.cogs = float(input("COGS: ")) * 1e6
        financial_data.sgna = float(input("SG&A: ")) * 1e6
        financial_data.rnd = float(input("R&D: ")) * 1e6
        financial_data.depreciation_amortization = float(input("Depreciation & Amortization: ")) * 1e6
        financial_data.current_assets = float(input("Current Assets: ")) * 1e6
        financial_data.current_liabilities = float(input("Current Liabilities: ")) * 1e6
        financial_data.cash = float(input("Cash: ")) * 1e6
        financial_data.total_debt = float(input("Total Debt: ")) * 1e6
        financial_data.cap_ex = float(input("Capital Expenditure: ")) * 1e6
        financial_data.ebit = float(input("EBIT: ")) * 1e6
        financial_data.interest_expense = float(input("Interest Expense: ")) * 1e6
    
    market_data.tax_rate = float(input("\nTax Rate (%): ")) / 100.0
    market_data.market_value_debt = float(input("Market Value of Debt: ")) * 1e6
    market_data.market_value_equity = float(input("Market Value of Equity: ")) * 1e6
    market_data.domestic_revenue_pct = float(input("Domestic Revenue %: "))
    market_data.sector_domestic_revenue_pct = float(input("Sector Average Domestic Revenue %: "))
    market_data.equity_risk_premium_sp500 = float(input("S&P 500 Equity Risk Premium (%): "))
    market_data.bond_market_stddev = float(input("Bond Market Std Dev (%): ")) / 100.0
    market_data.longest_gov_bond_rate = float(input("Longest Gov Bond Rate (%): "))
    market_data.country_default_spread = float(input(f"Country Default Spread for {market_data.country} (%): "))
    market_data.terminal_growth_rate = float(input("Terminal Growth Rate (%): "))
    
    other_revenue = 100 - market_data.domestic_revenue_pct
    if other_revenue > 0:
        add_other = input(f"\nAdd other country revenue ({other_revenue}% remaining)? (Y/N): ").strip().upper()
        if add_other == 'Y':
            country_name = input("Other country name: ").strip()
            revenue_pct = float(input(f"Revenue % from {country_name}: "))
            default_spread = float(input(f"Default spread for {country_name} (%): "))
            market_data.other_countries.append({
                'name': country_name,
                'revenue_pct': revenue_pct,
                'default_spread': default_spread
            })
    
    return financial_data, market_data


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Production DCF Calculator for Investment Banking')
    parser.add_argument('--config', type=str, help='Path to JSON configuration file')
    parser.add_argument('--ticker', type=str, help='Stock ticker symbol')
    parser.add_argument('--output', type=str, default='dcf_report.csv', help='Output file path')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    
    args = parser.parse_args()
    
    try:
        if args.config:
            config = load_config(args.config)
            if config:
                logger.info("Using configuration file")
        else:
            config = None
        
        if args.interactive or not args.ticker:
            financial_data, market_data = get_user_input_interactive()
        else:
            logger.error("Non-interactive mode requires full configuration file")
            return
        
        calculator = DCFCalculator(financial_data, market_data)
        results = calculator.calculate()
        
        report_text = ReportGenerator.generate_text_report(financial_data, market_data, results)
        print("\n" + report_text)
        
        ReportGenerator.generate_csv_report(financial_data, market_data, results, args.output)
        
        logger.info("Analysis complete")
        
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
