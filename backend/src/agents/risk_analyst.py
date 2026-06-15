import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage
from src.core.state import PortfolioState

def risk_analysis_node(state: PortfolioState) -> Dict[str, Any]:
    """Analyzes market data to determine risk metrics and updates the state."""
    market_data = state.get("market_data", {})

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    risk_metrics = {}

    for ticker, data in market_data.items():
        if "error" in data:
            risk_metrics[ticker] = {"risk_score": "Unknown", "reasoning": "Missing market data"}
            continue

        system_prompt = (
            "You are an expert Quantitative Risk Analyst. "
            "Analyze the provided financial metrics and assign a risk score from 1 (lowest) to 10 (highest). "
            "Apply the following strict rules: "
            "1. Forward P/E > 30 is high risk; < 15 is low risk; negative P/E is immediate high risk (7+). "
            "2. Market Cap < $2B adds +1 to the risk score due to volatility. "
            "3. Adjust baseline risk based on sector (e.g., Tech is riskier than Utilities). "
            "Return your assessment as a short paragraph explaining the reasoning, ending with 'Risk Score: X/10'."
        )

        messages = [
            SystemMessage(content=system_prompt),
            AIMessage(content=f"Market data for {ticker}: {json.dumps(data)}")
        ]

        response = llm.invoke(messages)

        risk_metrics[ticker] = {
            "analysis": response.content
        }

    summary_msg = f"Completed risk analysis for {len(risk_metrics)} active tickers."

    return {
        "risk_metrics": risk_metrics,
        "messages": [AIMessage(content=summary_msg, name="RiskAnalyst")]
    }