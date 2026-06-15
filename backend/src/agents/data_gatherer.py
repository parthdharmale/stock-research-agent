import yfinance as yf
from typing import Dict, Any
from src.core.state import PortfolioState
from langchain_core.messages import AIMessage

def data_gathering_node(state: PortfolioState) -> Dict[str, Any]:
    """Fetches market data for the requested tickers and updates the state."""
    tickers = state.get("tickers", [])
    market_data = {}

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            current_price = info.get("currentPrice")
            if current_price is None:
                market_data[ticker] = {"error": f"Invalid ticker or no data found for {ticker}."}
                continue

            market_data[ticker] = {
                "current_price": info.get("currentPrice"),
                "forward_pe": info.get("forwardPE"),
                "market_cap": info.get("marketCap"),
                "sector": info.get("sector"),
                "recommendation": info.get("recommendationKey"),
            }
        except Exception as e:
            market_data[ticker] = {"error": f"Could not fetch data: {str(e)}"}

    summary_msg = f"Successfully gathered financial data for {len(tickers)} tickers."
    return {
        "market_data": market_data,
        "messages": [AIMessage(content=summary_msg, name="DataGatherer")]
    }