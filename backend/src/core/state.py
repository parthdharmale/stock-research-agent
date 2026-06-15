from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph.message import add_messages
import operator

class PortfolioState(TypedDict):
    task_requirements: str
    tickers: List[str]

    #Where agents will store their findings
    market_data: Dict[str, Any]
    risk_metrics: Dict[str, Any]
    final_report: str

    feedback: str
    revision_count: Annotated[int, operator.add]

    #The running log of all agent interactions
    messages: Annotated[list, add_messages]