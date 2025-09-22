# stock_utils.py
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

def fetch_stock_data(query):
    if not YFINANCE_AVAILABLE:
        return f"yfinance not available. Cannot fetch stock data for {query}"
    
    # Handle sector queries by suggesting relevant stocks
    sector_keywords = {
        'IT': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA'],
        'pharma': ['JNJ', 'PFE', 'ABBV', 'MRK', 'TMO', 'DHR', 'ABT'],
        'finance': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP'],
        'tech': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA']
    }
    
    # Check if query contains sector keywords
    query_lower = query.lower()
    suggested_tickers = []
    
    for sector, tickers in sector_keywords.items():
        sector_lower = sector.lower()
        if sector_lower in query_lower or f"{sector_lower} " in query_lower or f" {sector_lower}" in query_lower:
            suggested_tickers = tickers[:3]  # Take top 3 stocks
            break
    
    if suggested_tickers:
        summary = f"Stock Data for {query} (Sector Analysis):\n"
        summary += f"Analyzing top stocks in this sector: {', '.join(suggested_tickers)}\n\n"
        
        for ticker in suggested_tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                summary += f"{ticker}:\n"
                summary += f"  - Current Price: ${info.get('currentPrice', 'N/A')}\n"
                summary += f"  - Market Cap: ${info.get('marketCap', 'N/A'):,}\n" if info.get('marketCap') else "  - Market Cap: N/A\n"
                summary += f"  - PE Ratio: {info.get('trailingPE', 'N/A')}\n"
                summary += f"  - 52W High/Low: ${info.get('fiftyTwoWeekHigh', 'N/A')} / ${info.get('fiftyTwoWeekLow', 'N/A')}\n\n"
            except Exception as e:
                summary += f"{ticker}: Error fetching data - {str(e)}\n\n"
        
        return summary
    else:
        # Try direct ticker lookup
        try:
            ticker = yf.Ticker(query)
            info = ticker.info
            if not info or len(info) < 5:  # Check if we got meaningful data
                return f"No stock data available for {query}. Please try a valid stock ticker (e.g., AAPL, MSFT) or sector query (e.g., 'IT sector', 'pharma stocks')."
            
            summary = f"Stock Info for {query}:\n"
            summary += f"- Current Price: ${info.get('currentPrice', 'N/A')}\n"
            summary += f"- Market Cap: ${info.get('marketCap', 'N/A'):,}\n" if info.get('marketCap') else "- Market Cap: N/A\n"
            summary += f"- PE Ratio: {info.get('trailingPE', 'N/A')}\n"
            summary += f"- Dividend Yield: {info.get('dividendYield', 'N/A')}\n"
            summary += f"- 52 Week High / Low: ${info.get('fiftyTwoWeekHigh', 'N/A')} / ${info.get('fiftyTwoWeekLow', 'N/A')}\n"
            return summary
        except Exception as e:
            return f"No stock data available for {query}. Please try a valid stock ticker (e.g., AAPL, MSFT) or sector query (e.g., 'IT sector', 'pharma stocks'). Error: {str(e)}"
