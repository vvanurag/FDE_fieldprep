"""Domain tools for financial research, calculations, and external lookup."""

import json
from langchain_core.tools import tool
from .schemas import StockPriceQuery, CurrencyConversionQuery, SECFilingQuery, PortfolioCalculationQuery

# Simulated Mock Database
MOCK_STOCK_DB = {
    "AAPL": {"price": 224.50, "currency": "USD", "name": "Apple Inc.", "pe_ratio": 34.2},
    "MSFT": {"price": 428.10, "currency": "USD", "name": "Microsoft Corp.", "pe_ratio": 36.8},
    "NVDA": {"price": 121.80, "currency": "USD", "name": "NVIDIA Corp.", "pe_ratio": 45.1},
    "GOOGL": {"price": 165.30, "currency": "USD", "name": "Alphabet Inc.", "pe_ratio": 24.5},
    "AMZN": {"price": 186.40, "currency": "USD", "name": "Amazon.com Inc.", "pe_ratio": 41.0},
}

MOCK_FX_RATES = {
    ("USD", "EUR"): 0.92,
    ("USD", "GBP"): 0.77,
    ("USD", "JPY"): 152.40,
    ("EUR", "USD"): 1.087,
    ("GBP", "USD"): 1.298,
    ("JPY", "USD"): 0.00656,
}

MOCK_SEC_FILINGS = {
    ("AAPL", 2023): {"total_revenue": "$383.29 Billion", "net_income": "$96.99 Billion", "eps": "$6.13"},
    ("AAPL", 2022): {"total_revenue": "$394.33 Billion", "net_income": "$99.80 Billion", "eps": "$6.11"},
    ("MSFT", 2023): {"total_revenue": "$211.91 Billion", "net_income": "$72.36 Billion", "eps": "$9.68"},
    ("NVDA", 2024): {"total_revenue": "$60.92 Billion", "net_income": "$29.76 Billion", "eps": "$11.93"},
}


@tool("get_live_stock_price", args_schema=StockPriceQuery)
def get_live_stock_price(ticker: str) -> str:
    """Fetch the real-time stock price and market metrics for a given ticker symbol."""
    ticker_clean = ticker.strip().upper()
    if ticker_clean in MOCK_STOCK_DB:
        data = MOCK_STOCK_DB[ticker_clean]
        return json.dumps({
            "status": "success",
            "ticker": ticker_clean,
            "company_name": data["name"],
            "current_price_usd": data["price"],
            "pe_ratio": data["pe_ratio"]
        })
    return json.dumps({
        "status": "error",
        "message": f"Ticker '{ticker}' not found in active market listings. Available tickers: {list(MOCK_STOCK_DB.keys())}."
    })


@tool("convert_currency", args_schema=CurrencyConversionQuery)
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount from one fiat currency to another using live FX rates."""
    src = from_currency.strip().upper()
    dst = to_currency.strip().upper()
    
    if src == dst:
        return json.dumps({"converted_amount": round(amount, 2), "rate": 1.0, "to_currency": dst})
    
    pair = (src, dst)
    if pair in MOCK_FX_RATES:
        rate = MOCK_FX_RATES[pair]
        converted = round(amount * rate, 2)
        return json.dumps({
            "status": "success",
            "original_amount": amount,
            "from_currency": src,
            "converted_amount": converted,
            "to_currency": dst,
            "exchange_rate": rate
        })
    
    return json.dumps({
        "status": "error",
        "message": f"Direct exchange rate for {src}->{dst} unavailable. Try converting through USD."
    })


@tool("lookup_sec_annual_filing", args_schema=SECFilingQuery)
def lookup_sec_annual_filing(ticker: str, year: int) -> str:
    """Retrieve verified SEC Form 10-K financial metrics (Revenue, Net Income, EPS) for a company."""
    ticker_clean = ticker.strip().upper()
    key = (ticker_clean, int(year))
    
    if key in MOCK_SEC_FILINGS:
        filing = MOCK_SEC_FILINGS[key]
        return json.dumps({
            "status": "success",
            "ticker": ticker_clean,
            "fiscal_year": year,
            **filing
        })
    
    return json.dumps({
        "status": "error",
        "message": f"No SEC 10-K filing found for {ticker_clean} in fiscal year {year}."
    })


@tool("calculate_portfolio_value", args_schema=PortfolioCalculationQuery)
def calculate_portfolio_value(shares: float, price_per_share: float) -> str:
    """Perform exact multiplication to compute total portfolio position value."""
    total = round(shares * price_per_share, 2)
    return json.dumps({
        "status": "success",
        "shares": shares,
        "price_per_share": price_per_share,
        "total_value_usd": total
    })


# Export all registered tools
ALL_REACT_TOOLS = [
    get_live_stock_price,
    convert_currency,
    lookup_sec_annual_filing,
    calculate_portfolio_value
]
