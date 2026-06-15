import os
from dotenv import load_dotenv
from src.core.graph import portfolio_app

load_dotenv()

def run_test():
    print("Starting the financial reasearch AI...\n")

    initial_state = {
        "task_requirements": "Analyze these stocks and provide a brief executive summary and risk assesment.",
        "tickers": ["AAPL", "MSFT"]
    }

    print("Executing Multi-Agent Workflow...\n")

    final_report = ""

    for output in portfolio_app.stream(initial_state):
        for node_name, state_update in output.items():
            print(f"{node_name.upper()} completed its task.")

            if node_name == "report_writer":
                final_report = state_update.get("final_report", "")

    print("\n=========================================")
    print("📊 FINAL SYNTHESIZED REPORT")
    print("=========================================\n")
    print(final_report)

if __name__ == "__main__":
    run_test()