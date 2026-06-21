import json
from typing import Dict, Any, List
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
import yfinance as yf
from src.core.state import PortfolioState
from src.core.memory import memory_manager

@tool
def fetch_stock_financials(ticker: str) -> str:
    """Fetches core financial metrics and stock prices for a given ticker symbol."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        current_price = info.get("currentPrice")

        if current_price is None:
            return f"Error: Invalid ticker or no data found for symbol {ticker}."
        
        data = {
            "current_price": current_price,
            "forward_pe": info.get("forwardPE"),
            "market_cap": info.get("marketCap"),
            "sector": info.get("sector", "Unknown"),
            "recommendation": info.get("recommendationKey", "None")
        }
        return json.dumps(data)
    
    except Exception as e:
        return f"Error processing {ticker}: {str(e)}"
    
@tool
def search_ticker_news(ticker: str) -> str:
    """Searches the live web for recent news, press releases, or sentiment regarding a stock ticker."""
    search = DuckDuckGoSearchRun()
    return search.run(f"{ticker} stock financial news recent developments")

@tool
def search_internal_archives(query: str, ticker: str) -> str:
    """Searches our internal corporate vector database for past reports and historical context"""
    print(f"AGENT ACTION: Searching historical memory for {ticker}: '{query}'")
    return memory_manager.query_archives(query, ticker=ticker)

def data_gatherer_node(state: PortfolioState) -> Dict[str, Any]:
    """Autonomous agent node that chooses tools to look up market data and news"""
    tickers = state.get("tickers", [])
    task_requirements = state.get("task_requirements", "")

    print(f"AGENT: Data Gatherer is analyzing requirements for tickers: {tickers}")

    tools = [fetch_stock_financials, search_ticker_news, search_internal_archives]

    llm = ChatOpenAI(model="gpt-4o", temperature=0).bind_tools(tools)

    system_prompt = (
        "You are an expert financial research assistant. Your task is to collect data "
        "for the specified target tickers to fulfill the user request.\n"
        "1. You MUST look up the stock metrics using the 'fetch_stock_financials' tool.\n"
        "2. If the user explicitly asks for news, utilize the 'search_ticker_news' tool.\n"
        "3. If the user asks about 'past reports', 'history', or 'previous analysis', "
        "you MUST use the 'search_internal_archives' tool to fetch our internal history.\n"
        "Compile your final findings into a clear structured layout grouped by ticker."
    )

    user_message = f"User Request: {task_requirements}\nTarget Tickers: {tickers}"

    response = llm.invoke([
        ("system", system_prompt),
        ("user", user_message)
    ])

    market_data = {}

    if response.tool_calls:
        print(f"🛠️ AGENT ACTION: LLM selected tools to execute: {[t['name'] for t in response.tool_calls]}")

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            ticker_arg = tool_args.get("ticker")

            if not ticker_arg:
                continue

            if ticker_arg not in market_data:
                market_data[ticker_arg] = {}

            if tool_name == "fetch_stock_financials":
                result = fetch_stock_financials.invoke(tool_args)
                try:
                    market_data[ticker_arg].update(json.loads(result))
                except Exception:
                    market_data[ticker_arg]["error"] = result

            elif tool_name == "search_ticker_news":
                result = search_ticker_news.invoke(tool_args)
                market_data[ticker_arg]["recent_news"] = result

            elif tool_name == "search_internal_archives":
                result = search_internal_archives.invoke(tool_args)
                market_data[ticker_arg]["historical_context"] = result
    else:
        print("AGENT WARNING: LLM decided no tools were necessary.")
        market_data["raw_llm_response"] = response.content
    
    return {
        "market_data": market_data,
        "messages": [response]
    }