from langgraph.graph import StateGraph, START, END
from .state import PortfolioState

from src.agents.data_gatherer import data_gatherer_node
from src.agents.risk_analyst import risk_analysis_node
from src.agents.report_writer import report_synthesis_node
from src.agents.critic import critic_node

def route_after_gathering(state: PortfolioState) -> str:
    """
    Looks at the market_data. If all requested tickers failed, we skip the Risk Analyst
    and go straight to the Report Writer.
    """
    market_data = state.get("market_data", {})

    # Check if every single ticker in the dictionary has an "error" key.

    all_errors = True
    for ticker, data in market_data.items():
        if "error" not in data:
            all_errors = False
            break

    if not market_data or all_errors:
        print("Router: All data fetches failed. Skipping Risk Analsis")
        return "bypass_to_report"
    
    print("Router: Data found. Proceeding to Risk Analysis.")
    return "proceed_to_risk"

def route_after_critic(state: PortfolioState) -> str:
    """Decides if the report is done, or if it needs to loop back to the writer."""
    feedback = state.get("feedback", "")
    revision_count = state.get("revision_count", 0)

    if feedback == "PASS" or revision_count >= 2:
        print(f"CRITIC: Report accepted or maximum number of revisions reached : {revision_count}")
        return "accept"
    
    print(f"CRITIC: Report rejected. Sending back to writer. Feedback: {feedback}")
    return "revise"


def create_portfolio_graph():
    """Builds and compiles the multi-agent workflow"""
    workflow = StateGraph(PortfolioState)

    workflow.add_node("data_gatherer", data_gatherer_node)
    workflow.add_node("risk_analyst", risk_analysis_node,)
    workflow.add_node("report_writer", report_synthesis_node)
    workflow.add_node("critic", critic_node)

    workflow.add_edge(START, "data_gatherer")
    # workflow.add_edge("data_gatherer", "risk_analyst")
    workflow.add_conditional_edges(
        "data_gatherer",
        route_after_gathering,
        {
            "proceed_to_risk": "risk_analyst",
            "bypass_to_report": "report_writer"
        }
    )
    workflow.add_edge("risk_analyst", "report_writer")
    workflow.add_edge("report_writer", "critic")

    workflow.add_conditional_edges(
        "critic",
        route_after_critic,{
            "accept": END,
            "revise": "report_writer"
        }
    )

    app = workflow.compile()

    return app
    
portfolio_app = create_portfolio_graph()