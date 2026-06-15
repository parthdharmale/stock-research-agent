import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage
from src.core.state import PortfolioState

def report_synthesis_node(state: PortfolioState) -> Dict[str, Any]:
    """Syntesizes market data and risk metrics into a final markdown report."""

    task_requirements = state.get("task_requirements", "")
    market_data = state.get("market_data", {})
    risk_metrics = state.get("risk_metrics", {})

    feedback = state.get("feedback", "")
    revision_count = state.get("revision_counnt", 0)

    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

    system_prompt = (
        "You are a Lead Financial Editor for an enterprise wealth management firm. "
        "Your job is to take raw market data and quantitative risk assessments and synthesize them "
        "into a highly professional, formatting-rich Markdown report. "
        "Structure the report with an Executive Summary, a Data Table of current metrics, "
        # "individual Risk Breakdowns, and a Final Strategic Recommendation."
    )

    if feedback and feedback != "PASS":
        system_prompt += f"\n\nURGENT FEEDBACK TO IMPLEMENT: {feedback}. YOU MUST FIX THIS."
        current_count = state.get("revision_count",0)
        print(f"WRITER: Drafting Revision {current_count + 1} based on feedback...")

    context = {
        "original_request": task_requirements,
        "market_data": market_data,
        "risk_analysis": risk_metrics
    }

    messages = [
        SystemMessage(content=system_prompt),
        AIMessage(content=f"Here is the context for the report: {json.dumps(context)}")
    ]

    

    response = llm.invoke(messages)

    summary_msg = "Final report succesfully synthesized."

    
    return{
        "final_report": response.content,
        "revision_count": 1,
        "messages": [AIMessage(content=f"Drafted report (Revision {current_count + 1}).", name="ReportWriter")]
    }