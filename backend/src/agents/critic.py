from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage
from src.core.state import PortfolioState

def critic_node(state: PortfolioState) -> Dict[str, Any]:
    """Reviews the reoprt and provides feedback if it fails quality checks."""
    report = state.get("final_report","")

    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

    system_prompt = (
        "You are a strict Financial Compliance Reviewer. "
        "Review the provided markdown report. It MUST contain these exact sections: "
        "1. Executive Summary "
        "2. Data Table "
        "3. Risk Breakdowns "
        "4. Final Strategic Recommendation "
        "If it has all of these, respond EXACTLY with the word 'PASS'. "
        "If it is missing anything, provide a very short, specific sentence on what is missing, nothing else."
    )

    messages = [
        SystemMessage(content=system_prompt),
        AIMessage(content=f"Review this report: \n\n{report}")
    ]

    response = llm.invoke(messages)
    feedback = response.content.strip()

    if "PASS" in feedback.upper():
        return {
            "feedback": "PASS", 
            "messages": [AIMessage(content="✅ Report passed compliance review.", name="Critic")]
        }
    else:
        return {
            "feedback": feedback, 
            "messages": [AIMessage(content=f"❌ Feedback: {feedback}", name="Critic")]
        }